from SECRETS import TOKEN
import api_requests.api_functions as api

class Waypoint:

    def __init__(self, data=None):
        self.symbol = None
        self.type = None
        self.systemSymbol = None
        self.x = None
        self.y = None
        self.orbitals = None
        self.faction = None
        self.traits = None
        self.chart = None
        self.isUnderConstruction = None

        if data is not None:
            self.update(data)

    def update(self, data):
        waypoint = data
        self.symbol = waypoint["symbol"]
        self.type = waypoint["type"]
        self.systemSymbol = waypoint["systemSymbol"]
        self.x = waypoint["x"]
        self.y = waypoint["y"]
        self.isUnderConstruction = waypoint["isUnderConstruction"]
        self.orbitals = waypoint["orbitals"]
        if "faction" in waypoint.keys():
            self.faction = waypoint["faction"]
        self.traits = waypoint["traits"]
        if "chart" in waypoint.keys():
            self.chart = waypoint["chart"]

    def toDict(self):
        data = {
            "symbol": self.symbol,
            "type": self.type,
            "systemSymbol": self.systemSymbol,
            "x": self.x,
            "y": self.y,
            "orbitals": self.orbitals,
            "faction": self.faction,
            "traits": self.traits,
            "chart": self.chart,
            "isUnderConstruction": self.isUnderConstruction
        }
        return data

    def __repr__(self):
        return str(self.toDict())



def getWaypoint(systemSymbol, waypointSymbol):
    data = api.get_waypoint(TOKEN, systemSymbol, waypointSymbol)['data']
    return Waypoint(data)



if __name__ == '__main__':
    print(getWaypoint("X1-UF69", "X1-UF69-I52"))