import dijkstar
from dijkstar import Graph, find_path

# import api_requests.api_functions
from database.dbFunctions import distance, access_get_available_jumps
from threading import Lock


MASTER_JUMP_GRAPH = None
MASTER_WARP_GRAPH = None
MASTER_GRAPH_INIT_LOCK = Lock()

def init_master_jump_graph(force_new=False):
    global MASTER_JUMP_GRAPH
    with MASTER_GRAPH_INIT_LOCK:
        if MASTER_JUMP_GRAPH is None or force_new:
            import database.dbFunctions as DBF
            all_systems = DBF.access_get_detailed_systems()
            notable_systems = DBF.get_notable_systems(all_systems)
            MASTER_JUMP_GRAPH = make_dij_graph(notable_systems, False)

    return MASTER_JUMP_GRAPH


def init_master_warp_graph(force_new=False):
    global MASTER_WARP_GRAPH
    with MASTER_GRAPH_INIT_LOCK:
        if MASTER_WARP_GRAPH is None or force_new:
            import database.dbFunctions as DBF
            all_systems = DBF.access_get_detailed_systems()
            notable_systems = DBF.get_notable_systems(all_systems)
            MASTER_WARP_GRAPH = make_dij_graph(notable_systems, True)

    return MASTER_WARP_GRAPH


def make_dij_graph(all_systems, warp_drive=False, engine_speed=30, warp_range=6000, warp_speed="DRIFT"):
    dij = Graph()

    sys_dict = {}
    for s in all_systems:
        sys_name = s["symbol"]
        sys_dict[sys_name] = s

    def warp_time(dist):
        warp_multiplier = 10000
        if warp_speed == "DRIFT":
            warp_multiplier = 300
        elif warp_speed == "CRUISE":
            warp_multiplier = 50
        elif warp_speed == "BURN":
            warp_multiplier = 25
        elif warp_speed == "STEALTH":
            warp_multiplier = 30

        travel_time = round(dist * warp_multiplier / engine_speed + 15)
        return travel_time

    if warp_drive:
        for s1 in all_systems:
            for s2 in all_systems:
                if s1 is not s2:
                    dist = distance(s1, s2)
                    if dist <= warp_range:
                        travel_time = warp_time(dist)
                        dij.add_edge(s1["symbol"], s2["symbol"], travel_time)

    jumps = access_get_available_jumps()
    for jump in jumps:
        origin_system = jump[2]
        destination_system = jump[4]

        dist = distance(sys_dict[origin_system], sys_dict[destination_system])
        cooldown_time = dist + 60

        dij.add_edge(origin_system, destination_system, cooldown_time)
        dij.add_edge(destination_system, origin_system, cooldown_time)

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


init_master_jump_graph()


if __name__ == '__main__':
    print(MASTER_JUMP_GRAPH)