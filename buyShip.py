from main import *

SHIPYARD = "X1-JF24-73757X"

def buyMiningDrone():
    endpoint = "v2/my/ships/"
    params = {"shipType": "SHIP_MINING_DRONE", "waypointSymbol": SHIPYARD}
    purchasedShip = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    shipName = purchasedShip["data"]["ship"]["symbol"]
    orbit(shipName)
    navigate(shipName, ASTEROIDS)
    return shipName

def buyOreHound():
    endpoint = "v2/my/ships/"
    params = {"shipType": "SHIP_ORE_HOUND", "waypointSymbol": SHIPYARD}
    purchasedShip = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    shipName = purchasedShip["data"]["ship"]["symbol"]
    orbit(shipName)
    navigate(shipName, ASTEROIDS)
    return shipName

def buyProbe():
    endpoint = "v2/my/ships/"
    params = {"shipType": "SHIP_PROBE", "waypointSymbol": SHIPYARD}
    purchasedShip = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    shipName = purchasedShip["data"]["ship"]["symbol"]
    orbit(shipName)
    destination_set = False
    for waypoint in WAYPOINTS:
        if not destination_set:
            ship_present = False
            for pairing in WAYPOINT_PROBES:
                w, p = pairing
                if w == waypoint:
                    ship_present = True
            if not ship_present:
                destination_set = True
                navigate(shipName, waypoint)
                wp = waypoint, shipName
                WAYPOINT_PROBES.append(wp)
                return wp
