from SECRETS import TOKEN
from SHARED import myClient

class System:

    def __init__(self, data=None):
        self.symbol = None
        self.sectorSymbol = None
        self.type = None
        self.x = None
        self.y = None
        self.waypoints = None
        self.factions = None

        if data is not None:
            self.update(data)

    def update(self, data):
        self.symbol = data["symbol"]
        self.sectorSymbol = data["sectorSymbol"]
        self.type = data["sectorSymbol"]
        self.x = data["x"]
        self.y = data["y"]
        self.waypoints = data["waypoints"]
        self.factions = data["factions"]

    def toDict(self):
        data = {
            "symbol": self.symbol,
            "sectorSymbol": self.sectorSymbol,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "waypoints": self.waypoints,
            "factions": self.factions
        }
        return data

    def __repr__(self):
        return str(self.toDict())


def getSystem(systemSymbol):
    endpoint = "v2/systems/" + systemSymbol
    params = None
    data = myClient.generic_api_call("GET", endpoint, params, TOKEN)["data"]
    return System(data)


def listSystems(limit=10, page=1):
    endpoint = "v2/systems/"
    params = {"limit": limit, "page": page}
    data = myClient.generic_api_call("GET", endpoint, params, TOKEN)
    return data


def listWaypointsInSystem(systemSymbol, limit=10, page=1):
    endpoint = "v2/systems/" + systemSymbol + "/waypoints"
    params = {"limit": limit, "page": page}
    data = myClient.generic_api_call("GET", endpoint, params, TOKEN)
    return data


if __name__ == '__main__':
    print(listSystems(20, 600))