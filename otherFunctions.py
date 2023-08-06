from SHARED import myClient
from SECRETS import TOKEN


def transfer(send_ship, receive_ship, item, quantity):
    endpoint = "v2/my/ships/" + send_ship + "/transfer"
    params = {"shipSymbol": receive_ship, "tradeSymbol": item, "units": quantity}
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)


def getContract(contract):
    endpoint = "v2/my/contracts/" + contract
    params = None
    return myClient.generic_api_call("GET", endpoint, params, TOKEN)


def fulfillContract(contract):
    endpoint = "v2/my/contracts/" + contract + "/fulfill"
    params = None
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)


def negotiateContract(ship):
    endpoint = "v2/my/ships/" + ship + "/negotiate/contract"
    params = None
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)


def acceptContract(contract):
    endpoint = "v2/my/contracts/" + contract + "/accept"
    params = None
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)


def getWaypoints(system):
    endpoint = "v2/systems/" + system + "/waypoints"
    params = None
    return myClient.generic_api_call("GET", endpoint, params, TOKEN)


def getMarket(system, waypoint):
    endpoint = "v2/systems/" + system + "/waypoints/" + waypoint + "/market"
    params = None
    return myClient.generic_api_call("GET", endpoint, params, TOKEN)


def getAgent():
    endpoint = "v2/my/agent"
    params = None
    return myClient.generic_api_call("GET", endpoint, params, TOKEN)


def patchShipNav(ship, flightMode):
    endpoint = "v2/my/ships/" + ship + "/nav"
    params = {"flightMode": flightMode}
    return myClient.generic_api_call("PATCH", endpoint, params, TOKEN)


if __name__ == '__main__':
    print(patchShipNav("EKMON-1", "BURN"))