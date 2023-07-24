from main import *

SHIPYARD = "X1-B13-48027C"


def getShipyard():
    endpoint = "v2/systems/" + SYSTEM + "/waypoints/" + SHIPYARD + "/shipyard"
    params = None
    return myClient.generic_api_call("GET", endpoint, params, TOKEN)


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
    try:
        purchase(shipName, "MOUNT_MINING_LASER_II", 1)
        installMount(shipName, "MOUNT_MINING_LASER_II")
    except TypeError:
        print("could not purchase secondary mining laser")
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

def installMount(ship, mount):
    endpoint = "v2/my/ships/" + ship + "/mounts/install"
    params = {"symbol": mount}
    return myClient.generic_api_call("POST", endpoint, params, TOKEN)

if __name__ == '__main__':
    buyOreHound()