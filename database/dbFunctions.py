import datetime
import math

from database import Waypoint
from database.System import *
from otherFunctions import *
from SHARED import *


def sector_to_sql(sector):
    cmd = 'INSERT INTO System (symbol, sectorSymbol, type, x, y) VALUES '
    cmd += "('" + sector["symbol"] + "', '" + sector["sectorSymbol"] + "', '" + sector["type"] + "', '" + str(sector["x"]) + "', '" + str(sector["y"]) + "');"
    return cmd


def waypoint_to_sql(wp, update_not_insert=False):
    if update_not_insert:
        return waypoint_to_sql_2(wp)

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


UNCHARTED_TRAIT_DICT = {
        "symbol": "UNCHARTED",
        "name": "Uncharted",
        "description": "An unexplored region of space, full of potential discoveries and hidden dangers."
      }

def waypoint_to_sql_2(wp):
    if UNCHARTED_TRAIT_DICT in wp.traits:
        return False

    cmd = 'UPDATE Waypoint SET Waypoint.UNCHARTED=False'

    if wp.faction is not None:
        cmd += ", Waypoint.faction='" + wp.faction["symbol"] + "'"

    for t in wp.traits:
        trait_symbol = t["symbol"]
        cmd += ", Waypoint." + trait_symbol + "=True"

    cmd += " WHERE (Waypoint.symbol='" + wp.symbol + "');"

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


def get_systems_dot_json():
    endpoint = "v2/systems.json"
    params = None
    return myClient.generic_api_call("GET", endpoint, params, TOKEN)


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

def get_all_waypoints_generator(all_systems):
    notable_systems = get_notable_systems(all_systems)
    for s in notable_systems:
        systemSymbol = s["symbol"]
        system_waypoints = get_all_waypoints_in_system(systemSymbol)
        for wp in system_waypoints:
            yield wp


def get_notable_systems(all_systems):
    # a notable system is a system that contains a non-zero number of waypoints
    notable_systems = []
    for s in all_systems:
        if len(s["waypoints"]) > 0:
            notable_systems.append(s)
    return notable_systems


def populate_waypoints(all_systems):
    access_waypoints = get_waypoints_from_access()
    access_waypoint_symbols = []
    for awp in access_waypoints:
        access_waypoint_symbols.append(awp["symbol"])

    counter = 0

    for wp in get_all_waypoints_generator(all_systems):
        wp_obj = Waypoint.Waypoint(wp)
        needs_update = False
        if wp["symbol"] in access_waypoint_symbols:
            needs_update = True
        cmd = waypoint_to_sql(wp_obj, needs_update)
        if cmd:
            cursor.execute(cmd)
        counter += 1
        print("\r", counter, wp["symbol"], end="")


def populate_systems(all_systems):
    for s in all_systems:
        cmd = sector_to_sql(s)
        cursor.execute(cmd)


def get_systems_from_access():
    raw_systems = []
    cursor.execute("SELECT * FROM System")
    for row in cursor:
        raw_systems.append(row)

    sys_dicts_by_name = {}

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
        sys_dicts_by_name[raw_sys[0]] = complete_system

    all_waypoints = get_waypoints_from_access()

    for full_wp in all_waypoints:
        sys_wp = {
            "symbol": full_wp["symbol"],
            "type": full_wp["type"],
            "x": full_wp["x"],
            "y": full_wp["y"]
        }
        faction = None
        if "faction" in full_wp.keys():
            faction = {"symbol": full_wp["faction"]}
        active_system = sys_dicts_by_name[full_wp["systemSymbol"]]
        active_system["waypoints"].append(sys_wp)
        if faction is not None:
            if faction not in active_system["factions"]:
                active_system["factions"].append(faction)

    sys_list = []
    for sys in sys_dicts_by_name.values():
        sys_list.append(sys)
    return sys_list


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
        faction = raw_wp[5]
        if faction is not None and faction != "":
            dict_wp["faction"] = faction

        for trait_num in range(6, 65):
            if raw_wp[trait_num]:
                trait_name = raw_wp.cursor_description[trait_num][0]
                traits.append({"symbol": trait_name})
        waypoints.append(dict_wp)
    return waypoints


def access_insert_entry(table_name, column_name_list, value_list):
    cmd = "INSERT INTO " + table_name + "(" + column_name_list[0]
    for col_name in column_name_list[1:]:
        cmd += ", " + col_name
    cmd += ") VALUES ('" + str(value_list[0])
    for value in value_list[1:]:
        cmd += "', '" + str(value)
    cmd += "');"
    cursor.execute(cmd)


def access_update_entry(table_name, update_column_name_list, update_value_list, where_column_name_list, where_value_list):
    cmd = "UPDATE " + table_name + " SET " + table_name + "." + update_column_name_list[0] + ' = ?'
    for i in range(1, len(update_column_name_list)):
        cmd += ", " + table_name + "." + update_column_name_list[i] + ' = ?'
    cmd += " WHERE (((" + table_name + "." + where_column_name_list[0] + ')=?)'
    for i in range(1, len(where_column_name_list)):
        cmd += " AND ((" + table_name + "." + where_column_name_list[i] + ')=?)'
    cmd += ");"
    params = tuple(update_value_list + where_value_list)

    cursor.execute(cmd, params)


def access_get_market(waypoint):
    cmd = "SELECT * FROM Markets WHERE Waypoint=?"
    cursor.execute(cmd, (waypoint,))
    market_vals = []
    for m in cursor:
        good_dict = {
            "waypoint": m[1],
            "symbol": m[2],
            "tradeVolume": m[3],
            "supply": m[4],
            "purchasePrice": m[5],
            "sellPrice": m[6],
            "timeStamp": m[7]
        }
        market_vals.append(good_dict)

    return market_vals


def access_record_market(market_dict):
    current_time = datetime.datetime.now(datetime.timezone.utc)
    waypoint = market_dict["data"]["symbol"]
    if "tradeGoods" in market_dict["data"].keys():
        trade_goods = market_dict["data"]["tradeGoods"]

        existing_market = access_get_market(waypoint)

        for trade_good in trade_goods:
            entry_present = False
            for good in existing_market:
                if trade_good["symbol"] == good["symbol"]:
                    entry_present = True

            if entry_present:
                access_update_entry("Markets", ["TradeVolume", "Supply", "PurchasePrice", "SellPrice", "timestamp"], [trade_good["tradeVolume"], trade_good["supply"], trade_good["purchasePrice"], trade_good["sellPrice"], current_time], ["Waypoint", "Symbol"], [waypoint, trade_good["symbol"]])
            else:
                access_insert_entry("Markets", ["Waypoint", "Symbol", "TradeVolume", "Supply", "PurchasePrice", "SellPrice"], [waypoint, trade_good["symbol"], trade_good["tradeVolume"], trade_good["supply"], trade_good["purchasePrice"], trade_good["sellPrice"]])
                access_update_entry("Markets", ["timestamp"], [current_time], ["Waypoint", "Symbol"], [waypoint, trade_good["symbol"]])
    else:
        access_record_low_info_market(market_dict)


def access_record_low_info_market(market_dict):
    waypoint = market_dict["data"]["symbol"]
    trade_goods = market_dict["data"]["exports"] + market_dict["data"]["imports"] + market_dict["data"]["exchange"]

    existing_market = access_get_market(waypoint)

    for trade_good in trade_goods:
        entry_present = False
        for good in existing_market:
            if trade_good["symbol"] == good["symbol"]:
                entry_present = True

        if not entry_present:
            access_insert_entry("Markets", ["Waypoint", "Symbol"], [waypoint, trade_good["symbol"]])


if __name__ == '__main__':
    all_systems = get_systems_from_access()
    populate_waypoints(all_systems)

