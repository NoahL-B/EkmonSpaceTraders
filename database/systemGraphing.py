from dijkstar import Graph, find_path
from database.dbFunctions import distance


def make_dij_graph(all_systems):
    dij = Graph()
    for s1 in all_systems:
        has_gate_1 = False
        for wp in s1["waypoints"]:
            if wp["type"] == "JUMP_GATE":
                has_gate_1 = True
        for s2 in all_systems:
            has_gate_2 = False
            for wp in s2["waypoints"]:
                if wp["type"] == "JUMP_GATE":
                    has_gate_2 = True
            dist = distance(s1, s2)
            if has_gate_1 and has_gate_2 and dist < 2000:
                dij.add_edge(s1["symbol"], s2["symbol"], 1)
            else:
                dij.add_edge(s1["symbol"], s2["symbol"], dist)


def dij_path(graph, start_name, end_name):
    return find_path(graph, start_name, end_name)