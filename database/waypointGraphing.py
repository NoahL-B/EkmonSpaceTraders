import dijkstar
from dijkstar import Graph, find_path
from database.dbFunctions import distance


def make_dij_graph(all_waypoints, fuel_capacity, burn=True):
    dij = Graph()
    for w1 in all_waypoints:
        w1_has_market = False
        for trait in w1['traits']:
            if trait['symbol'] == "MARKETPLACE":
                w1_has_market = True
        for w2 in all_waypoints:
            w2_has_market = False
            for trait in w2['traits']:
                if trait['symbol'] == "MARKETPLACE":
                    w2_has_market = True
            if w1 is not w2 and w1['systemSymbol'] == w2['systemSymbol']:
                dist = distance(w1, w2)
                if dist * (1 + burn) < fuel_capacity - 1:
                    if burn:
                        dist *= 2
                    if not w1_has_market:
                        dist += 10000
                    if not w2_has_market:
                        dist += 10000
                    dij.add_edge(w1["symbol"], w2["symbol"], dist)
    return dij


def dij_path(graph, start_name, end_name):
    try:
        f = find_path(graph, start_name, end_name)
        return f
    except dijkstar.NoPathError:
        return None

