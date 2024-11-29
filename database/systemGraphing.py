import dijkstar
from dijkstar import Graph, find_path
from database.dbFunctions import distance


def make_dij_graph(all_systems, warp_drive=True):
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
            elif warp_drive:
                dij.add_edge(s1["symbol"], s2["symbol"], dist)
    return dij


def dij_path(graph, start_name, end_name):
    try:
        f = find_path(graph, start_name, end_name)
        return f
    except dijkstar.NoPathError:
        return None


def connected_systems_list(graph, origin):
    sssp = dijkstar.algorithm.single_source_shortest_paths(graph, origin)
    system_names = []
    for n in sssp.keys():
        system_names.append(n)
    return system_names


def get_jump_networks(all_systems):
    dij = make_dij_graph(all_systems, False)
    system_counted = {}
    for s in all_systems:
        s_name = s["symbol"]
        system_counted[s_name] = False
    all_networks = []
    for s in system_counted.keys():
        if not system_counted[s]:
            csl = connected_systems_list(dij, s)
            for s2 in csl:
                system_counted[s2] = csl
            all_networks.append(csl)
    system_counted["all_networks"] = all_networks
    return system_counted
