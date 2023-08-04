from main import *


SHIPYARD = "X1-RJ19-51287F"


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
        uninstallMount(shipName, "MOUNT_SURVEYOR_I")
        sell(shipName, [])
        purchase(shipName, "MOUNT_MINING_LASER_II", 2)
        installMount(shipName, "MOUNT_MINING_LASER_II")
        installMount(shipName, "MOUNT_MINING_LASER_II")
    except TypeError:
        print("could not purchase secondary/tertiary mining laser")
    orbit(shipName)
    navigate(shipName, ASTEROIDS)
    return shipName

def buyProbe():
    endpoint = "v2/my/ships/"
    params = {"shipType": "SHIP_PROBE", "waypointSymbol": SHIPYARD}
    purchasedShip = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    shipName = purchasedShip["data"]["ship"]["symbol"]
    orbit(shipName)

    from otherFunctions import patchShipNav
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


def buyRefiningFreighter():
    endpoint = "v2/my/ships/"
    params = {"shipType": "SHIP_REFINING_FREIGHTER", "waypointSymbol": SHIPYARD}
    purchasedShip = myClient.generic_api_call("POST", endpoint, params, TOKEN)
    shipName = purchasedShip["data"]["ship"]["symbol"]
    uninstallMount(shipName, "MOUNT_TURRET_I")
    uninstallMount(shipName, "MOUNT_TURRET_I")
    uninstallMount(shipName, "MOUNT_MISSILE_LAUNCHER_I")
    purchase(shipName, "MOUNT_SURVEYOR_I", 3)
    installMount(shipName, "MOUNT_SURVEYOR_I")
    installMount(shipName, "MOUNT_SURVEYOR_I")
    installMount(shipName, "MOUNT_SURVEYOR_I")
    return shipName

if __name__ == '__main__':
    print(buyRefiningFreighter())