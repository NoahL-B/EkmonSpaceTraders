from SpacePyTraders import client
import time
import threading

USERNAME = "EKMON"
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGlmaWVyIjoiRUtNT04iLCJ2ZXJzaW9uIjoidjIiLCJyZXNldF9kYXRlIjoiMjAyMy0wNy0xNSIsImlhdCI6MTY4OTQ0NTA5Mywic3ViIjoiYWdlbnQtdG9rZW4ifQ.TovM6gCtQCVEY3M8m5RVVioTXrYa8RBGDeArPjVMrUI2UD-NYFwvH4QCb9dXFKWUoAFWmjxrF84L1Ctw85omq2jhQSS390SZBstG6DHrqyhT__2XVuO1RLHy1-o-stXF5mSaG6DTROfkoMZMLo_WEpSy9SvHF9Qj5kowOPF_odFf2q433C0gtFKpSPaOO86_bFffRoGKSgkgyds5VlqkJgfVUGhFoawOitDtEBnUUWnlWj7JF9Mefk43kRvA2Cdxncg14BV2HD3qMCDIZ1tIbQPnbJJX4jiPWEc3yIDemSkPTHebKIf1uxy8wkQqJ6Hrmu_7UR1HpnatQ9nbFEBxrg"

myClient = client.Client(USERNAME, TOKEN)

ALL_SHIPS = ["EKMON-1", "EKMON-3", "EKMON-4"]

    #[, "EKMON-5", "EKMON-6", "EKMON-7", "EKMON-8", "EKMON-9", "EKMON-A", "EKMON-B", "EKMON-C", "EKMON-D", "EKMON-E", "EKMON-F", "EKMON-10", "EKMON-11", "EKMON-12" "EKMON-13", "EKMON-14", "EKMON-15", "EKMON-16", "EKMON-17", "EKMON-18", "EKMON-19", "EKMON-1A", "EKMON-1B", "EKMON-1C", "EKMON-1D", "EKMON-1E", "EKMON-1F"]


SHIP = "EKMON-3"

CONTRACT = "clk4bzl9t000hs60cins0j1ay"
ITEM = "IRON_ORE"

ASTEROIDS = "X1-JF24-23225F"
DELIVERY = "X1-JF24-97552X"


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
    for item in inv:
        symbol = item["symbol"]
        units = item["units"]

        if symbol not in saved:

            endpoint = "v2/my/ships/" + ship + "/sell"
            params = {"symbol": symbol, "units": units}
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



def shipLoop(ship):
    while True:
        orbit(ship)
        time.sleep(1)
        print(ship + ": " + str(extract(ship)))
        time.sleep(1)
        dock(ship)
        time.sleep(1)
        sell(ship, ITEM)
        time.sleep(1)
        c = cargo(ship)["data"]
        capacity = c["capacity"]
        collected = c["units"]
        print(ship + ": " + str(collected) + "/" + str(capacity))
        if collected/capacity >= 0.8:
            print(ship + ": " + str(refuel(ship)))
            time.sleep(1)
            orbit(ship)
            time.sleep(1)
            print(ship + ": " + str(navigate(ship, DELIVERY)))
            print(ship + ": " + "En route to delivery")
            time.sleep(50)
            dock(ship)
            time.sleep(1)
            print(ship + ": " + str(deliver(ship, ITEM, collected, CONTRACT)))
            time.sleep(1)
            print(ship + ": " + str(refuel(ship)))
            time.sleep(1)
            orbit(ship)
            time.sleep(1)
            print(ship + ": " + str(navigate(ship, ASTEROIDS)))
            print(ship + ": " + "En route to asteroids")
            time.sleep(50)
            print(ship + ": " + "Returned to asteroids")
        else:
            time.sleep(70)









def main1():
    for ship in ALL_SHIPS:
        orbit(ship)
    time.sleep(1)
    for ship in ALL_SHIPS:
        print(extract(ship))

def main2():
    for ship in ALL_SHIPS:
        dock(ship)
    for ship in ALL_SHIPS:
        sell(ship, ITEM)

def main3():
    for ship in ALL_SHIPS:
        print(ship)
        print(cargo(ship))

def main4():
    shipLoop("EKMON-1")


def main5():
    miningDrones = ALL_SHIPS
    threads = []
    for drone in miningDrones:
        x = threading.Thread(target=shipLoop, args=(drone,), daemon=True)
        threads.append(x)
        x.start()
    for t in threads:
        t.join()




if __name__ == '__main__':
    main5()



