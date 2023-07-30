

class Agent:

    def __init__(self, data: dict):
        if "data" in data.keys():
            data = data["data"]

        self.symbol = data["symbol"]
        self.headquarters = data["headquarters"]
        self.credits = int(data["credits"])
        self.startingFaction = data["startingFaction"]
