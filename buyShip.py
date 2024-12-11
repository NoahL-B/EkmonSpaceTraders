from SHARED import myClient
from SECRETS import TOKEN
from main import orbit
from otherFunctions import patchShipNav


def getShipyard(system, waypoint):
    endpoint = "v2/systems/" + system + "/waypoints/" + waypoint + "/shipyard"
    params = None
    return myClient.generic_api_call("GET", endpoint, params, TOKEN)


def findShipyard(system, ship_type):
    from database.dbFunctions import get_waypoints_from_access

    waypoints = get_waypoints_from_access(system)
    for wp in waypoints:
        for t in wp['traits']:
            if t['symbol'] == "SHIPYARD":
                shipyard = getShipyard(system, wp['symbol'])
                for s in shipyard['data']['shipTypes']:
                    if s['type'] == ship_type:
                        return wp['symbol']



def buyMiningDrone(shipyard):
    endpoint = "v2/my/ships/"
    params = {"shipType": "SHIP_MINING_DRONE", "waypointSymbol": shipyard}
    purchasedShip = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    shipName = purchasedShip["data"]["ship"]["symbol"]
    orbit(shipName)
    patchShipNav(shipName, "BURN")
    return shipName


def buyOreHound(shipyard):
    endpoint = "v2/my/ships/"
    params = {"shipType": "SHIP_ORE_HOUND", "waypointSymbol": shipyard}
    purchasedShip = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    shipName = purchasedShip["data"]["ship"]["symbol"]
    orbit(shipName)
    patchShipNav(shipName, "BURN")
    return shipName


def buySurveyor(shipyard):
    endpoint = "v2/my/ships/"
    params = {"shipType": "SHIP_SURVEYOR", "waypointSymbol": shipyard}
    purchasedShip = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    shipName = purchasedShip["data"]["ship"]["symbol"]
    orbit(shipName)
    patchShipNav(shipName, "BURN")
    return shipName


def buyProbe(shipyard):
    endpoint = "v2/my/ships/"
    params = {"shipType": "SHIP_PROBE", "waypointSymbol": shipyard}
    purchasedShip = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    shipName = purchasedShip["data"]["ship"]["symbol"]
    orbit(shipName)
    patchShipNav(shipName, "BURN")
    return shipName


def buySiphonDrone(shipyard):
    endpoint = "v2/my/ships/"
    params = {"shipType": "SHIP_SIPHON_DRONE", "waypointSymbol": shipyard}
    purchasedShip = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    shipName = purchasedShip["data"]["ship"]["symbol"]
    orbit(shipName)
    patchShipNav(shipName, "BURN")
    return shipName


def installMount(ship, mount):
    endpoint = "v2/my/ships/" + ship + "/mounts/install"
    params = {"symbol": mount}
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)


def uninstallMount(ship, mount):
    endpoint = "v2/my/ships/" + ship + "/mounts/remove"
    params = {"symbol": mount}
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)


def buyLightHauler(shipyard):
    endpoint = "v2/my/ships/"
    params = {"shipType": "SHIP_LIGHT_HAULER", "waypointSymbol": shipyard}
    purchasedShip = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    shipName = purchasedShip["data"]["ship"]["symbol"]
    orbit(shipName)
    patchShipNav(shipName, "BURN")
    return shipName


def buyRefiningFreighter(shipyard):
    endpoint = "v2/my/ships/"
    params = {"shipType": "SHIP_REFINING_FREIGHTER", "waypointSymbol": shipyard}
    purchasedShip = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    shipName = purchasedShip["data"]["ship"]["symbol"]
    orbit(shipName)
    patchShipNav(shipName, "BURN")
    return shipName


if __name__ == '__main__':
    pass