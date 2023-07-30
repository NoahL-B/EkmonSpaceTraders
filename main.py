from SpacePyTraders import client
import time
import threading
from datetime import datetime
import otherFunctions
import buyShip

USERNAME = "EKMON"
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGlmaWVyIjoiRUtNT04iLCJ2ZXJzaW9uIjoidjIiLCJyZXNldF9kYXRlIjoiMjAyMy0wNy0yOSIsImlhdCI6MTY5MDY0NzM2MSwic3ViIjoiYWdlbnQtdG9rZW4ifQ.W4RYEuGm5xCqo92Efc0QQIEmnudAE1tHv_cLBMZ4R7TIToBQsqR-cPbOcWmvwDFI8WvG3cjQ91JrEK2h-BMj2H7tzfNlZ7Ah88_SrhAjLGbnRnabtQCZGq4R8j2uG4XDiSRlVaotL_Ng-tzkkha4ul-pRLceIQ-NWF1y2yQTf_6E21UsWLrT61LMkvQaj1RH6oJZApaJxx2KxTR2dlkSBvH2UZ0RL59IBPLcpw9hgtWWmdSlw8ZRFMR9GdYeOEfhYYtaXeZWdNXDsC81IScHqBId9B_9QpztmHKqiXepZwTREgELb2Saeqts02WsgN13D9G-GMAVP1iAN-eWmNftdw"

myClient = client.Client(USERNAME, TOKEN)

MINING_SHIPS = [            #"EKMON-1"    #,              "EKMON-3",
                 "EKMON-4",  "EKMON-5",  "EKMON-6",  "EKMON-7",  "EKMON-8",  "EKMON-9" #,  "EKMON-A",  "EKMON-B",  "EKMON-C",  "EKMON-D",  "EKMON-E",  "EKMON-F",
#                "EKMON-10", "EKMON-11", "EKMON-12", "EKMON-13", "EKMON-14", "EKMON-15", "EKMON-16", "EKMON-17", "EKMON-18", "EKMON-19", "EKMON-1A", "EKMON-1B", "EKMON-1C", "EKMON-1D", "EKMON-1E", "EKMON-1F",
#                "EKMON-20", "EKMON-21", "EKMON-22", "EKMON-23", "EKMON-24", "EKMON-25", "EKMON-26", "EKMON-27", 'EKMON-28', 'EKMON-29', 'EKMON-2A', 'EKMON-2B', 'EKMON-2C', 'EKMON-2D', 'EKMON-2E', 'EKMON-2F',
#                'EKMON-30', 'EKMON-31', 'EKMON-32', "EKMON-33", "EKMON-34", "EKMON-35", "EKMON-36", "EKMON-37", 'EKMON-38', 'EKMON-39', 'EKMON-3A', 'EKMON-3B', 'EKMON-3C', 'EKMON-3D', 'EKMON-3E', 'EKMON-3F',
#                            "EKMON-41",                                                                                                                         "EKMON-4C", "EKMON-4D", "EKMON-4E",
#                            'EKMON-51', 'EKMON-52', "EKMON-53", "EKMON-54", "EKMON-55", "EKMON-56", "EKMON-57", 'EKMON-58', 'EKMON-59', 'EKMON-5A', 'EKMON-5B', 'EKMON-5C', 'EKMON-5D', 'EKMON-5E', 'EKMON-5F',
#                'EKMON-60', 'EKMON-61', 'EKMON-62', "EKMON-63", "EKMON-64", "EKMON-65", "EKMON-66", "EKMON-67", 'EKMON-68', 'EKMON-69', 'EKMON-6A', 'EKMON-6B', 'EKMON-6C', 'EKMON-6D', 'EKMON-6E', 'EKMON-6F',
#                'EKMON-70', 'EKMON-71', 'EKMON-72', "EKMON-73", "EKMON-74", "EKMON-75", "EKMON-76", "EKMON-77", 'EKMON-78', 'EKMON-79', 'EKMON-7A', 'EKMON-7B', 'EKMON-7C', 'EKMON-7D', 'EKMON-7E', 'EKMON-7F',
#                'EKMON-80', 'EKMON-81', 'EKMON-82', "EKMON-83", "EKMON-84", "EKMON-85", "EKMON-86", "EKMON-87", 'EKMON-88', 'EKMON-89', 'EKMON-8A', 'EKMON-8B', 'EKMON-8C', 'EKMON-8D', 'EKMON-8E', 'EKMON-8F',
#                'EKMON-90', 'EKMON-91', 'EKMON-92', "EKMON-93"
                            ]



SURVEY_SHIPS = [
#    "EKMON-40", "EKMON-4B"
        ]

sample_survey = {
    "signature": "X1-RJ19-73095E-B3B61B",
    "symbol": "X1-RJ19-73095E",
    "deposits":
    [
        {"symbol": "PRECIOUS_STONES"},
        {"symbol": "PRECIOUS_STONES"},
        {"symbol": "SILICON_CRYSTALS"},
        {"symbol": "COPPER_ORE"}
    ],
    "expiration": "2023-07-29T20:01:08.000Z",
    "size": "LARGE"
}


PROBE_SHIPS = ["EKMON-2"]

WAYPOINTS = []
WAYPOINT_PROBES = []


SYSTEM = "X1-RJ19"
SHIP = "EKMON-1"

CONTRACT = ''
ITEM = []

ASTEROIDS = "X1-RJ19-73095E"
DELIVERY = ""


def extract(ship, survey=None):
    endpoint = "v2/my/ships/" + ship + "/extract"
    params = None
    if survey is not None:
        params = {"survey": survey}
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

def sell(ship, saved):
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
    return new_cargo

def purchase(ship, item, units):
    endpoint = "v2/my/ships/" + ship + "/purchase"
    params = {"symbol": item, "units": units}
    p = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    return p


def navigate(ship, location):
    endpoint = "v2/my/ships/" + ship + "/navigate"
    params = {"waypointSymbol": location}
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)

def jump(ship, system):
    endpoint = "v2/my/ships/" + ship + "/jump"
    params = {"systemSymbol": system}
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)

def jumpNav(ship, jump_gate, systems, final_waypoint):
    orbit(ship)
    num_jumps = len(systems)
    nav = navigate(ship, jump_gate)
    sleep_time = nav_to_time_delay(nav)
    time.sleep(sleep_time)
    for i in range(num_jumps):
        jump(ship, systems[i])
    nav = navigate(ship, final_waypoint)
    sleep_time = nav_to_time_delay(nav)
    time.sleep(sleep_time)
    return

def deliver(ship, item, quantity, contract):
    endpoint = "v2/my/contracts/" + contract + "/deliver"
    params = {"shipSymbol": ship, "tradeSymbol": item, "units": quantity}
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)

def refuel(ship):
    endpoint = "v2/my/ships/" + ship + "/refuel"
    return myClient.generic_api_call("POST", endpoint, None, TOKEN)


def nav_to_time_delay(nav):
    try:
        start = nav["data"]["nav"]["route"]["departureTime"]
        end = nav["data"]["nav"]["route"]["arrival"]
        startdt = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S.%fZ')
        enddt = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S.%fZ')
        diff = enddt - startdt
        sec = diff.total_seconds()
        return sec
    except TypeError:
        return 60




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
                extraction = extract(ship, survey)
                print(ship + ": " + str(extraction))
                c = extraction["data"]["cargo"]
                capacity = c["capacity"]
                collected = c["units"]
            except TypeError:
                fullCargo = True
            if fullCargo or collected / capacity >= 0.67:
                dock(ship)
                c = sell(ship, ITEM)
                capacity = c["capacity"]
                collected = c["units"]
                print(ship + ": " + str(collected) + "/" + str(capacity))
                if collected/capacity >= 0.5:
                    print(ship + ": " + str(refuel(ship)))
                    orbit(ship)
                    nav = navigate(ship, DELIVERY)
                    print(ship + ": " + "En route to delivery")
                    time.sleep(nav_to_time_delay(nav) + 1)
                    dock(ship)
                    delivery = deliver(ship, ITEM, collected, CONTRACT)
                    if delivery["data"]["contract"]["terms"]["deliver"][0]["unitsRequired"] == delivery["data"]["contract"]["terms"]["deliver"][0]["unitsFulfilled"]:
                        ITEM.pop()
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


def haulerLoop(ship,  contract, origin, use_jump_nav=False, jump_nav_gates_to_origin=None, jump_nav_systems_to_origin=None, jump_nav_gates_to_destination=None, jump_nav_systems_to_destination=None, item=None, destination=None, required=None, fulfilled=None, max_price=None):

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
        max_price = total/required
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



def ore_hound_thread_spawner(lock=None, surveys=None):
    new_threads = []

    while True:
        agent = otherFunctions.getAgent()
        credits = agent["data"]["credits"]
        shipyard = buyShip.getShipyard()
        ships = shipyard["data"]["ships"]
        ore_hound = None
        for ship in ships:
            if ship["type"] == "SHIP_ORE_HOUND":
                ore_hound = ship
        ore_hound_price = ore_hound["purchasePrice"]
        market = otherFunctions.getMarket(SYSTEM, otherFunctions.SHIPYARD)
        goods = market["data"]["tradeGoods"]
        mount_price = None
        for good in goods:
            if good["symbol"] == "MOUNT_MINING_LASER_II":
                mount_price = good["purchasePrice"]
        total_price = ore_hound_price + mount_price + 4000
        print("***")
        print("CREDITS:", credits)
        print("COST:", total_price)
        print("***")
        if credits > total_price:
            new_ship = buyShip.buyOreHound()
            new_thread = threading.Thread(target=shipLoop, args=(new_ship,lock,surveys), daemon=True)
            new_threads.append(new_thread)
            new_thread.start()
            print("New Ship:", new_ship)

        time.sleep(600)



def survey_loop(ship, lock: threading.Lock, surveys):
    orbit(ship)
    while True:
        new_survey = createSurvey(ship)
        if new_survey is not False:
            cooldown = new_survey["data"]["cooldown"]["totalSeconds"]
            survey_list = new_survey["data"]["surveys"]
            while not lock.acquire():
                time.sleep(1)
            surveys.extend(survey_list)
            lock.release()
            time.sleep(cooldown)
        else:
            time.sleep(60)



def main():
    miningDrones = MINING_SHIPS
    threads = []
    survey_lock = threading.Lock()
    surveys = []

    for surveyor in SURVEY_SHIPS:
        x = threading.Thread(target=survey_loop, args=(surveyor, survey_lock, surveys), daemon=True)
        threads.append(x)
        x.start()
        print("surveyor started!", surveyor)
        time.sleep(3)

    for drone in miningDrones:
        x = threading.Thread(target=shipLoop, args=(drone, survey_lock, surveys), daemon=True)
        threads.append(x)
        x.start()
        print("miner started!", drone)
        time.sleep(3)

    x = threading.Thread(target=ore_hound_thread_spawner, args=(survey_lock, surveys), daemon=True)
    threads.append(x)
    x.start()
    if __name__ == '__main__':
        while True:
            pass



if __name__ == '__main__':
    main()



