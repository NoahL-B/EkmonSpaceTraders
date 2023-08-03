import math

class Node:
    def __init__(self, name: str, x: int, y: int, data:object):
        self.name = name
        self.x = x
        self.y = y
        self.data = data
        self.edges = {}

    def distance(self, other):
        x1 = self.x
        y1 = self.y
        x2 = other.x
        y2 = other.y
        sos = (x1-x2)**2 + (y1-y2)**2
        dist = math.sqrt(sos)
        return dist

    def get_data(self):
        return self.data

    def add_edge(self, other, weight):
        self.edges
