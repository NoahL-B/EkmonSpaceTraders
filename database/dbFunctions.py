import math
import pyodbc
import os
import dijkstar

from database import Waypoint
from database.System import *
from otherFunctions import *

base_path = os.path.abspath(os.getcwd())
db_path = os.path.join(base_path, "SpaceTradersDatabase.accdb")

driver = 'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + db_path
conn = pyodbc.connect(driver)
conn.autocommit = True
cursor = conn.cursor()


def sector_to_sql(sector):
    cmd = 'INSERT INTO System (symbol, sectorSymbol, type, x, y) VALUES '
    cmd += "('" + sector["symbol"] + "', '" + sector["sectorSymbol"] + "', '" + sector["type"] + "', '" + str(sector["x"]) + "', '" + str(sector["y"]) + "');"
    return cmd


def waypoint_to_sql(wp):
    cmd = 'INSERT INTO Waypoint (symbol, type, systemSymbol, x, y'

    if wp.faction is not None:
        cmd += ", faction"

    for t in wp.traits:
        trait_symbol = t["symbol"]
        cmd += ", " + trait_symbol

    cmd += ') VALUES '
    cmd += "('" + wp.symbol + "', '" + wp.type + "', '" + wp.systemSymbol + "', '" + str(wp.x) + "', '" + str(wp.y) + "'"

    if wp.faction is not None:
        cmd += ", '" + wp.faction["symbol"] + "'"

    for _ in wp.traits:
        cmd += ", True"

    cmd += ");"
    return cmd


def distance(system_1, system_2):
    x1 = system_1["x"]
    x2 = system_2["x"]
    y1 = system_1["y"]
    y2 = system_2["y"]

    dist = math.sqrt((x2-x1) ** 2 + (y2-y1) ** 2)
    return dist


def systems_to_waypoints(system_list):
    all_waypoints = []
    for s in system_list:
        systemSymbol = s["symbol"]
        for w in s["waypoints"]:
            w["systemSymbol"] = systemSymbol
            all_waypoints.append(w)
    return all_waypoints


def find_nearest_with_trait(start_system, all_systems, target_trait, max_distance=None):
    dist_list = dist_systems(start_system, all_systems)

    for (d, s) in dist_list:
        if s is start_system:
            pass
        else:
            if max_distance is not None:
                if d > max_distance:
                    return None
            wps = get_all_waypoints_in_system(s["symbol"])
            for wp in wps:
                for t in wp["traits"]:
                    if t["symbol"] == target_trait:
                        return wp


def find_all_with_trait(all_systems, target_trait):
    wp_list = []
    counter = 0
    for s in all_systems:
        wps = get_all_waypoints_in_system(s["symbol"])
        for wp in wps:
            for t in wp["traits"]:
                if t["symbol"] == target_trait:
                    wp_list.append(wp)
        counter += 1
        if counter % 25 == 0:
            print(len(wp_list), "/", counter)
    return wp_list


def find_all_with_trait_2(all_waypoints, target_trait):
    wp_list = []
    counter = 0
    for wp in all_waypoints:
        for t in wp["traits"]:
            if t["symbol"] == target_trait:
                wp_list.append(wp)
        counter += 1
        if counter % 25 == 0:
            print(len(wp_list), "/", counter)
    len(wp_list), "/", counter
    return wp_list


def search_marketplaces_for_item(waypoint_list, item):
    stocked_markets = []
    for wp in waypoint_list:
        wp_name = wp["symbol"]
        wp_system = wp["systemSymbol"]
        mark = getMarket(wp_system, wp_name)
        if search_marketplace_for_item(mark, item):
            stocked_markets.append(wp)
    return stocked_markets


def search_marketplace_for_item(marketplace, item):
    if "data" in marketplace.keys():
        marketplace = marketplace["data"]

    goods = []
    goods.extend(marketplace["exports"])
    goods.extend(marketplace["imports"])
    goods.extend(marketplace["exchange"])

    for good in goods:
        if good["symbol"] == item:
            return True
    return False


def get_system(system_name, all_systems):
    for s in all_systems:
        if s["symbol"] == system_name:
            return s


def dist_systems(start_system, all_systems):
    dist_list = []
    for s in all_systems:
        d = distance(start_system, s)
        d_tup = (d, s)
        dist_list.append(d_tup)
    dist_list.sort()
    return dist_list


def is_charted(system):
    if len(system["waypoints"]) == 0:
        return True

    wp = system["waypoints"][0]

    wp_obj = Waypoint.getWaypoint(system["symbol"], wp["symbol"])
    for t in wp_obj.traits:
        if t["symbol"] == "UNCHARTED":
            return False
    return True


def get_all_systems():
    all_systems = []

    num_systems = listSystems()["meta"]["total"]
    systems_per_page = 20
    num_pages = num_systems // systems_per_page

    for page in range(1, num_pages + 1):
        l = listSystems(systems_per_page, page)
        for i in range(systems_per_page):
            all_systems.append(l["data"][i])
            print(l["data"][i]["symbol"])

    return all_systems


def get_all_waypoints_in_system(systemSymbol):
    system_waypoints = []

    waypoints_per_page = 20

    first_page = listWaypointsInSystem(systemSymbol, waypoints_per_page)

    for wp in first_page["data"]:
        system_waypoints.append(wp)

    return system_waypoints


def get_all_waypoints(all_systems):
    notable_systems = get_notable_systems(all_systems)
    all_waypoints = []
    for s in notable_systems:
        systemSymbol = s["symbol"]
        system_waypoints = get_all_waypoints_in_system(systemSymbol)
        for wp in system_waypoints:
            all_waypoints.append(wp)
            if len(all_waypoints) % 100 == 0:
                print(len(all_waypoints))
    return all_waypoints


def get_notable_systems(all_systems):
    # a notable system is a system that contains a non-zero number of waypoints
    notable_systems = []
    for s in all_systems:
        if len(s["waypoints"]) > 0:
            notable_systems.append(s)
    return notable_systems


def populate_waypoints(all_systems):
    all_waypoints = get_all_waypoints(all_systems)
    for wp in all_waypoints:
        wp_obj = Waypoint.Waypoint(wp)
        cmd = waypoint_to_sql(wp_obj)
        cursor.execute(cmd)


def get_systems_from_access():
    raw_systems = []
    cursor.execute("SELECT * FROM System")
    for row in cursor:
        raw_systems.append(row)

    complete_systems = []

    for raw_sys in raw_systems:
        complete_system = {
            "symbol": raw_sys[0],
            "sectorSymbol": raw_sys[1],
            "type": raw_sys[2],
            "x": raw_sys[3],
            "y": raw_sys[4],
            "waypoints": [],
            "factions": []
        }
        cmd = 'SELECT symbol, type, x, y, faction FROM Waypoint WHERE systemSymbol=?;'
        cursor.execute(cmd, (raw_sys[0],))
        for raw_wp in cursor:
            dict_wp = {
                "symbol": raw_wp[0],
                "type": raw_wp[1],
                "x": raw_wp[2],
                "y": raw_wp[3]
            }
            faction = raw_wp[4]
            if faction is not None and faction != "":
                already_listed = False
                for already_listed_faction in complete_system["factions"]:
                    if already_listed_faction["symbol"] == faction:
                        already_listed = True
                if not already_listed:
                    complete_system["factions"].append({"symbol": faction})
            complete_system["waypoints"].append(dict_wp)
        complete_systems.append(complete_system)
    return complete_systems


def get_waypoints_from_access():
    waypoints = []
    cursor.execute("SELECT * FROM Waypoint")
    for raw_wp in cursor:
        traits = []
        dict_wp = {
            "symbol": raw_wp[0],
            "type": raw_wp[1],
            "systemSymbol": raw_wp[2],
            "x": raw_wp[3],
            "y": raw_wp[4],
            "traits": traits
        }
        for trait_num in range(6, 65):
            if raw_wp[trait_num]:
                trait_name = raw_wp.cursor_description[trait_num][0]
                traits.append({"symbol": trait_name})
        waypoints.append(dict_wp)
    return waypoints


if __name__ == '__main__':
    import time
    start = time.time()
    get_all_systems()
    end = time.time()
    diff = start - end
    print(diff)

"""
PathInfo(nodes=['X1-VM60', 'X1-UM56', 'X1-MG94', 'X1-JT47', 'X1-QD56', 'X1-SS88', 'X1-FZ66', 'X1-AM51', 'X1-JC43', 'X1-XC54', 'X1-BB82', 'X1-CZ83', 'X1-JA13', 'X1-AU64', 'X1-XA9', 'X1-NU89', 'X1-US18', 'X1-UN56', 'X1-GS91', 'X1-JM65', 'X1-QR77', 'X1-NN9', 'X1-DU50', 'X1-RH51', 'X1-GA17', 'X1-ZN96', 'X1-ZX72', 'X1-BV95', 'X1-NM79', 'X1-UX21', 'X1-FV96', 'X1-YV12', 'X1-BB92', 'X1-SG45', 'X1-TD82', 'X1-GZ67'], edges=[2002.0029970007538, 1, 1, 1, 1, 2371.6334033741387, 1, 1, 1, 1, 3302.1841256962034, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], costs=[2002.0029970007538, 1, 1, 1, 1, 2371.6334033741387, 1, 1, 1, 1, 3302.1841256962034, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], total_cost=13322.244587750982)
"""