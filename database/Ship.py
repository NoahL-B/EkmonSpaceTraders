

class Ship:

    def __init__(self, ship_symbol, data=None):
        self.symbol = ship_symbol
        self.registration = None
        self.nav = None
        self.crew = None
        self.crew = None
        self.frame = None
        self.reactor = None
        self.engine = None
        self.modules = []
        self.mounts = []
        self.cargo = None
        self.fuel = None
        if data is not None:
            self.update(data)


    def update(self, data: dict):
        if "data" in data.keys():
            data = data["data"]
        self.registration = data["registration"]
        self.nav = data["nav"]
        self.crew = data["crew"]
        self.frame = data["frame"]
        self.reactor = data["reactor"]
        self.engine = data["engine"]
        self.modules = data["modules"]
        self.mounts = data["mounts"]
        self.cargo = data["cargo"]
        self.fuel = data["fuel"]

