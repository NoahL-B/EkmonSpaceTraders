import math
import random
import time
import threading
import json
from datetime import datetime, timedelta, timezone

import hauling
from SECRETS import TOKEN
from SHARED import myClient


import otherFunctions
import database.waypointGraphing as waypointGraphing
import database.dbFunctions as dbFunctions
from database.Waypoint import Waypoint, getWaypoint

SYSTEM = ""
CONTRACT = ""
ITEM = []
ASTEROIDS = "X1-DP28-DC5X"
SHIPYARD = ""
DELIVERY = ""


def init_globals():
    global SYSTEM
    global CONTRACT
    global ITEM
    global ASTEROIDS
    global SHIPYARD
    global DELIVERY

    agent = otherFunctions.getAgent()
    hq = agent["data"]["headquarters"]
    hql = hq.split("-")
    SYSTEM = hql[0] + "-" + hql[1]

    active_contracts = get_active_contracts(get_all_contracts(), False, False)
    if len(active_contracts) > 0:
        CONTRACT = active_contracts[0]["id"]
        ITEM.append(active_contracts[0]["terms"]["deliver"][0]["tradeSymbol"])
        DELIVERY = active_contracts[0]["terms"]["deliver"][0]["destinationSymbol"]
    else:
        CONTRACT = ""
        DELIVERY = ""
    waypoints_list = otherFunctions.getWaypoints(SYSTEM)["data"]


def get_all_contracts():
    endpoint = "v2/my/contracts"
    params = {
        "limit": 20,
        "page": 1
    }
    page = myClient.generic_api_call("GET", endpoint, params, TOKEN)
    num_contracts = page["meta"]["total"]
    all_contracts = page["data"]

    while num_contracts > len(all_contracts):
        params["page"] += 1
        page = myClient.generic_api_call("GET", endpoint, params, TOKEN)
        all_contracts.extend(page["data"])
    return all_contracts


def get_active_contracts(all_contracts, accept_unaccepted=False, include_unaccepted=True):
    active_contracts = []
    for c in all_contracts:
        if not c["fulfilled"]:
            if c["accepted"]:
                active_contracts.append(c)
            elif accept_unaccepted:
                otherFunctions.acceptContract(c["id"])
                active_contracts.append(c)
            elif include_unaccepted:
                active_contracts.append(c)
    return active_contracts


def refine(ship, item_to_produce):
    endpoint = "v2/my/ships/" + ship + "/refine"
    params = {"produce": item_to_produce}
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)

def extract(ship, survey=None):
    endpoint = "v2/my/ships/" + ship + "/extract"
    params = None
    if survey is not None:
        params = {"survey": json.dumps(survey)}
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)


def siphon(ship):
    endpoint = "v2/my/ships/" + ship + "/siphon"
    params = None
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)



def dumb_extract(ship, survey=None):
    endpoint = "v2/my/ships/" + ship + "/extract"
    params = None
    if survey is not None:
        params = {
            "survey.signature": survey["signature"],
            "survey.symbol": survey["symbol"],
            "survey.deposits": survey["deposits"],
            "survey.expiration": survey["expiration"],
            "survey.size": survey["size"],
            "survey": survey
        }
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)


def createSurvey(ship):
    endpoint = "v2/my/ships/" + ship + "/survey"
    return myClient.generic_api_call("POST", endpoint, None, TOKEN)


def dock(ship):
    endpoint = "v2/my/ships/" + ship + "/dock"
    return myClient.generic_api_call("POST", endpoint, None, TOKEN)


def orbit(ship):
    endpoint = "v2/my/ships/" + ship + "/orbit"
    return myClient.generic_api_call("POST", endpoint, None, TOKEN)


def cargo(ship):
    endpoint = "v2/my/ships/" + ship + "/cargo"
    return myClient.generic_api_call("GET", endpoint, None, TOKEN)


def sell_all(ship, saved=None):
    if saved is None:
        saved = list()
    data = cargo(ship)["data"]
    inv = data["inventory"]
    new_cargo = None
    for item in inv:
        symbol = item["symbol"]
        units = item["units"]

        if symbol not in saved:
            endpoint = "v2/my/ships/" + ship + "/sell"
            params = {"symbol": symbol, "units": units}
            sale = myClient.generic_api_call("POST", endpoint, params, TOKEN)
            new_cargo = sale["data"]["cargo"]
            print(ship + ": " + str(sale))
    if new_cargo is None:
        new_cargo = cargo(ship)["data"]
    return new_cargo


def sell(ship, item, quantity):
    endpoint = "v2/my/ships/" + ship + "/sell"
    params = {"symbol": item, "units": quantity}
    sale = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    if sale:
        waypoint = sale['data']['transaction']['waypointSymbol']
        system = waypoint
        while system[-1] != '-':
            system = system[:-1]
        system = system[:-1]
        dbFunctions.getMarket(system, waypoint)
    return sale


def purchase(ship, item, units):
    endpoint = "v2/my/ships/" + ship + "/purchase"
    params = {"symbol": item, "units": units}
    purchase = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    if purchase:
        waypoint = purchase['data']['transaction']['waypointSymbol']
        system = waypoint
        while system[-1] != '-':
            system = system[:-1]
        system = system[:-1]
        dbFunctions.getMarket(system, waypoint)
    return purchase


def navigate(ship, location, nav_and_sleep=False):
    endpoint = "v2/my/ships/" + ship + "/navigate"
    params = {"waypointSymbol": location}
    to_return = myClient.generic_api_call("POST", endpoint, params, TOKEN)

    if not to_return:
        ship_status = get_ship(ship)
        nav = ship_status['data']['nav']
        if nav['status'] == 'IN_TRANSIT':
            if nav['route']['destination']['symbol'] == location:
                if nav_and_sleep:
                    time.sleep(nav_to_time_delay(ship_status))
                return ship_status
            else:
                return to_return
        elif nav['status'] == 'DOCKED':
            orbit(ship)
            return navigate(ship, location, nav_and_sleep)
        elif nav['status'] == 'IN_ORBIT':
            if nav['route']['destination']['symbol'] == location:
                return ship_status
            else:
                return to_return

    if nav_and_sleep:
        time.sleep(nav_to_time_delay(to_return))
    return to_return


def auto_nav(ship, destination):
    ship_stats = get_ship(ship)
    system = ship_stats['data']['nav']['systemSymbol']
    origin = ship_stats['data']['nav']['waypointSymbol']
    status = ship_stats['data']['nav']['status']
    fuel = ship_stats['data']['fuel']['current']
    fuel_cap = ship_stats['data']['fuel']['capacity']

    if status == "DOCKED":
        orbit(ship)
    elif status == "IN_TRANSIT":
        sleep_until_arrival(ship)
    if origin == destination:
        return

    if ship_stats['data']['registration']['role'] == "SATELLITE":
        navigate(ship, destination, True)
        return


    all_waypoints = dbFunctions.get_waypoints_from_access(system)

    origin_in_access = False
    destination_in_access = False

    origin_wp = None
    destination_wp = None

    for wp in all_waypoints:
        if not origin_in_access:
            if wp['symbol'] == origin:
                origin_in_access = True
                origin_wp = wp
        if not destination_in_access:
            if wp['symbol'] == destination:
                destination_in_access = True
                destination_wp = wp

    if ship_stats['data']['nav']['flightMode'] == "DRIFT":
        origin_market = False
        destination_market = False
        for t in origin_wp['traits']:
            if t['symbol'] == "MARKETPLACE":
                origin_market = True
        for t in destination_wp['traits']:
            if t['symbol'] == "MARKETPLACE":
                destination_market = True
        if origin_market and not destination_market and fuel < fuel_cap:
            dock(ship)
            refuel(ship)
            orbit(ship)
        navigate(ship, destination, True)
        return

    if not origin_in_access or not destination_in_access:
        all_waypoints = dbFunctions.get_all_waypoints_in_system(system)


    burn = ship_stats['data']['nav']['flightMode'] == "BURN"

    dij_graph = waypointGraphing.make_dij_graph(all_waypoints, fuel_cap, burn)


    path = waypointGraphing.dij_path(dij_graph, origin, destination)

    if path is None:
        start_speed = ship_stats['data']['nav']['flightMode']
        if start_speed == "BURN":
            new_speed = "CRUISE"
        else:
            new_speed = "DRIFT"
        print("Slowing down", ship, "to", new_speed, "speed")
        otherFunctions.patchShipNav(ship, new_speed)
        auto_nav(ship, destination)
        print("Returning", ship, "to", start_speed, "speed")
        otherFunctions.patchShipNav(ship, start_speed)
        return

    waypoint_num = 0

    while waypoint_num < len(path.edges):

        fuel_required = path.edges[waypoint_num] % 10000
        fueled_up = True

        this_wp_market = False
        next_wp_market = False
        for wp in all_waypoints:
            if wp['symbol'] == path.nodes[waypoint_num]:
                for t in wp['traits']:
                    if t['symbol'] == "MARKETPLACE":
                        this_wp_market = True
            if wp['symbol'] == path.nodes[waypoint_num + 1]:
                for t in wp['traits']:
                    if t['symbol'] == "MARKETPLACE":
                        next_wp_market = True

        if not next_wp_market:
            fueled_up = False

        if fuel == fuel_cap:
            fueled_up = True

        if fuel_required > fuel:
            fueled_up = False

        if not fueled_up and this_wp_market:
            dock(ship)
            fueled_up = refuel(ship)
            orbit(ship)

        if fueled_up:
            nav = navigate(ship, path.nodes[waypoint_num + 1], True)
            fuel = nav['data']['fuel']['current']
        else:
            start_speed = ship_stats['data']['nav']['flightMode']
            if start_speed == "BURN":
                new_speed = "CRUISE"
            else:
                new_speed = "DRIFT"
            print("Slowing down", ship, "to", new_speed, "speed")
            otherFunctions.patchShipNav(ship, new_speed)
            auto_nav(ship, path.nodes[waypoint_num + 1])
            print("Returning", ship, "to", start_speed, "speed")
            otherFunctions.patchShipNav(ship, start_speed)

        waypoint_num += 1


def jump(ship, system, jump_and_sleep=False):
    endpoint = "v2/my/ships/" + ship + "/jump"
    params = {"systemSymbol": system}
    to_return = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    if jump_and_sleep:
        sleep_time = to_return["data"]["cooldown"]["totalSeconds"]
        time.sleep(sleep_time)
    return to_return


def warp(ship, waypoint, warp_and_sleep=False, sleep_counter=True):
    endpoint = "v2/my/ships/" + ship + "/warp"
    params = {"waypointSymbol": waypoint}
    to_return = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    if warp_and_sleep:
        sleep_time = int(nav_to_time_delay(to_return))
        if sleep_counter:
            print("Warping to", waypoint, "in", sleep_time, "seconds.")
            for i in range(sleep_time, 0, -1):
                time.sleep(1)
                print("          ", end="\r")
                print(i, end="\r")
        else:
            time.sleep(sleep_time)

    return to_return


def travel(ship, destination_waypoint, all_systems=None, sys_graph=None, limit_fuel=True, chart_while_traveling=False):
    #TODO: finish writing this function
    ship_obj = sleep_until_arrival(ship)
    fuel = ship_obj["data"]["fuel"]["current"]
    current_waypoint = ship_obj["data"]["nav"]["waypointSymbol"]
    current_system = ship_obj["data"]["nav"]["systemSymbol"]
    deconstructed_destination = destination_waypoint.split("-")
    destination_system = deconstructed_destination[0] + "-" + deconstructed_destination[1]

    if destination_system != current_system:
        pass
        #get graph, plot route
        # if first is jump not warp, navigate to jump gate
        # if any is warp, target a jump gate when applicable
        # after jump/warp, if chart_while_travelling, chart system
        # if waypoint is not the jump gate, navigate to jump gate

    else:
        if current_waypoint == destination_waypoint:
            return
        else:
            navigate(ship, destination_waypoint, True)
            return

    # note to future: need to tell route plotter to ignore empty systems
    return


def max_speed(fuel, x1, y1, x2, y2):
    distance = math.sqrt((x1-x2)**2 + (y1-y2)**2)

    if fuel >= 2 * distance:
        return "BURN"
    elif fuel >= distance:
        return "CRUISE"
    elif fuel >= 1:
        return "DRIFT"
    else:
        return None


def jumpNav(ship, jump_gate, systems, final_waypoint):
    orbit(ship)
    num_jumps = len(systems)
    navigate(ship, jump_gate, nav_and_sleep=True)
    for i in range(num_jumps):
        jump(ship, systems[i])
    return navigate(ship, final_waypoint, nav_and_sleep=True)


def deliver(ship, item, quantity, contract):
    endpoint = "v2/my/contracts/" + contract + "/deliver"
    params = {"shipSymbol": ship, "tradeSymbol": item, "units": quantity}
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)


def supply_construction(ship, system, waypoint, item, quantity):
    endpoint = "v2/systems/" + system + "/waypoints/" + waypoint + "/construction/supply"
    params = {"shipSymbol": ship, "tradeSymbol": item, "units": quantity}
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)


def get_construction(system, waypoint):
    endpoint = "v2/systems/" + system + "/waypoints/" + waypoint + "/construction"
    params = None
    return myClient.generic_api_call("GET", endpoint, params, TOKEN)

def refuel(ship):
    endpoint = "v2/my/ships/" + ship + "/refuel"
    return myClient.generic_api_call("POST", endpoint, None, TOKEN)


def nav_to_time_delay(nav):
    try:
        end = nav["data"]["nav"]["route"]["arrival"]
        start_dt = datetime.utcnow()
        end_dt = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S.%fZ')
        diff = end_dt - start_dt
        sec = diff.total_seconds()
        return sec
    except TypeError:
        return 60


def get_ship(ship):
    endpoint = "v2/my/ships/" + ship
    return myClient.generic_api_call("GET", endpoint, None, TOKEN)


def sleep_until_arrival(ship, sleep_counter=False):
    ship_data = get_ship(ship)
    nav_data = ship_data

    sleep_time = int(nav_to_time_delay(nav_data))
    if sleep_time <= 0:
        return ship_data
    if sleep_counter:
        print("Warping to", nav_data["data"]["nav"]["waypointSymbol"], "in", sleep_time, "seconds.")
        now = datetime.now()
        end = now + timedelta(seconds=sleep_time)
        while now < end:
            diff = end - now
            d = diff // timedelta(days=1)
            h = diff // timedelta(hours=1) % 24
            m = diff // timedelta(minutes=1) % 60
            s = diff // timedelta(seconds=1) % 60

            print("                   ", end="\r")
            print("{d:01d}:{h:02d}:{m:02d}:{s:02d}".format(d=d, h=h, m=m, s=s), end="\r")
            time.sleep(1)
            now = datetime.now()
    else:
        time.sleep(sleep_time)
    return ship_data


def chart_system(ship, system=None, limit_fuel=True):
    ship_stats = get_ship(ship)
    system = ship_stats['data']['nav']['systemSymbol']
    waypoints = dbFunctions.get_waypoints_from_access(system)
    chart_count = 0

    i = 0
    while i < len(waypoints):
        traits = waypoints[i]['traits']
        charted = True
        for t in traits:
            if t['symbol'] == "UNCHARTED":
                charted = False
        if charted:
            waypoints.pop(i)
        else:
            i += 1

    current_wp = {'symbol': ship_stats['data']['nav']['waypointSymbol'],
                  'x': ship_stats['data']['nav']['route']['destination']['x'],
                  'y': ship_stats['data']['nav']['route']['destination']['y']}
    while len(waypoints) > 0:
        closest_wp = waypoints[0]
        closest_distance = dbFunctions.distance(current_wp, closest_wp)
        for wp in waypoints:
            d = dbFunctions.distance(current_wp, wp)
            if d < closest_distance:
                closest_wp = wp
                closest_distance = d
        charted = True
        for t in closest_wp['traits']:
            if t['symbol'] == "UNCHARTED":
                charted = False
        if not charted:
            print("Closest uncharted waypoint to", ship, "is", closest_wp['symbol'], "at a distance of", closest_distance, "(with", len(waypoints), "waypoints left, inclusive)")
            auto_nav(ship, closest_wp['symbol'])
            c = chart_wp(ship)
            if c:
                chart_count += 1
                wp_obj = Waypoint(c['data']['waypoint'])
            else:
                wp_obj = getWaypoint(system, closest_wp['symbol'])
            dbFunctions.populate_waypoint(wp_obj)
            for t2 in wp_obj.traits:
                if t2["symbol"] == "MARKETPLACE":
                    mark = otherFunctions.getMarket(closest_wp["systemSymbol"], closest_wp["symbol"])
                    for good in mark["data"]["tradeGoods"]:
                        if good["symbol"] == "FUEL":
                            dock(ship)
                            refuel(ship)
                            orbit(ship)
                            otherFunctions.patchShipNav(ship, "BURN")
            current_wp = closest_wp
        waypoints.remove(closest_wp)
    return chart_count


def chart_wp(ship):
    endpoint = "v2/my/ships/" + ship + "/chart"
    return myClient.generic_api_call("POST", endpoint, None, TOKEN)


def shipLoop(ship, lock=None, surveys=None):
    global DELIVERY
    global ITEM
    orbit(ship)
    timeSinceLast = datetime.now()
    while True:
        new_time = datetime.now()
        diff = new_time - timeSinceLast
        # print(ship, diff)
        timeSinceLast = new_time
        try:
            fullCargo = False
            collected = None
            capacity = None
            extraction = None
            try:
                survey = None
                if lock is not None and surveys is not None:
                    while not lock.acquire():
                        time.sleep(1)
                    if len(surveys) > 0:
                        survey = surveys.pop(0)
                    lock.release()
                extraction = dumb_extract(ship, survey)
                print(ship + ": " + str(extraction))
                c = extraction["data"]["cargo"]
                capacity = c["capacity"]
                collected = c["units"]
            except TypeError:
                fullCargo = True
            if fullCargo or collected / capacity >= 0.67:
                dock(ship)
                c = sell_all(ship, ITEM)
                capacity = c["capacity"]
                collected = c["units"]
                print(ship + ": " + str(collected) + "/" + str(capacity))
                if collected / capacity >= 0.5:
                    print(ship + ": " + str(refuel(ship)))
                    orbit(ship)
                    nav = navigate(ship, DELIVERY)
                    print(ship + ": " + "En route to delivery")
                    time.sleep(nav_to_time_delay(nav) + 1)
                    dock(ship)
                    delivery = deliver(ship, ITEM[0], collected, CONTRACT)
                    if delivery["data"]["contract"]["terms"]["deliver"][0]["unitsRequired"] == \
                            delivery["data"]["contract"]["terms"]["deliver"][0]["unitsFulfilled"]:
                        ITEM.pop(0)
                        otherFunctions.fulfillContract(CONTRACT)
                    print(ship + ": " + str(delivery))
                    print(ship + ": " + str(refuel(ship)))
                    orbit(ship)
                    nav = navigate(ship, ASTEROIDS)
                    print(ship + ": " + "En route to asteroids")
                    time.sleep(nav_to_time_delay(nav) + 1)
                    print(ship + ": " + "Returned to asteroids")
                else:
                    orbit(ship)
                    cooldown = extraction["data"]["cooldown"]["remainingSeconds"]
                    time.sleep(cooldown)
            else:
                cooldown = extraction["data"]["cooldown"]["remainingSeconds"]
                time.sleep(cooldown)
        except TypeError:
            print(ship + ": ****************************ERROR************************")
            orbit(ship)
            time.sleep(60)


def minerLoop(ship, lock=None, surveys=None):
    orbit(ship)
    timeSinceLast = datetime.now()
    while True:
        new_time = datetime.now()
        diff = new_time - timeSinceLast
        # print(ship, diff)
        timeSinceLast = new_time
        try:
            survey = None
            if lock is not None and surveys is not None:
                while not lock.acquire():
                    time.sleep(1)
                if len(surveys) > 0:
                    survey = surveys.pop(0)
                lock.release()
            extraction = dumb_extract(ship, survey)
            if not extraction:
                print(ship + ": " + str(extraction))
            elif extraction['data']['extraction']['yield']['units'] >= 0:
                # print(ship + ": Extracted " + str(extraction['data']['extraction']['yield']['units']) + " " + extraction['data']['extraction']['yield']['symbol'])
                pass

            cooldown = extraction["data"]["cooldown"]["remainingSeconds"]
            time.sleep(cooldown)
        except TypeError as e:
            print(ship + ": ****************************ERROR************************")
            print(e)
            orbit(ship)
            time.sleep(70)


def siphonLoop(ship):
    orbit(ship)
    timeSinceLast = datetime.now()
    ship_stats = get_ship(ship)
    capacity = ship_stats['data']['cargo']['capacity']
    inventory = ship_stats['data']['cargo']['units']
    while True:
        if capacity == inventory:
            time.sleep(20)
            ship_stats = get_ship(ship)
            inventory = ship_stats['data']['cargo']['units']
        elif capacity < inventory:
            ship_stats = get_ship(ship)
            inventory = ship_stats['data']['cargo']['units']
        else:
            new_time = datetime.now()
            diff = new_time - timeSinceLast
            # print(ship, diff)
            timeSinceLast = new_time
            try:
                extraction = siphon(ship)
                cooldown = 60
                if extraction:
                    cooldown = extraction["data"]["cooldown"]["remainingSeconds"]
                    num_units = extraction['data']['siphon']['yield']['units']
                    if num_units >= 0:
                        # print(ship + ": Siphoned " + str(extraction['data']['siphon']['yield']['units']) + " " + extraction['data']['siphon']['yield']['symbol'])
                        inventory += num_units
                else:
                    print(ship + ": " + str(extraction))

                time.sleep(cooldown)
            except TypeError as e:
                print(ship + ": ****************************ERROR************************")
                print(e)
                orbit(ship)
                time.sleep(70)
def haulerLoop(ship, contract, origin, use_jump_nav=False, jump_nav_gates_to_origin=None,
               jump_nav_systems_to_origin=None, jump_nav_gates_to_destination=None,
               jump_nav_systems_to_destination=None, item=None, destination=None, required=None, fulfilled=None,
               max_price=None):
    c = otherFunctions.getContract(contract)
    if required is None:
        required = c["data"]["terms"]["deliver"][0]["unitsRequired"]
        print("required", required)
    if fulfilled is None:
        fulfilled = c["data"]["terms"]["deliver"][0]["unitsFulfilled"]
        print("fulfilled", fulfilled)
    if destination is None:
        destination = c["data"]["terms"]["deliver"][0]["destinationSymbol"]
        print("destination", destination)
    if item is None:
        item = c["data"]["terms"]["deliver"][0]["tradeSymbol"]
        print("item", item)
    if max_price is None:
        start_credits = c["data"]["terms"]["payment"]["onAccepted"]
        end_credits = c["data"]["terms"]["payment"]["onFulfilled"]
        total = start_credits + end_credits
        max_price = total / required
        print("max price per unit", max_price)

    too_expensive = False
    while required > fulfilled and not too_expensive:
        orbit(ship)
        if use_jump_nav:
            jumpNav(ship, jump_nav_gates_to_origin, jump_nav_systems_to_origin, origin)
        else:
            nav = navigate(ship, origin)
            print(nav)
            time.sleep(nav_to_time_delay(nav) + 1)
        dock(ship)
        to_purchase = required - fulfilled
        if to_purchase > 120:
            purchase(ship, item, 60)
            p = purchase(ship, item, 60)
            numPurchased = 120
        elif 60 < to_purchase:
            purchase(ship, item, 60)
            p = purchase(ship, item, to_purchase - 60)
            numPurchased = to_purchase
        else:
            purchase(ship, item, to_purchase)
            p = numPurchased = to_purchase
        orbit(ship)
        if use_jump_nav:
            jumpNav(ship, jump_nav_gates_to_destination, jump_nav_systems_to_destination, destination)
        else:
            nav = navigate(ship, destination)
            print(nav)
            time.sleep(nav_to_time_delay(nav) + 1)

        dock(ship)
        d = deliver(ship, item, numPurchased, contract)
        fulfilled += numPurchased
        print(d["data"]["contract"]["terms"]["deliver"])
        fulfilled = d["data"]["contract"]["terms"]["deliver"][0]["unitsFulfilled"]
        refuel(ship)
        if p is not None:
            if p["data"]["transaction"]["pricePerUnit"] >= max_price:
                too_expensive = True

    return not too_expensive


def haulerLoopB(hauling_ship, mining_ships, lock, collection_waypoint, refining_ships=None):
    hauler = hauling_ship
    excavators = mining_ships
    hauling.sell_off_existing_cargo(hauler)

    refinable_ores = []
    if refining_ships:
        refinable_ores = ['IRON_ORE', "COPPER_ORE", "ALUMINUM_ORE", "SILVER_ORE", "GOLD_ORE", "PLATINUM_ORE", "URANITE_ORE", "MERITUM_ORE"]

    while True:
        try:

            auto_nav(hauler, collection_waypoint)

            ship = get_ship(hauler)
            capacity = ship['data']['cargo']['capacity']
            inventory_size = ship['data']['cargo']['units']

            full = capacity == inventory_size

            while not full:
                try:
                    lock.acquire()
                    for e in excavators:
                        if capacity > inventory_size:
                            result = cargo(e)
                            inventory = result['data']['inventory']

                            for i in inventory:
                                if i['symbol'] not in refinable_ores:
                                    num_units = i['units']
                                    if num_units > capacity - inventory_size:
                                        num_units = capacity - inventory_size
                                    if num_units > 0:
                                        otherFunctions.transfer(e, hauler, i['symbol'], num_units)
                                        inventory_size += num_units
                finally:
                    lock.release()

                time.sleep(30)


                c = cargo(hauler)['data']
                if c['units'] > 0:
                    pass  # print(hauler + ': ' + str(c))

                full = c['units'] >= capacity * 0.9

            lock.acquire()
            lock.release()
            hauling.sell_off_existing_cargo(hauler)

        except TypeError:
            time.sleep(60)


def refinerLoop(refining_ship, extraction_ships, hauling_ships, hauling_lock):

    asteroid = "X1-DP28-DC5X"

    basic_to_processed_goods = {
        "IRON_ORE": "IRON",
        "COPPER_ORE": "COPPER",
        "ALUMINUM_ORE": "ALUMINUM",
        "SILVER_ORE": "SILVER",
        "GOLD_ORE": "GOLD",
        "PLATINUM_ORE": "PLATINUM",
        "URANITE_ORE": "URANITE",
        "MERITUM_ORE": "MERITUM"
    }

    while True:
        try:
            auto_nav(refining_ship, asteroid)

            ship = get_ship(refining_ship)
            capacity = ship['data']['cargo']['capacity']
            inventory_size = ship['data']['cargo']['units']

            try:
                hauling_lock.acquire()

                for s in hauling_ships + extraction_ships:
                    if capacity > inventory_size:

                        result = get_ship(s)
                        waypoint = result['data']['nav']['waypointSymbol']
                        nav_status = result['data']['nav']['status']
                        if waypoint == asteroid and nav_status == "IN_ORBIT":
                            inventory = result['data']['cargo']['inventory']

                            for i in inventory:
                                if i['symbol'] in basic_to_processed_goods.keys():
                                    num_units = i['units']
                                    if num_units > capacity - inventory_size:
                                        num_units = capacity - inventory_size
                                    if num_units > 0:
                                        otherFunctions.transfer(s, refining_ship, i['symbol'], num_units)
                                        inventory_size += num_units
            finally:
                hauling_lock.release()

            ship = get_ship(refining_ship)
            processed_goods = []
            if ship['data']['cooldown']['remainingSeconds'] == 0:
                cooldown = False
                for i in ship['data']['cargo']['inventory']:
                    symbol = i['symbol']
                    if symbol in basic_to_processed_goods.keys():
                        if not cooldown and i['units'] > 100:
                            r = refine(refining_ship, basic_to_processed_goods[symbol])
                            if r:
                                refined_item = r['data']['produced'][0]
                                print(refining_ship, "refined something:", r['data'])
                                print(refining_ship, "now has cargo:", r['data']['cargo'])
                                processed_goods.append(refined_item)
                                cooldown = True
                    else:
                        processed_goods.append(i)

            if processed_goods:
                try:
                    hauling_lock.acquire()

                    for h in hauling_ships:
                        if processed_goods:
                            result = get_ship(h)
                            waypoint = result['data']['nav']['waypointSymbol']
                            nav_status = result['data']['nav']['status']
                            if waypoint == asteroid and nav_status == "IN_ORBIT":
                                empty_space = result['data']['cargo']['capacity'] - result['data']['cargo']['units']
                                while processed_goods and empty_space > 0:
                                    i = processed_goods.pop()
                                    num_to_transfer = min(empty_space, i['units'])
                                    t = otherFunctions.transfer(refining_ship, h, i['symbol'], num_to_transfer)
                                    print("Transfered refined goods back to haulers:", t)
                                    empty_space -= num_to_transfer
                finally:
                    hauling_lock.release()

            time.sleep(10)

        except TypeError as e:
            raise e
            #time.sleep(60)


def get_all_ships():
    endpoint = "v2/my/ships/"
    params = {
        "limit": 20,
        "page": 1
    }
    page = myClient.generic_api_call("GET", endpoint, params, TOKEN)
    num_ships = page["meta"]["total"]
    all_ships = page["data"]

    while num_ships > len(all_ships):
        params["page"] += 1
        page = myClient.generic_api_call("GET", endpoint, params, TOKEN)
        all_ships.extend(page["data"])
    return all_ships


def get_ships_by_role(all_ships, role):
    role_ships = []
    for ship in all_ships:
        if ship["registration"]["role"] == role:
            role_ships.append(ship)
    return role_ships


def get_ships_by_frame(all_ships, frame):
    frame_ships = []
    for ship in all_ships:
        if ship["frame"]["symbol"] == frame:
            frame_ships.append(ship)
    return frame_ships


def get_ships_by_mounts(all_ships, desired_mounts_list=None, disallowed_mounts_list=None):
    if desired_mounts_list is None:
        desired_mounts_list = []
    if disallowed_mounts_list is None:
        disallowed_mounts_list = []

    equipped_ships = []

    for ship in all_ships:
        equipment_list = ship["mounts"]
        if len(desired_mounts_list) == 0:
            equipped = True
        else:
            equipped = False
        for mount in equipment_list:
            if mount["symbol"] in desired_mounts_list:
                equipped = True
        for mount in equipment_list:
            if mount["symbol"] in disallowed_mounts_list:
                equipped = False

        if equipped:
            equipped_ships.append(ship)
    return equipped_ships


def ships_to_names(ships):
    names = []
    for ship in ships:
        names.append(ship["symbol"])
    return names


def ore_hound_thread_spawner(lock=None, surveys=None, max_hounds=30, max_surveys=100):
    #TODO: spawn survey ships up to 20% of the number of ore hounds
    import buyShip
    new_threads = []

    all_ships = get_all_ships()

    survey_mounts = ["MOUNT_SURVEYOR_I",
                     "MOUNT_SURVEYOR_II",
                     "MOUNT_SURVEYOR_III"
                     ]
    mining_mounts = ["MOUNT_MINING_LASER_I",
                     "MOUNT_MINING_LASER_II",
                     "MOUNT_MINING_LASER_III"]

    mining_ships = ships_to_names(get_ships_by_mounts(all_ships, mining_mounts, survey_mounts))
    survey_ships = ships_to_names(get_ships_by_mounts(all_ships, survey_mounts, mining_mounts))

    num_hounds = len(mining_ships)
    num_surveyors = len(survey_ships)

    surveyors_per_miner = 0.2
    max_surveyors = max_hounds * surveyors_per_miner

    while num_hounds < max_hounds or num_surveyors < max_surveyors:
        agent = otherFunctions.getAgent()
        credits = agent["data"]["credits"]
        shipyard = buyShip.getShipyard()
        ships = shipyard["data"]["ships"]
        ore_hound = None
        for ship in ships:
            if ship["type"] == "SHIP_ORE_HOUND":
                ore_hound = ship
        ore_hound_price = ore_hound["purchasePrice"]
        market = otherFunctions.getMarket(SYSTEM, SHIPYARD)
        goods = market["data"]["tradeGoods"]
        mount_price = None
        for good in goods:
            if good["symbol"] == "MOUNT_MINING_LASER_II":
                mount_price = good["purchasePrice"] * 2

        total_price = ore_hound_price + mount_price + 8000
        print("***")
        print("CREDITS:", credits)
        print("COST:", total_price)
        print("***")
        if credits > total_price:
            if num_surveyors < num_hounds * surveyors_per_miner:
                new_ship = buyShip.buySurveyHound()
                new_thread = threading.Thread(target=survey_loop, args=(new_ship, lock, surveys, max_surveys), daemon=True)
                new_threads.append(new_thread)
                new_thread.start()
                num_surveyors += 1
            else:
                new_ship = buyShip.buyOreHound()
                new_thread = threading.Thread(target=shipLoop, args=(new_ship, lock, surveys), daemon=True)
                new_threads.append(new_thread)
                new_thread.start()
                print("New Ship:", new_ship)
                num_hounds += 1

        time.sleep(600)


def survey_loop(ship, lock: threading.Lock, surveys, max_num_surveys=100):
    orbit(ship)
    while True:
        if len(surveys) < max_num_surveys:
            new_survey = createSurvey(ship)
            if new_survey is not False:
                cooldown = new_survey["data"]["cooldown"]["totalSeconds"]
                survey_list = new_survey["data"]["surveys"]
                good_surveys = []
                for survey in survey_list:
                    if is_good(survey):
                        good_surveys.append(survey)
                if good_surveys:
                    gsc = []
                    for s in good_surveys:
                        if s["size"] == "SMALL":
                            for _ in range(5):
                                gsc.append(s)
                        elif s["size"] == "MODERATE":
                            for _ in range(10):
                                gsc.append(s)
                        elif s["size"] == "LARGE":
                            for _ in range(20):
                                gsc.append(s)
                    while not lock.acquire():
                        time.sleep(1)
                    surveys.extend(gsc)
                    update_material_values()
                    # print("NUM SURVEYS:", len(surveys))
                    lock.release()
                time.sleep(cooldown)
            else:
                time.sleep(60)
        else:
            time.sleep(150)


material_values = {
    "ALUMINUM_ORE": 0,
    "AMMONIA_ICE": 0,
    "COPPER_ORE": 0,
    "ICE_WATER": 0,
    "IRON_ORE": 0,
    "PRECIOUS_STONES": 0,
    "QUARTZ_SAND": 0,
    "SILICON_CRYSTALS": 0
}
last_hundred_survey_values = [0 for _ in range(100)]


def is_good(survey):
    global last_hundred_survey_values
    value = survey_value(survey)
    last_hundred_survey_values.append(value)
    if len(last_hundred_survey_values) < 100:
        return True
    else:
        last_hundred_survey_values.pop(0)
    top_30 = last_hundred_survey_values.copy()
    top_30.sort(reverse=True)
    threshold = top_30[30]
    if value > threshold:
        return True
    else:
        return False


def survey_value(survey):
    deposits = survey["deposits"]
    divisor = len(deposits)
    value = 0
    for d in deposits:
        d_type = d["symbol"]
        value += material_values[d_type] / divisor

    return value


def update_material_values():
    global material_values
    for material in material_values.keys():
        material_values[material] = 0
    all_markets = dbFunctions.get_markets_from_access()
    local_markets = []
    for m in all_markets:
        if SYSTEM in m['symbol']:
            local_markets.append(m)
    for market in local_markets:
        for good in market['tradeGoods']:
            if good['symbol'] not in material_values.keys():
                material_values[good['symbol']] = good['sellPrice']
            elif material_values[good['symbol']] < good['sellPrice']:
                material_values[good['symbol']] = good['sellPrice']
    return True


update_material_values()


def jettison(ship):
    data = cargo(ship)["data"]
    inv = data["inventory"]
    new_cargo = None
    for item in inv:
        symbol = item["symbol"]
        units = item["units"]
        endpoint = "v2/my/ships/" + ship + "/jettison"
        params = {"symbol": symbol, "units": units}
        jet = myClient.generic_api_call("POST", endpoint, params, TOKEN)
        new_cargo = jet["data"]["cargo"]
    return new_cargo


def trade_loop(ship, purchase_waypoint, sell_waypoint, item, trade_volume, margin=1.1):
    ship_data = sleep_until_arrival(ship)
    if len(ship_data["data"]["cargo"]["inventory"]) > 0:
        if ship_data["data"]["nav"]["status"] != "DOCKED":
            dock(ship)
        try:
            sell_all(ship)
        except KeyError:
            jettison(ship)
        orbit(ship)
    elif ship_data["data"]["nav"]["status"] == "DOCKED":
        orbit(ship)
    if ship_data["data"]["nav"]["waypointSymbol"] != purchase_waypoint:
        navigate(ship, purchase_waypoint, True)
    dock(ship)

    capacity = ship_data["data"]["cargo"]["capacity"]
    profitable = True
    p = None
    while profitable:
        num_purchased = 0
        while num_purchased < capacity:
            next_purchase_volume = min(trade_volume, capacity - num_purchased)
            p = purchase(ship, item, next_purchase_volume)
            num_purchased += next_purchase_volume
        investment = p["data"]["transaction"]["pricePerUnit"] * capacity
        orbit(ship)
        navigate(ship, sell_waypoint, True)
        dock(ship)
        s = sell(ship, item, capacity)
        refuel(ship)
        gross = s["data"]["transaction"]["pricePerUnit"]
        orbit(ship)
        navigate(ship, purchase_waypoint, True)
        dock(ship)
        if investment * margin < gross:
            profitable = False


def main():
    all_ships = get_all_ships()
    to_remove = []
    for s in all_ships:
        if s['symbol'] in ["EKMON-1", "EKMON-41"]:
            to_remove.append(s)
    for s in to_remove:
        all_ships.remove(s)

    survey_mounts = ["MOUNT_SURVEYOR_I",
                     "MOUNT_SURVEYOR_II",
                     "MOUNT_SURVEYOR_III"
                     ]
    mining_mounts = ["MOUNT_MINING_LASER_I",
                     "MOUNT_MINING_LASER_II",
                     "MOUNT_MINING_LASER_III"]

    siphon_mounts = ["MOUNT_GAS_SIPHON_I",
                     "MOUNT_GAS_SIPHON_II",
                     "MOUNT_GAS_SIPHON_III"]

    mining_ships = ships_to_names(get_ships_by_mounts(all_ships, mining_mounts))
    survey_ships = ships_to_names(get_ships_by_mounts(all_ships, survey_mounts))
    siphon_ships = ships_to_names(get_ships_by_mounts(all_ships, siphon_mounts))
    explorers = ships_to_names(get_ships_by_frame(all_ships, "FRAME_EXPLORER"))

    i = 0
    while i < len(mining_ships):
        if mining_ships[i] in siphon_ships:
            siphon_ships.remove(mining_ships[i])
        if mining_ships[i] in survey_ships:
            if len(mining_ships) > 2.5 * len(survey_ships):
                mining_ships.pop(i)
            else:
                survey_ships.remove(mining_ships[i])
                i += 1
        else:
            i += 1

    for e in explorers:
        if e in siphon_ships:
            siphon_ships.remove(e)

    threads = []
    survey_lock = threading.Lock()
    surveys = []

    max_num_surveys = min(100, 2*len(mining_ships))

    mining_collection_lock = threading.Lock()
    siphon_collection_lock = threading.Lock()

    asteroid_haulers = ["EKMON-A", "EKMON-11", "EKMON-12", "EKMON-13"]
    gas_giant_haulers = ["EKMON-3C", "EKMON-3D"]
    trade_haulers = ["EKMON-24", "EKMON-25", "EKMON-34", "EKMON-35", "EKMON-36", "EKMON-37", "EKMON-47", "EKMON-48", "EKMON-49", "EKMON-4A", "EKMON-4B", "EKMON-4C", "EKMON-4D", "EKMON-4E", "EKMON-4F", "EKMON-50", "EKMON-51", "EKMON-52", "EKMON-55", "EKMON-56", "EKMON-57", "EKMON-58"]
    refineries = []

    for hauler in asteroid_haulers:
        x = threading.Thread(target=haulerLoopB, args=(hauler, mining_ships, mining_collection_lock, ASTEROIDS), daemon=True)
        threads.append(x)
        x.start()

    for refinery in refineries:
        x = threading.Thread(target=refinerLoop, args=(refinery, mining_ships, asteroid_haulers, mining_collection_lock), daemon=True)
        threads.append(x)
        x.start()

    for hauler in gas_giant_haulers:
        x = threading.Thread(target=haulerLoopB, args=(hauler, siphon_ships, siphon_collection_lock, "X1-DP28-C38"), daemon=True)
        threads.append(x)
        x.start()


    for hauler in trade_haulers:
        system = None
        for s in all_ships:
            if s['symbol'] == hauler:
                system = s['nav']['systemSymbol']
        x = threading.Thread(target=hauling.choose_trade_run_loop, args=(system, hauler, []), daemon=True)
        threads.append(x)
        x.start()

    for surveyor in survey_ships:
        x = threading.Thread(target=survey_loop, args=(surveyor, survey_lock, surveys, max_num_surveys), daemon=True)
        threads.append(x)
        x.start()
        # print("surveyor started!", surveyor)


    for drone in mining_ships:
        x = threading.Thread(target=minerLoop, args=(drone, survey_lock, surveys), daemon=True)
        threads.append(x)
        x.start()
        # print("miner started!", drone)

    for drone in siphon_ships:
        x = threading.Thread(target=siphonLoop, args=(drone,), daemon=True)
        threads.append(x)
        x.start()

    if __name__ == '__main__':
        while True:
            main3()
            time.sleep(1000)
    return threads


def main2():
    import hauling
    for hauler in ["EKMON-12", "EKMON-13", "EKMON-25"]:
        ship_stats = get_ship(hauler)
        sys = ship_stats['data']['nav']['systemSymbol']
        x = threading.Thread(target=hauling.choose_trade_run_loop, args=(sys, hauler, []), daemon=True)
        x.start()
        time.sleep(5)

    if __name__ == '__main__':
        while True:
            time.sleep(100)

def scout_markets(ship, need_to_chart = True):
    if need_to_chart:
        chart_system(ship)

    ship_stats = get_ship(ship)
    sys = ship_stats['data']['nav']['systemSymbol']
    local_waypoints = dbFunctions.get_waypoints_from_access(sys)
    markets = dbFunctions.find_all_with_trait_2(local_waypoints, "MARKETPLACE")

    index = 0
    while index < len(markets):
        market_wp = markets[index]
        current_time = datetime.now(timezone.utc)
        marketplace = dbFunctions.access_get_market(market_wp['symbol'])
        if len(marketplace) == 0:
            markets.pop(index)
        elif marketplace[0]['timeStamp'] is None:
            index += 1
        else:
            market_time = marketplace[0]['timeStamp']
            market_time = market_time.replace(tzinfo=timezone.utc)
            time_diff = current_time-market_time
            if time_diff > timedelta(hours=4):
                index += 1
            else:
                markets.pop(index)


    current_wp = {'symbol': ship_stats['data']['nav']['waypointSymbol'],
                  'x': ship_stats['data']['nav']['route']['destination']['x'],
                  'y': ship_stats['data']['nav']['route']['destination']['y']}
    num_to_scout = len(markets)
    print(ship, "has", num_to_scout, "market(s) to scout in system", sys)
    while len(markets) > 0:
        closest_wp = markets[0]
        closest_distance = dbFunctions.distance(current_wp, closest_wp)
        for m in markets:
            d = dbFunctions.distance(current_wp, m)
            if d < closest_distance:
                closest_wp = m
                closest_distance = d
        print("Closest market to", ship, "is", closest_wp['symbol'], "at a distance of", closest_distance, "(with", len(markets), "markets left, inclusive)")
        auto_nav(ship, closest_wp['symbol'])
        otherFunctions.getMarket(sys, closest_wp['symbol'])
        current_wp = closest_wp
        markets.remove(closest_wp)

    print(ship, "finished scouting", num_to_scout, "market(s) in system", sys)



def main3():
    scouts = ["EKMON-2F", "EKMON-2", "EKMON-38", "EKMON-3E", "EKMON-3F", "EKMON-40", "EKMON-42", "EKMON-43", "EKMON-44", "EKMON-45", "EKMON-46"]
    threads = []
    for scout in scouts:
        x = threading.Thread(target=scout_markets, args=(scout, True), daemon=True)
        x.start()
        threads.append(x)
    if __name__ == '__main__':
        for x in threads:
            x.join()


init_globals()

if __name__ == '__main__':

    import faulthandler
    faulthandler.enable()

    main()


