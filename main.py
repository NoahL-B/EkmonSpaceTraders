import math
import time
import threading
import json

import otherFunctions

from datetime import datetime, timedelta

from SECRETS import TOKEN
from SHARED import myClient


SYSTEM = ""
CONTRACT = ""
ITEM = []
ASTEROIDS = ""
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
    for wp in waypoints_list:
        if wp["type"] == "ASTEROID_FIELD":
            ASTEROIDS = wp["symbol"]
        elif wp["type"] == "ORBITAL_STATION":
            SHIPYARD = wp["symbol"]


def get_all_contracts():
    endpoint = "v2/my/contracts"
    params = {
        "limit": 20,
        "page": 1
    }
    page = myClient.generic_api_call("GET", endpoint, params, TOKEN)
    num_ships = page["meta"]["total"]
    all_contracts = page["data"]

    while num_ships > len(all_contracts):
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


def extract(ship, survey=None):
    endpoint = "v2/my/ships/" + ship + "/extract"
    params = None
    if survey is not None:
        params = {"survey": json.dumps(survey)}
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
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)


def purchase(ship, item, units):
    endpoint = "v2/my/ships/" + ship + "/purchase"
    params = {"symbol": item, "units": units}
    p = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    return p


def navigate(ship, location, nav_and_sleep=False):
    endpoint = "v2/my/ships/" + ship + "/navigate"
    params = {"waypointSymbol": location}
    to_return = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    if nav_and_sleep:
        time.sleep(nav_to_time_delay(to_return))
    return to_return


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


def chart_system(ship, system, limit_fuel=True):
    from database.System import listWaypointsInSystem
    waypoints = listWaypointsInSystem(system, limit=20)
    jump_gate = None
    chart_count = 0
    speed = ""
    if limit_fuel:
        speed = "BURN"
    for wp in waypoints["data"]:
        if wp["type"] == "JUMP_GATE":
            jump_gate = wp
        else:
            for t in wp["traits"]:
                if t["symbol"] == "UNCHARTED":
                    if limit_fuel:
                        if speed == "BURN":
                            s = get_ship(ship)
                            if s["data"]["fuel"]["current"] < 500:
                                otherFunctions.patchShipNav(ship, "DRIFT")
                                speed = "DRIFT"
                    navigate(ship, wp["symbol"], nav_and_sleep=True)
                    c = chart_wp(ship)
                    if c:
                        chart_count += 1
                        for t2 in c["data"]["waypoint"]["traits"]:
                            if t2["symbol"] == "MARKETPLACE":
                                mark = otherFunctions.getMarket(wp["systemSymbol"], wp["symbol"])
                                for good in mark["data"]["tradeGoods"]:
                                    if good["symbol"] == "FUEL":
                                        dock(ship)
                                        refuel(ship)
                                        orbit(ship)
                                        otherFunctions.patchShipNav(ship, "BURN")
                                        speed = "BURN"
    if jump_gate is not None:
        if limit_fuel:
            if speed == "BURN":
                s = get_ship(ship)
                if s["data"]["fuel"]["current"] < 500:
                    otherFunctions.patchShipNav(ship, "DRIFT")
        navigate(ship, jump_gate["symbol"], nav_and_sleep=True)
        for t in jump_gate["traits"]:
            if t["symbol"] == "UNCHARTED":
                chart_wp(ship)
                chart_count += 1
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
        print(ship, diff)
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


def ore_hound_thread_spawner(lock=None, surveys=None, max_hounds=30):
    #TODO: spawn survey ships up to 20% of the number of ore hounds
    import buyShip
    new_threads = []

    all_ships = get_all_ships()
    all_hounds = get_ships_by_frame(all_ships, "FRAME_MINER")
    num_hounds = len(all_hounds)

    while num_hounds < max_hounds:
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
                    print("NUM SURVEYS:", len(surveys))
                    lock.release()
                time.sleep(cooldown)
            else:
                time.sleep(60)
        else:
            time.sleep(150)


material_values = {
    "ALUMINUM_ORE": 20,
    "AMMONIA_ICE": 38,
    "COPPER_ORE": 2,
    "ICE_WATER": 11,
    "IRON_ORE": 2,
    "PRECIOUS_STONES": 2,
    "QUARTZ_SAND": 18,
    "SILICON_CRYSTALS": 33
}
avg = sum(material_values.values()) / len(material_values)
last_hundred_survey_values = [avg for _ in range(100)]


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
    market = otherFunctions.getMarket(SYSTEM, ASTEROIDS)
    try:
        trades = market["data"]["tradeGoods"]
    except KeyError:
        return False
    for t in trades:
        material_values[t["symbol"]] = t["sellPrice"]
    return True


def mat_val_updater(frequency=600):
    while True:
        update_material_values()
        print("Updated Mat Val:", material_values)
        time.sleep(frequency)


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

    survey_mounts = ["MOUNT_SURVEYOR_I",
                     "MOUNT_SURVEYOR_II",
                     "MOUNT_SURVEYOR_III"
                     ]
    mining_mounts = ["MOUNT_MINING_LASER_I",
                     "MOUNT_MINING_LASER_II",
                     "MOUNT_MINING_LASER_III"]

    mining_ships = ships_to_names(get_ships_by_mounts(all_ships, mining_mounts, survey_mounts))
    survey_ships = ships_to_names(get_ships_by_mounts(all_ships, survey_mounts, mining_mounts))

    threads = []
    survey_lock = threading.Lock()
    surveys = []

    max_num_surveys = min(100, 2*len(mining_ships))

    x = threading.Thread(target=mat_val_updater, daemon=True)
    threads.append(x)
    x.start()
    print("Material Value Updater Started!")
    time.sleep(1)

    for surveyor in survey_ships:
        x = threading.Thread(target=survey_loop, args=(surveyor, survey_lock, surveys, max_num_surveys), daemon=True)
        threads.append(x)
        x.start()
        print("surveyor started!", surveyor)

    if len(surveys) < 1 and len(survey_ships) > 0:
        print("Waiting", end="")
    while len(surveys) < 1 and len(survey_ships) > 0:
        print(".", end="")
        time.sleep(1)
    time.sleep(len(survey_ships) + 1)

    for drone in mining_ships:
        x = threading.Thread(target=shipLoop, args=(drone, survey_lock, surveys), daemon=True)
        threads.append(x)
        x.start()
        print("miner started!", drone)

    x = threading.Thread(target=ore_hound_thread_spawner, args=(survey_lock, surveys), daemon=True)
    threads.append(x)
    x.start()

    if __name__ == '__main__':
        while True:
            pass

    return threads


init_globals()

if __name__ == '__main__':
    main()
