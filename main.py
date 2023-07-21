from SpacePyTraders import client
import time
import threading
from datetime import datetime

USERNAME = "EKMON"
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGlmaWVyIjoiRUtNT04iLCJ2ZXJzaW9uIjoidjIiLCJyZXNldF9kYXRlIjoiMjAyMy0wNy0xNSIsImlhdCI6MTY4OTQ0NTA5Mywic3ViIjoiYWdlbnQtdG9rZW4ifQ.TovM6gCtQCVEY3M8m5RVVioTXrYa8RBGDeArPjVMrUI2UD-NYFwvH4QCb9dXFKWUoAFWmjxrF84L1Ctw85omq2jhQSS390SZBstG6DHrqyhT__2XVuO1RLHy1-o-stXF5mSaG6DTROfkoMZMLo_WEpSy9SvHF9Qj5kowOPF_odFf2q433C0gtFKpSPaOO86_bFffRoGKSgkgyds5VlqkJgfVUGhFoawOitDtEBnUUWnlWj7JF9Mefk43kRvA2Cdxncg14BV2HD3qMCDIZ1tIbQPnbJJX4jiPWEc3yIDemSkPTHebKIf1uxy8wkQqJ6Hrmu_7UR1HpnatQ9nbFEBxrg"

myClient = client.Client(USERNAME, TOKEN)

MINING_SHIPS = ["EKMON-1", "EKMON-5", "EKMON-6",
                "EKMON-7", "EKMON-8", "EKMON-9", "EKMON-A", "EKMON-B",
                "EKMON-C", "EKMON-D", "EKMON-E", "EKMON-F", "EKMON-10",
                "EKMON-11", "EKMON-1B", "EKMON-1C", "EKMON-1D", "EKMON-1E",
                "EKMON-1F", "EKMON-20", "EKMON-21", "EKMON-22", "EKMON-23", "EKMON-24",
                "EKMON-25", "EKMON-26", "EKMON-27", 'EKMON-28', 'EKMON-29', 'EKMON-2A',
                'EKMON-2B', 'EKMON-2C', 'EKMON-2D', 'EKMON-2E', 'EKMON-2F', 'EKMON-30',
                'EKMON-31', 'EKMON-32']

# ["EKMON-3", "EKMON-4"]

PROBE_SHIPS = ["EKMON-2", "EKMON-12", "EKMON-13", "EKMON-14", "EKMON-15", "EKMON-16", "EKMON-17", "EKMON-18", "EKMON-19", "EKMON-1A"]
WAYPOINTS = ['X1-JF24-77691C', 'X1-JF24-06790Z', 'X1-JF24-97552X', 'X1-JF24-78153C', 'X1-JF24-01924F', 'X1-JF24-23225F', 'X1-JF24-45556D', 'X1-JF24-73757X', 'X1-JF24-34538X', 'X1-JF24-00189Z']

WAYPOINT_PROBES = [('X1-JF24-73757X', "EKMON-2"),
                   ('X1-JF24-77691C', 'EKMON-12'),
                   ('X1-JF24-06790Z', 'EKMON-13'),
                   ('X1-JF24-97552X', 'EKMON-14'),
                   ('X1-JF24-78153C', 'EKMON-15'),
                   ('X1-JF24-01924F', 'EKMON-16'),
                   ('X1-JF24-23225F', 'EKMON-17'),
                   ('X1-JF24-45556D', 'EKMON-18'),
                   ('X1-JF24-34538X', 'EKMON-19'),
                   ('X1-JF24-00189Z', 'EKMON-1A')]


SYSTEM = "X1-JF24"
SHIP = "EKMON-1"

CONTRACT = "clkbnrophqi88s60cuut63fun"
ITEM = ['MOUNT_SURVEYOR_I']

ASTEROIDS = "X1-JF24-23225F"
DELIVERY = "X1-JF24-73757X"


def extract(ship):
    endpoint = "v2/my/ships/" + ship + "/extract"
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
    return new_cargo

def purchase(ship, item, units):
    endpoint = "v2/my/ships/" + ship + "/purchase"
    params = {"symbol": item, "units": units}
    print(myClient.generic_api_call("POST", endpoint, params, TOKEN))


def navigate(ship, location):
    endpoint = "v2/my/ships/" + ship + "/navigate"
    params = {"waypointSymbol": location}
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)

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




def shipLoop(ship):
    orbit(ship)
    while True:
        try:
            fullCargo = False
            collected = None
            capacity = None
            extraction = None
            try:
                extraction = extract(ship)
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
                if collected/capacity >= 0.67:
                    print(ship + ": " + str(refuel(ship)))
                    orbit(ship)
                    nav = navigate(ship, DELIVERY)
                    print(ship + ": " + "En route to delivery")
                    time.sleep(nav_to_time_delay(nav) + 1)
                    dock(ship)
                    print(ship + ": " + str(deliver(ship, ITEM, collected, CONTRACT)))
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



def main():
    miningDrones = MINING_SHIPS
    threads = []
    for drone in miningDrones:
        x = threading.Thread(target=shipLoop, args=(drone,), daemon=True)
        threads.append(x)
        x.start()
        time.sleep(1.5)
    for t in threads:
        t.join()




if __name__ == '__main__':
    main()



