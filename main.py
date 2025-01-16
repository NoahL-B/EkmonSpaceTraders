import math
import random
import time
import threading
from datetime import datetime, timedelta, timezone

import economy
from SECRETS import TOKEN
from SHARED import *


import database.waypointGraphing as waypointGraphing
import database.dbFunctions as dbFunctions
from database.Waypoint import Waypoint, getWaypoint
from database.systemGraphing import *

SYSTEM = ""
ASTEROIDS = ""
GAS_GIANT = ""



def init_globals():
    global SYSTEM
    global ASTEROIDS
    global GAS_GIANT

    agent = api_functions.get_agent(TOKEN)
    hq = agent["data"]["headquarters"]
    hql = hq.split("-")
    SYSTEM = hql[0] + "-" + hql[1]

    waypoints_list = dbFunctions.get_all_waypoints_in_system(SYSTEM)
    for wp in waypoints_list:
        if wp['type'] == "ENGINEERED_ASTEROID":
            ASTEROIDS = wp['symbol']
        elif wp['type'] == "GAS_GIANT":
            GAS_GIANT = wp['symbol']


def get_all_contracts():
    return api_functions.get_all_contracts(TOKEN)


def get_active_contracts(all_contracts, accept_unaccepted=False, include_unaccepted=True):
    active_contracts = []
    for c in all_contracts:
        if not c["fulfilled"]:
            if c["accepted"]:
                active_contracts.append(c)
            elif accept_unaccepted:
                api_functions.accept_contract(TOKEN, c["id"])
                active_contracts.append(c)
            elif include_unaccepted:
                active_contracts.append(c)
    return active_contracts


def refine(ship, item_to_produce):
    return api_functions.ship_refine(TOKEN, ship, item_to_produce)


def extract(ship, survey=None):
    return api_functions.extract(TOKEN, ship, survey)


def siphon(ship):
    return api_functions.siphon_resources(TOKEN, ship)


def createSurvey(ship):
    return api_functions.create_survey(TOKEN, ship)


def dock(ship):
    return api_functions.dock_ship(TOKEN, ship)


def orbit(ship):
    return api_functions.orbit_ship(TOKEN, ship)


def cargo(ship):
    return api_functions.get_ship_cargo(TOKEN, ship)


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
            sale = api_functions.sell_cargo(TOKEN, ship, symbol, units)
            new_cargo = sale["data"]["cargo"]
            print(ship + ": " + str(sale))
    if new_cargo is None:
        new_cargo = cargo(ship)["data"]
    return new_cargo


def sell(ship, item, quantity):
    return api_functions.sell_cargo(TOKEN, ship, item, quantity)


def purchase(ship, item, units):
    return api_functions.purchase_cargo(TOKEN, ship, item, units)


def navigate(ship, location, nav_and_sleep=False):
    return api_functions.navigate(TOKEN, ship, location, nav_and_sleep)


def auto_nav(ship, destination, ship_stats=None):
    if ship_stats is None:
        ship_stats = get_ship(ship)

    system = ship_stats['data']['nav']['systemSymbol']
    origin = ship_stats['data']['nav']['waypointSymbol']
    status = ship_stats['data']['nav']['status']
    fuel = ship_stats['data']['fuel']['current']
    fuel_cap = ship_stats['data']['fuel']['capacity']

    if status == "DOCKED":
        orbit_response = orbit(ship)
        nav = orbit_response["data"]["nav"]
        ship_stats["data"]["nav"] = nav
        status = "IN_ORBIT"
    elif status == "IN_TRANSIT":
        ship_stats = sleep_until_arrival(ship, ship_data=ship_stats)
    if origin == destination:
        return ship_stats

    if ship_stats['data']['registration']['role'] == "SATELLITE":
        navigation = navigate(ship, destination, True)
        nav = navigation["data"]["nav"]
        fuel = navigation["data"]["fuel"]
        ship_stats["data"]["nav"] = nav
        ship_stats["data"]["fuel"] = fuel
        return ship_stats


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
        if origin_market and (fuel <= 5 or not destination_market and fuel < fuel_cap):
            dock(ship)
            refuel(ship)
            orbit(ship)
        navigation = navigate(ship, destination, True)
        nav = navigation["data"]["nav"]
        fuel = navigation["data"]["fuel"]
        ship_stats["data"]["nav"] = nav
        ship_stats["data"]["fuel"] = fuel
        return ship_stats

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
        api_functions.patch_ship_nav(TOKEN, ship, new_speed)

        ship_stats["data"]["nav"]["flightMode"] = new_speed
        ship_stats = auto_nav(ship, destination, ship_stats=ship_stats)
        print("Returning", ship, "to", start_speed, "speed")
        api_functions.patch_ship_nav(TOKEN, ship, start_speed)
        ship_stats["data"]["nav"]["flightMode"] = start_speed
        return ship_stats

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
            refuel_response = refuel(ship)
            ship_stats["data"]["fuel"] = refuel_response["data"]["fuel"]
            if "data" in refuel_response.keys():
                fueled_up = True
                fuel = refuel_response["data"]["fuel"]["current"]
            orbit(ship)

        if fueled_up:
            nav = navigate(ship, path.nodes[waypoint_num + 1], True)
            if "data" not in nav.keys():
                print(nav)
                raise Exception("UNKNOWN NAV ERROR:" + str(nav))
            fuel = nav['data']['fuel']['current']
            ship_stats["data"]["fuel"] = nav["data"]["fuel"]
            ship_stats["data"]["nav"] = nav["data"]["nav"]
        else:
            start_speed = ship_stats['data']['nav']['flightMode']
            if start_speed == "BURN":
                new_speed = "CRUISE"
            else:
                new_speed = "DRIFT"
            print("Slowing down", ship, "to", new_speed, "speed")
            api_functions.patch_ship_nav(TOKEN, ship, new_speed)
            ship_stats["data"]["nav"]["flightMode"] = new_speed
            ship_stats = auto_nav(ship, path.nodes[waypoint_num + 1], ship_stats=ship_stats)
            print("Returning", ship, "to", start_speed, "speed")
            api_functions.patch_ship_nav(TOKEN, ship, start_speed)
            ship_stats["data"]["nav"]["flightMode"] = start_speed
            if waypoint_num + 1 < len(path.edges):
                fuel = get_ship(ship)["data"]["fuel"]["current"]

        waypoint_num += 1
    return ship_stats


def get_jump_gate(system, waypoint):
    return api_functions.get_jump_gate(TOKEN, system, waypoint)


def jump(ship, waypoint, jump_and_sleep=False):
    to_return = api_functions.jump_ship(TOKEN, ship, waypoint)
    if jump_and_sleep:
        sleep_time = to_return["data"]["cooldown"]["totalSeconds"]
        time.sleep(sleep_time)
    return to_return


def warp(ship, waypoint, warp_and_sleep=False):
    to_return = api_functions.warp_ship(TOKEN, ship, waypoint)
    if warp_and_sleep:
        sleep_time = to_return["data"]["cooldown"]["totalSeconds"]
        time.sleep(sleep_time)
    return to_return



def auto_jump_warp(ship, destination_system):
    ship_stats = get_ship(ship)
    origin_system = ship_stats['data']['nav']['systemSymbol']
    status = ship_stats['data']['nav']['status']
    fuel = ship_stats['data']['fuel']['current']
    fuel_cap = ship_stats['data']['fuel']['capacity']
    can_warp = False

    modules = ship_stats['data']['modules']
    for m in modules:
        if "WARP" in m['symbol']:
            can_warp = True

    if status == "DOCKED":
        orbit(ship)
    elif status == "IN_TRANSIT":
        sleep_until_arrival(ship)
    if origin_system == destination_system:
        return

    local_jump_gate = None
    local_waypoints = dbFunctions.get_waypoints_from_access(origin_system)
    for wp in local_waypoints:
        if wp['type'] == "JUMP_GATE":
            local_jump_gate = wp['symbol']

    if local_jump_gate is None:
        if can_warp:
            api_functions.patch_ship_nav(TOKEN, ship, "DRIFT")
            waypoints = dbFunctions.get_waypoints_from_access(destination_system)
            destination_waypoint = random.choice(waypoints)['symbol']
            warp(ship, destination_waypoint, False)
            api_functions.patch_ship_nav(TOKEN, ship, "BURN")
            sleep_until_arrival(ship)
            return
        else:
            print("No jump gate is available, and", ship, "cannot warp!")

    auto_nav(ship, local_jump_gate)
    jump_graph = init_master_jump_graph()
    jump_path = dij_path(jump_graph, origin_system, destination_system)
    if jump_path is not None:

        jump_num = 0
        while jump_num < len(jump_path.edges):

            local_jump_gate, next_jump_gate = dbFunctions.jump_connection_exists(jump_path.nodes[jump_num], jump_path.nodes[jump_num + 1])
            jump_num += 1
            if jump_num < len(jump_path.edges):
                cooldown = api_functions.get_ship_cooldown(TOKEN, ship)
                time.sleep(api_functions.cooldown_to_time_delay(cooldown))
                jump(ship, next_jump_gate, True)
                get_jump_gate(api_functions.waypoint_name_to_system_name(next_jump_gate), next_jump_gate)
            else:
                jump(ship, next_jump_gate, False)
                get_jump_gate(api_functions.waypoint_name_to_system_name(next_jump_gate), next_jump_gate)

    else:
        if can_warp:
            jump_warp_graph = init_master_warp_graph()
            jump_warp_path = dij_path(jump_warp_graph, origin_system, destination_system)

            if jump_warp_path is None:
                api_functions.patch_ship_nav(TOKEN, ship, "DRIFT")
                waypoints = dbFunctions.get_waypoints_from_access(destination_system)
                destination_waypoint = random.choice(waypoints)['symbol']
                result = api_functions.warp_ship(TOKEN, ship, destination_waypoint)
                api_functions.patch_ship_nav(TOKEN, ship, "BURN")
                sleep_until_arrival(ship)
                return


            travel_num = 0

            while travel_num < len(jump_warp_path.edges):

                this_system = jump_warp_path.nodes[travel_num]
                next_system = jump_warp_path.nodes[travel_num + 1]


                jump_info = dbFunctions.jump_connection_exists(this_system, next_system)

                this_waypoint = None
                next_waypoint = None

                successfully_jumped = False

                # try to jump. Can fail if either side of the jump gate has not been built.
                # note that the path finding algorithm accounts for whether it will be able to successfully jump here, not whether it tries to jump here.
                if jump_info:
                    this_waypoint, next_waypoint = jump_info
                    auto_nav(ship, this_waypoint)
                    get_jump_gate(api_functions.waypoint_name_to_system_name(this_waypoint), this_waypoint)

                    cooldown = api_functions.get_ship_cooldown(TOKEN, ship)
                    time.sleep(api_functions.cooldown_to_time_delay(cooldown))

                    result = jump(ship, next_waypoint, False)
                    if "data" in result.keys():
                        successfully_jumped = True

                # warp if there was a missing jump gate, or if the jump failed to a jump gate still being built.
                if not successfully_jumped:
                    following_system = None
                    if travel_num < len(jump_warp_path.nodes) - 2:
                        following_system = jump_warp_path.nodes[travel_num + 2]
                    following_jump_info = None
                    if following_system is not None:
                        following_jump_info = dbFunctions.jump_connection_exists(next_system, following_system)

                    if following_jump_info:
                        next_waypoint = following_jump_info[0]

                    if next_waypoint is None:
                        waypoints = dbFunctions.get_waypoints_from_access(next_system)
                        next_waypoint = random.choice(waypoints)['symbol']

                    api_functions.patch_ship_nav(TOKEN, ship, "DRIFT")
                    warp(ship, next_waypoint, False)
                    api_functions.patch_ship_nav(TOKEN, ship, "BURN")
                    sleep_until_arrival(ship)



                travel_num += 1

        else:
            print("Too complicated a jump/warp to complete")





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
    return api_functions.deliver_cargo_to_contract(TOKEN, contract, ship, item, quantity)


def supply_construction(ship, system, waypoint, item, quantity):
    return api_functions.supply_construction_site(TOKEN, system, waypoint, ship, item, quantity)


def get_construction(system, waypoint):
    return api_functions.get_construction_site(TOKEN, system, waypoint)


def refuel(ship):
    return api_functions.refuel_ship(TOKEN, ship)


def nav_to_time_delay(nav):
    return api_functions.nav_to_time_delay(nav)


def get_ship(ship):
    return api_functions.get_ship(TOKEN, ship)


def sleep_until_arrival(ship, sleep_counter=False, ship_data=None):
    if ship_data is None:
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
    ship_data["data"]["nav"]["status"] = "IN_ORBIT"

    return ship_data


def chart_system(ship):
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
                    mark = api_functions.get_market(TOKEN, closest_wp["systemSymbol"], closest_wp["symbol"])
                    for good in mark["data"]["tradeGoods"]:
                        if good["symbol"] == "FUEL":
                            dock(ship)
                            refuel(ship)
                            orbit(ship)
                            api_functions.patch_ship_nav(TOKEN, ship, "BURN")
            current_wp = closest_wp
        waypoints.remove(closest_wp)
    return chart_count


def chart_wp(ship):
    return api_functions.create_chart(TOKEN, ship)



def minerLoop(ship, lock=None, surveys=None):
    orbit(ship)
    cooldown = api_functions.get_ship_cooldown(TOKEN, ship)
    time.sleep(api_functions.cooldown_to_time_delay(cooldown))
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
            extraction = extract(ship, survey)
            if "data" not in extraction.keys():
                print(ship + ": " + str(extraction))
            elif extraction['data']['extraction']['yield']['units'] >= 0:
                # print(ship + ": Extracted " + str(extraction['data']['extraction']['yield']['units']) + " " + extraction['data']['extraction']['yield']['symbol'])
                pass

            if "error" in extraction.keys() and extraction["error"]["code"] == 4221:
                # print("Survey expired and extraction failed")
                pass
            else:
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
                if "data" in extraction.keys():
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
    c = api_functions.get_contract(TOKEN, contract)
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


import hauling


def haulerLoopB(hauling_ship, mining_ships, lock, collection_waypoint, refining_ships=None):
    hauler = hauling_ship
    excavators = mining_ships
    hauling.sell_off_existing_cargo(hauler)

    refinable_ores = []
    if refining_ships:
        refinable_ores = ['IRON_ORE', "COPPER_ORE", "ALUMINUM_ORE", "SILVER_ORE", "GOLD_ORE", "PLATINUM_ORE", "URANITE_ORE", "MERITUM_ORE"]

    while True:
        try:

            ship = auto_nav(hauler, collection_waypoint)

            capacity = ship['data']['cargo']['capacity']
            inventory_size = ship['data']['cargo']['units']

            full = capacity == inventory_size

            lock.acquire()
            try:
                while not full:
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
                                        api_functions.transfer_cargo(TOKEN, e, hauler, i['symbol'], num_units)
                                        inventory_size += num_units


                    c = cargo(hauler)['data']
                    if c['units'] > 0:
                        pass  # print(hauler + ': ' + str(c))

                    full = c['units'] >= capacity * 0.9
                    if not full:
                        time.sleep(20)

            finally:
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
                                        api_functions.transfer_cargo(TOKEN, s, refining_ship, i['symbol'], num_units)
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
                                    t = api_functions.transfer_cargo(TOKEN, refining_ship, h, i['symbol'], num_to_transfer)
                                    print("Transfered refined goods back to haulers:", t)
                                    empty_space -= num_to_transfer
                finally:
                    hauling_lock.release()

            time.sleep(10)

        except TypeError as e:
            raise e
            #time.sleep(60)


def explorationRun(ship, destination_system, shipyard_waypoint):
    ship_stats = get_ship(ship)
    if ship_stats['data']['nav']['status'] == "DOCKED":
        orbit(ship)
        ship_stats["data"]["nav"]["status"] = "IN_ORBIT"
    elif ship_stats['data']['nav']['status'] == "IN_TRANSIT":
        ship_stats = sleep_until_arrival(ship, ship_data=ship_stats)

    if ship_stats['data']['nav']['systemSymbol'] != destination_system:
        auto_jump_warp(ship, destination_system)
        ship_stats = auto_nav(ship, shipyard_waypoint)
    elif ship_stats['data']['nav']['waypointSymbol'] != shipyard_waypoint:
        ship_stats = auto_nav(ship, shipyard_waypoint, ship_stats)

    ship_roles = dbFunctions.get_ship_roles_from_access()
    hauler_count = 0
    nurse_count = 0
    for s in ship_roles:
        if s['hasAssignment']  and s['systemSymbol'] == destination_system:
            if s['assignmentType'] == "TRADE_HAULER":
                hauler_count += 1
            elif s['assignmentType'] == "MARKET_NURSE":
                nurse_count += 1


    while hauler_count < 2 or nurse_count <= 1:
        assignment = "TRADE_HAULER"
        if hauler_count >= 2:
            assignment = "MARKET_NURSE"

        new_ship = api_functions.buyLightHauler(TOKEN, shipyard_waypoint)
        if type(new_ship) == str:
            new_ship_name = new_ship
            dbFunctions.access_add_ship_assignment(new_ship_name, True, assignment, destination_system)
            if assignment == "TRADE_HAULER":
                hauler_count += 1
            else:
                nurse_count += 1
        else:
            while api_functions.get_credits(TOKEN) < 1000000:
                scout_markets(ship)
                ship_stats = hauling.choose_trade_run_loop(destination_system, ship, [], False, ship_data=ship_stats)


    dbFunctions.access_update_ship_assignment(ship, assignmentType="MARKET_SCOUT")


def commandPhaseA(ship):
    # Initial funds to get 10 miner, 3 asteroid hauler, 3 surveyors, 2 siphons, 2 siphon haulers, 4 trade haulers
    ship_assignments = dbFunctions.get_ship_roles_from_access()
    ships_desired = {
        "MINING_SHIP": 1,
        "ASTEROID_HAULER": 1,
        "SURVEYOR": 1,
        "TRADE_HAULER": 1,
        "SIPHON_SHIP": 1,
        "GAS_GIANT_HAULER": 1,
        "MARKET_NURSE": 1
    }

    def start_ship(assignmentType):
        ship_type = ""
        if assignmentType == "MINING_SHIP":
            ship_type = "SHIP_MINING_DRONE"
        elif assignmentType in ["ASTEROID_HAULER", "TRADE_HAULER", "GAS_GIANT_HAULER", "MARKET_NURSE"]:
            ship_type = "SHIP_LIGHT_HAULER"
        elif assignmentType == "SURVEYOR":
            ship_type = "SHIP_SURVEYOR"
        elif assignmentType == "SIPHON_SHIP":
            ship_type = "SHIP_SIPHON_DRONE"
        shipyard = api_functions.findShipyard(SYSTEM, ship_type)

        auto_nav(ship, shipyard)
        dock(ship)

        if assignmentType == "MINING_SHIP":
            new_ship_name = api_functions.buyMiningDrone(TOKEN, shipyard)
            dbFunctions.access_add_ship_assignment(new_ship_name, True, assignmentType, SYSTEM, ASTEROIDS)
            x = threading.Thread(target=auto_nav, args=(new_ship_name, ASTEROIDS), daemon=True)
            x.start()
            print("THREAD REQUIRES PROGRAM RESTART TO FUNCTION")
        elif assignmentType == "ASTEROID_HAULER":
            new_ship_name = api_functions.buyLightHauler(TOKEN, shipyard)
            dbFunctions.access_add_ship_assignment(new_ship_name, True, assignmentType, SYSTEM, ASTEROIDS)
            x = threading.Thread(target=auto_nav, args=(new_ship_name, ASTEROIDS), daemon=True)
            x.start()
            print("THREAD REQUIRES PROGRAM RESTART TO FUNCTION")
        elif assignmentType == "SURVEYOR":
            new_ship_name = api_functions.buySurveyor(TOKEN, shipyard)
            dbFunctions.access_add_ship_assignment(new_ship_name, True, assignmentType, SYSTEM, ASTEROIDS)
            x = threading.Thread(target=auto_nav, args=(new_ship_name, ASTEROIDS), daemon=True)
            x.start()
            print("THREAD REQUIRES PROGRAM RESTART TO FUNCTION")
        elif assignmentType in ["TRADE_HAULER", "MARKET_NURSE"]:
            new_ship_name = api_functions.buyLightHauler(TOKEN, shipyard)
            dbFunctions.access_add_ship_assignment(new_ship_name, True, assignmentType, SYSTEM)

        elif assignmentType == "SIPHON_SHIP":
            new_ship_name = api_functions.buySiphonDrone(TOKEN, shipyard)
            dbFunctions.access_add_ship_assignment(new_ship_name, True, assignmentType, SYSTEM, GAS_GIANT)
            x = threading.Thread(target=auto_nav, args=(new_ship_name, GAS_GIANT), daemon=True)
            x.start()
            print("THREAD REQUIRES PROGRAM RESTART TO FUNCTION")
        elif assignmentType == "GAS_GIANT_HAULER":
            new_ship_name = api_functions.buyLightHauler(TOKEN, shipyard)
            dbFunctions.access_add_ship_assignment(new_ship_name, True, assignmentType, SYSTEM, GAS_GIANT)
            x = threading.Thread(target=auto_nav, args=(new_ship_name, GAS_GIANT), daemon=True)
            x.start()
            print("THREAD REQUIRES PROGRAM RESTART TO FUNCTION")

    for s in ship_assignments:
        if s['assignmentType'] in ships_desired.keys():
            ships_desired[s['assignmentType']] -= 1

    for assignment_type, num in ships_desired.items():
        while num > 0:
            while api_functions.get_agent(TOKEN)['data']['credits'] < 1000000:
                hauling.choose_trade_run_loop(SYSTEM, ship, ["FUEL", "ADVANCED_CIRCUITRY", "FAB_MATS"], False)

            start_ship(assignment_type)
            num -= 1

    ship_assignments = dbFunctions.get_ship_roles_from_access()
    ships_desired = {
        "ASTEROID_HAULER": 3,
        "MINING_SHIP": 10,
        "TRADE_HAULER": 4,
        "SIPHON_SHIP": 2,
        "GAS_GIANT_HAULER": 2,
        "SURVEYOR": 3
    }
    for s in ship_assignments:
        if s['assignmentType'] in ships_desired.keys():
            ships_desired[s['assignmentType']] -= 1

    for assignment_type, num in ships_desired.items():
        while num > 0:
            while api_functions.get_agent(TOKEN)['data']['credits'] < 700000:
                hauling.choose_trade_run_loop(SYSTEM, ship, ["ADVANCED_CIRCUITRY", "FAB_MATS"], False)

            start_ship(assignment_type)
            num -= 1

    dbFunctions.access_update_ship_assignment(ship, assignmentType="COMMAND_PHASE_B")


def find_construction(system):
    waypoints = dbFunctions.get_waypoints_from_access(system)
    for wp in waypoints:
        if wp['isUnderConstruction']:
            return wp['symbol']


def get_construction_materials(system):
    construction_site = find_construction(system)

    construction_dict = {}
    if construction_site is None:
        return construction_dict
    construction_stats = get_construction(system, construction_site)
    for material in construction_stats['data']['materials']:
        if material['required'] != material['fulfilled']:
            construction_dict[material['tradeSymbol']] = material['required'] - material['fulfilled']
    return construction_dict


def commandPhaseB(ship, system=None):
    if system is None:
        system = SYSTEM
    # Find and deliver FAB_MATS and ADVANCED_CIRCUITRY when supplies are high and cash is above 1.5 million

    construction_site = find_construction(system)

    construction_requirements = get_construction_materials(system)
    material_sum = sum(construction_requirements.values())

    while material_sum > 0:

        while api_functions.get_agent(TOKEN)['data']['credits'] < 1500000:
            hauling.choose_trade_run_loop(system, ship, construction_requirements.keys(), False)

        for material, num_to_deliver in construction_requirements.items():
            if num_to_deliver > 0:
                agent_credits = api_functions.get_agent(TOKEN)['data']['credits'] - 1000000
                max_cost = agent_credits/material_sum
                waypoints = dbFunctions.get_waypoints_from_access(system)
                waypoints = dbFunctions.find_all_with_trait_2(waypoints, "MARKETPLACE")
                marketplaces = dbFunctions.search_marketplaces_for_item(waypoints, material, imports=False, exchange=False)
                if len(marketplaces) == 0:
                    marketplaces = dbFunctions.search_marketplaces_for_item(waypoints, material)
                purchase_location = random.choice(marketplaces)['symbol']
                hauling.trade_cycle(ship, material, system, purchase_location, construction_site, "CONSTRUCTION", stop_on_unprofitable_origin=max_cost)
                hauling.trade_cycle(ship, material, system, purchase_location, construction_site, "CONSTRUCTION")

        start = datetime.now()
        while datetime.now() - start < timedelta(minutes=30):
            if api_functions.get_agent(TOKEN)['data']['credits'] < 2000000:
                hauling.choose_trade_run_loop(SYSTEM, ship, construction_requirements.keys(), False)
            else:
                products_to_promote = economy.get_all_predecessors(construction_requirements.keys())
                products_to_promote.reverse()
                num_promoted_products = 0
                for product in products_to_promote:
                    if hauling.stimulate_economy(system, ship, product):
                        num_promoted_products += 1
                print(ship, "stimulated the economy of", num_promoted_products, "trade goods")


        construction_requirements = get_construction_materials(system)
        material_sum = sum(construction_requirements.values())

    agent = api_functions.get_agent(TOKEN)
    faction_name = agent['data']['startingFaction']
    faction = api_functions.get_faction(TOKEN, faction_name)
    headquarters = faction['data']['headquarters']
    hq_system = api_functions.waypoint_name_to_system_name(headquarters)

    dbFunctions.access_update_ship_assignment(ship, assignmentType="COMMAND_PHASE_C", assignmentSystem=hq_system, assignmentWaypoint="")


def commandPhaseC(ship, system):

    auto_jump_warp(ship, system)
    ship_stats = scout_markets(ship, False)

    ship_assignments = dbFunctions.get_ship_roles_from_access()
    trade_haulers_desired = 3

    ship_prices = {}
    for ship_type in ["SHIP_REFINING_FREIGHTER", "SHIP_EXPLORER"]:
        shipyard = api_functions.findShipyard(system, ship_type)
        if shipyard is not None:
            ship_stats = auto_nav(ship, shipyard, ship_stats=ship_stats)
            shipyard_stats = api_functions.get_shipyard(TOKEN, system, shipyard)
            for s in shipyard_stats['data']['ships']:
                ship_prices[s['type']] = s['purchasePrice']

    if "SHIP_EXPLORER" not in ship_prices.keys():
        dbFunctions.access_update_ship_assignment(ship, True, "EXPLORER", system, api_functions.findShipyard(system, "SHIP_LIGHT_HAULER"))
        return

    for s in ship_assignments:
        if s['systemSymbol'] == system:
            if s['assignmentType'] == "TRADE_HAULER" or s['assignmentType'] == "MARKET_NURSE":
                trade_haulers_desired -= 1

    while trade_haulers_desired > 0:
        while api_functions.get_agent(TOKEN)['data']['credits'] < ship_prices['SHIP_REFINING_FREIGHTER'] * 2:
            ship_stats = hauling.choose_trade_run_loop(system, ship, [], False, ship_data=ship_stats)
            ship_stats = scout_markets(ship, False, ship_stats)
        shipyard = api_functions.findShipyard(system, "SHIP_REFINING_FREIGHTER")
        ship_stats = auto_nav(ship, shipyard, ship_stats)
        new_ship_name = api_functions.buyRefiningFreighter(TOKEN, shipyard)
        if trade_haulers_desired > 1:
            assignment = "TRADE_HAULER"
        else:
            assignment = "MARKET_NURSE"
        dbFunctions.access_add_ship_assignment(new_ship_name, True, assignment, system)
        trade_haulers_desired -= 1

    systems_with_assignments = []
    for s in ship_assignments:
        if s['hasAssignment']:
            if s['systemSymbol'] not in systems_with_assignments:
                systems_with_assignments.append(s['systemSymbol'])

    all_waypoints = dbFunctions.get_waypoints_from_access()
    this_faction = None
    all_factions = []
    incomplete_jump_gates = []

    for wp in all_waypoints:
        if 'faction' in wp.keys():
            if wp['systemSymbol'] == system:
                this_faction = wp['faction']
            if wp['faction'] not in all_factions:
                all_factions.append(wp['faction'])


    for wp in all_waypoints:
        if wp['isUnderConstruction']:
            if 'faction' in wp.keys():
                if wp['faction'] == this_faction:
                    if wp['systemSymbol'] not in systems_with_assignments:
                        incomplete_jump_gates.append(wp)

    for ijg in incomplete_jump_gates:
        while api_functions.get_agent(TOKEN)['data']['credits'] < ship_prices['SHIP_EXPLORER'] * 2:
            ship_stats = hauling.choose_trade_run_loop(system, ship, [], False, ship_data=ship_stats)
            ship_stats = scout_markets(ship, False, ship_stats)

        destination_system = ijg['systemSymbol']
        destination_shipyard = api_functions.findShipyard(destination_system, "SHIP_LIGHT_HAULER")
        if destination_shipyard is not None:

            shipyard = api_functions.findShipyard(system, "SHIP_EXPLORER")
            ship_stats = auto_nav(ship, shipyard, ship_stats)
            new_ship_name = api_functions.buyExplorer(TOKEN, shipyard)
            dbFunctions.access_add_ship_assignment(new_ship_name, True, "EXPLORER", destination_system, destination_shipyard)

    for faction in all_factions:
        faction_stats = api_functions.get_faction(TOKEN, faction)
        faction_hq = faction_stats['data']['headquarters']
        if faction_hq:
            faction_system = api_functions.waypoint_name_to_system_name(faction_hq)
            if faction_system not in systems_with_assignments:
                while api_functions.get_agent(TOKEN)['data']['credits'] < ship_prices['SHIP_EXPLORER'] * 2:
                    ship_stats = hauling.choose_trade_run_loop(system, ship, [], False, ship_data=ship_stats)
                    ship_stats = scout_markets(ship, False, ship_stats)
                shipyard = api_functions.findShipyard(system, "SHIP_EXPLORER")
                ship_stats = auto_nav(ship, shipyard, ship_stats)
                new_ship_name = api_functions.buyExplorer(TOKEN, shipyard)
                dbFunctions.access_add_ship_assignment(new_ship_name, True, "COMMAND_PHASE_C", faction_system)

    dbFunctions.access_update_ship_assignment(ship, assignmentType="MARKET_SCOUT")


def get_all_ships():
    return api_functions.get_all_ships(TOKEN)


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




def survey_loop(ship, lock: threading.Lock, surveys, max_num_surveys=100):
    orbit(ship)
    while True:
        if len(surveys) < max_num_surveys:
            new_survey = createSurvey(ship)
            if "data" in new_survey.keys():
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
            time.sleep(60)


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


def scout_markets(ship, need_to_chart=True, ship_stats=None):
    if need_to_chart:
        chart_system(ship)
        ship_stats = None

    if ship_stats is None:
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
        ship_stats = auto_nav(ship, closest_wp['symbol'])
        api_functions.get_market(TOKEN, sys, closest_wp['symbol'])
        current_wp = closest_wp
        markets.remove(closest_wp)

    print(ship, "finished scouting", num_to_scout, "market(s) in system", sys)
    return ship_stats


def market_scout_master(ship, system):
    def init_stationary_scout_dict():
        stationary_scout_dict = {}

        markets = dbFunctions.get_markets_from_access(system)

        for m in markets:
            stationary_scout_dict[m["symbol"]] = [None, m]

        ship_roles = dbFunctions.get_ship_roles_from_access()

        for ship_role in ship_roles:
            if ship_role['hasAssignment'] and ship_role['assignmentType'] == "STATIONARY_SCOUT" and ship_role["systemSymbol"] == system:
                stationary_scout_dict[ship_role["waypointSymbol"]][0] = ship_role["shipName"]
        return stationary_scout_dict

    def remote_check_in():

        stationary_scout_dict = init_stationary_scout_dict()

        shipyard = None

        for waypoint, value in stationary_scout_dict.items():
            ship_name, market = value
            if ship_name is None:
                if shipyard is None:
                    shipyard = api_functions.findShipyard(system, "SHIP_PROBE")
                    if shipyard is not None:
                        auto_nav(ship, shipyard)
                        dock(ship)
                if shipyard is not None:
                    ship_name = api_functions.buyProbe(TOKEN, shipyard)
                    if type(ship_name) == str:
                        stationary_scout_dict[waypoint] = ship_name
                        dbFunctions.access_add_ship_assignment(ship_name, True, "STATIONARY_SCOUT", system, waypoint)
                    else:
                        ship_name = None
                        break

            time_to_check_in = True
            if "timeStamp" in market["tradeGoods"][0].keys():
                market_time = market["tradeGoods"][0]["timeStamp"]
                market_time = market_time.replace(tzinfo=timezone.utc)
                current_time = datetime.now(timezone.utc)
                time_diff = current_time - market_time
                if time_diff < timedelta(minutes=30):
                    time_to_check_in = False

            if time_to_check_in:
                if ship_name is not None:
                    market = api_functions.get_market(TOKEN, system, waypoint, priority="HIGH")
                    if "data" in market.keys():
                        if "tradeGoods" not in market["data"].keys():
                            navigate(ship_name, waypoint)

    ship_stats = None

    while True:
        init_stationary_scout_dict()
        remote_check_in()

        ship_stats = scout_markets(ship, False, ship_stats)
        time.sleep(3600)


def market_nurse(ship, system):
    ship_stats = None
    while True:
        ship_stats = hauling.replenish_economy(system, ship, ship_stats, True)
        ship_stats = hauling.choose_trade_run_loop(system, ship, loop=False, ship_data=ship_stats)
        sleep_time = api_functions.queue_len() / 2.5
        time.sleep(sleep_time)


def main():

    threads = []

    mining_collection_lock = threading.Lock()
    siphon_collection_lock = threading.Lock()
    survey_lock = threading.Lock()
    surveys = []
    max_num_surveys = 20

    ship_roles = dbFunctions.get_ship_roles_from_access()

    mining_ships = {}
    siphon_ships = {}

    def make_thread(ship_role):
        t = None

        if ship_role['hasAssignment']:
            if ship_role['waypointSymbol'] not in mining_ships.keys():
                mining_ships[ship_role['waypointSymbol']] = []
                siphon_ships[ship_role['waypointSymbol']] = []
            if ship_role['assignmentType'] == "MINING_SHIP":
                mining_ships[ship_role['waypointSymbol']].append(ship_role['shipName'])
            elif ship_role['assignmentType'] == "SIPHON_SHIP":
                siphon_ships[ship_role['waypointSymbol']].append(ship_role['shipName'])


        if ship_role['hasAssignment']:

            if ship_role['assignmentType'] == "MINING_SHIP":
                t = threading.Thread(target=minerLoop, args=(ship_role['shipName'], survey_lock, surveys), daemon=True)
            elif ship_role['assignmentType'] == "SIPHON_SHIP":
                t = threading.Thread(target=siphonLoop, args=(ship_role['shipName'],), daemon=True)
            elif ship_role['assignmentType'] == "SURVEYOR":
                t = threading.Thread(target=survey_loop, args=(ship_role['shipName'], survey_lock, surveys, max_num_surveys), daemon=True)
            elif ship_role['assignmentType'] == "TRADE_HAULER":
                if ship_role["systemSymbol"] == SYSTEM:
                    construction_materials = get_construction_materials(SYSTEM).keys()
                else:
                    construction_materials = []
                t = threading.Thread(target=hauling.choose_trade_run_loop, args=(ship_role['systemSymbol'], ship_role['shipName'], construction_materials), daemon=True)
            elif ship_role['assignmentType'] == "ASTEROID_HAULER":
                if ship_role['waypointSymbol'] in mining_ships.keys():
                    t = threading.Thread(target=haulerLoopB, args=(ship_role['shipName'], mining_ships[ship_role['waypointSymbol']], mining_collection_lock, ship_role['waypointSymbol']), daemon=True)
                else:
                    print("ASTEROID REQUIRES PROGRAM RESTART TO FUNCTION")
            elif ship_role['assignmentType'] == "GAS_GIANT_HAULER":
                if ship_role['waypointSymbol'] in siphon_ships.keys():
                    t = threading.Thread(target=haulerLoopB, args=(ship_role['shipName'], siphon_ships[ship_role['waypointSymbol']], siphon_collection_lock, ship_role['waypointSymbol']), daemon=True)
                else:
                    print("GAS GIANT REQUIRES PROGRAM RESTART TO FUNCTION")
            elif ship_role['assignmentType'] == "MARKET_SCOUT":
                t = threading.Thread(target=market_scout_master, args=(ship_role['shipName'], ship_role["systemSymbol"]), daemon=True)
            elif ship_role['assignmentType'] == "EXPLORER":
                t = threading.Thread(target=explorationRun, args=(ship_role['shipName'], ship_role['systemSymbol'], ship_role['waypointSymbol']), daemon=True)
            elif ship_role['assignmentType'] == "COMMAND_PHASE_A":
                t = threading.Thread(target=commandPhaseA, args=(ship_role['shipName'],), daemon=True)
            elif ship_role['assignmentType'] == "COMMAND_PHASE_B":
                t = threading.Thread(target=commandPhaseB, args=(ship_role['shipName'], ship_role['systemSymbol']), daemon=True)
            elif ship_role['assignmentType'] == "COMMAND_PHASE_C":
                t = threading.Thread(target=commandPhaseC, args=(ship_role['shipName'], ship_role['systemSymbol']), daemon=True)
            elif ship_role['assignmentType'] == "MARKET_NURSE":
                t = threading.Thread(target=market_nurse, args=(ship_role['shipName'], ship_role['systemSymbol']), daemon=True)
            elif ship_role['assignmentType'] in ["", "STATIONARY_SCOUT"]:
                pass
            else:
                print("No assignment function for", ship_role['assignmentType'])

        if t is not None:
            t.name = ship_role["shipName"]
        return t

    considered_ships = []

    for ship_role in ship_roles:
        x = make_thread(ship_role)
        considered_ships.append(ship_role['shipName'])
        if x is not None:
            threads.append((x, ship_role['shipName']))
            x.start()
            time.sleep(0.15)  # prevents every thread from bombarding the database with queries simultaneously and crashing pyodbc


    if __name__ == '__main__':
        while len(threads) > 0:
            time.sleep(3600)
            ship_roles = dbFunctions.get_ship_roles_from_access()
            for ship_role in ship_roles:
                if ship_role['shipName'] not in considered_ships:
                    x = make_thread(ship_role)
                    considered_ships.append(ship_role['shipName'])
                    if x is not None:
                        threads.append((x, ship_role['shipName']))
                        x.start()

            role_map = {}
            for s in ship_roles:
                role_map[s['shipName']] = s
            i = 0
            while i < len(threads):
                if threads[i][0].is_alive():
                    i += 1
                else:
                    ship_role = role_map[threads[i][1]]
                    x = make_thread(ship_role)
                    if x is None:
                        threads.pop(i)
                    else:
                        x.start()
                        threads[i] = (x, ship_role['shipName'])
                        i += 1
    return threads



init_globals()

if __name__ == '__main__':
    try:
        from __SHARED import conn
        main()
    except KeyboardInterrupt as k:
        conn.close()
        raise k


