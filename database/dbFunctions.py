import datetime
import math
import time

from database import Waypoint
from database.System import *
from otherFunctions import *
from SHARED import *
from threading import Lock


DB_LOCK = Lock()



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

    cmd += ", isUnderConstruction"

    for t in wp.traits:
        trait_symbol = t["symbol"]
        cmd += ", " + trait_symbol

    cmd += ') VALUES '
    cmd += "('" + wp.symbol + "', '" + wp.type + "', '" + wp.systemSymbol + "', '" + str(wp.x) + "', '" + str(wp.y) + "'"

    if wp.faction is not None:
        cmd += ", '" + wp.faction["symbol"] + "'"

    cmd += ", " + str(wp.isUnderConstruction)

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

    if wp.isUnderConstruction:
        cmd += ", Waypoint.isUnderConstruction=True"
    else:
        cmd += ", Waypoint.isUnderConstruction=False"

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

    if x1 == x2 and y1 == y2:
        return 1

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

    if num_systems % systems_per_page != 0:
        num_pages += 1

    for page in range(1, num_pages + 1):
        l = listSystems(systems_per_page, page)
        for i in range(len(l['data'])):
            all_systems.append(l["data"][i])
            print(l["data"][i]["symbol"])
        print("Page", page, "of", num_pages)

    return all_systems


def get_systems_dot_json():
    endpoint = "v2/systems.json"
    params = None
    return myClient.generic_api_call("GET", endpoint, params, TOKEN)


def get_all_waypoints_in_system(systemSymbol):
    system_waypoints = []

    waypoints_per_page = 20

    num_waypoints = listWaypointsInSystem(systemSymbol, waypoints_per_page)["meta"]["total"]
    num_pages = num_waypoints // waypoints_per_page

    if num_waypoints % waypoints_per_page != 0:
        num_pages += 1

    for page in range(1, num_pages + 1):
        l = listWaypointsInSystem(systemSymbol, waypoints_per_page, page)
        for i in range(len(l['data'])):
            system_waypoints.append(l["data"][i])

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


def populate_markets():
    all_waypoints = get_waypoints_from_access()
    for wp in all_waypoints:
        for trait in wp["traits"]:
            if trait["symbol"] == "MARKETPLACE":
                getMarket(wp["systemSymbol"], wp["symbol"])


def populate_waypoints(all_systems):
    access_waypoints = get_waypoints_from_access()
    access_waypoint_symbols = []
    for awp in access_waypoints:
        access_waypoint_symbols.append(awp["symbol"])

    counter = 0

    for wp in get_all_waypoints_generator(all_systems):
        wp_obj = Waypoint.Waypoint(wp)
        populate_waypoint(wp_obj, access_waypoint_symbols)
        counter += 1
        print("\r", counter, wp["symbol"], end="")


def populate_waypoint(wp_object, access_waypoint_symbols=None):
    if access_waypoint_symbols is None:
        access_waypoints = get_waypoints_from_access()
        access_waypoint_symbols = []
        for awp in access_waypoints:
            access_waypoint_symbols.append(awp["symbol"])
    needs_update = False
    if wp_object.symbol in access_waypoint_symbols:
        needs_update = True
    cmd = waypoint_to_sql(wp_object, needs_update)
    if cmd:
        DB_LOCK.acquire()
        try:
            cursor.execute(cmd)
        finally:
            DB_LOCK.release()

    if wp_object.chart is not None:
        record_chart(wp_object)


def populate_systems(all_systems):
    access_systems = get_systems_from_access()
    access_system_symbols = []
    for asp in access_systems:
        access_system_symbols.append(asp["symbol"])

    for s in all_systems:
        if s["symbol"] not in access_system_symbols:
            cmd = sector_to_sql(s)
            DB_LOCK.acquire()
            try:
                cursor.execute(cmd)
            finally:
                DB_LOCK.release()


def record_chart(wp):
    chart = wp.chart
    symbol = wp.symbol
    cmd = "SELECT * FROM Charts WHERE (Charts.waypointSymbol='" + symbol + "');"
    DB_LOCK.acquire()

    try:
        cursor.execute(cmd)
        needs_recording = False
        if cursor.fetchone() is None:
            needs_recording = True
    finally:
        DB_LOCK.release()
    all_factions = ["COSMIC", "VOID", "GALACTIC", "QUANTUM", "DOMINION", "ASTRO", "CORSAIRS", "OBSIDIAN", "AEGIS",
                    "UNITED", "SOLITARY", "COBALT", "OMEGA", "ECHO", "LORDS", "CULT", "ANCIENTS", "SHADOW", "ETHEREAL"]
    if needs_recording:
        ship = chart["submittedBy"]
        if ship in all_factions:
            agent = ship
        else:
            sub_agent = ship.split("-")
            agent = sub_agent.pop(0)
            for x in sub_agent[0:-1]:
                agent += "-" + x
        access_insert_entry("Charts", ["waypointSymbol", "submittedBy", "submittedByAgent"], [symbol, ship, agent])
        submission_time = datetime.datetime.strptime(chart["submittedOn"], '%Y-%m-%dT%H:%M:%S.%fZ')
        access_update_entry("Charts", ["submittedOn"], [submission_time], ["waypointSymbol"], [symbol])


def get_systems_from_access():
    raw_systems = []

    DB_LOCK.acquire()
    try:
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

    finally:
        DB_LOCK.release()

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


def get_waypoints_from_access(system=None):
    waypoints = []

    DB_LOCK.acquire()
    try:
        cursor.execute("SELECT * FROM (Waypoint LEFT JOIN Charts ON (Waypoint.symbol = Charts.WaypointSymbol))")

        for raw_wp in cursor:
            if system is None or raw_wp[2] == system:
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

                for trait_num in range(7, 76):
                    if raw_wp[trait_num]:
                        trait_name = raw_wp.cursor_description[trait_num][0]
                        traits.append({"symbol": trait_name})

                if raw_wp[76] is not None:
                    chart = {
                        "waypointSymbol": raw_wp[76],
                        "submittedBy": raw_wp[77],
                        "submittedOn": raw_wp[78],
                        "submittedByAgent": raw_wp[79]
                    }
                    dict_wp["chart"] = chart

                waypoints.append(dict_wp)
    finally:
        DB_LOCK.release()
    return waypoints


def get_markets_from_access():
    marketplaces = {}
    DB_LOCK.acquire()

    try:
        cursor.execute("SELECT * FROM Markets")
        for marketplace_entry in cursor:
            waypoint_symbol = marketplace_entry[1]
            if waypoint_symbol not in marketplaces.keys():
                marketplaces[waypoint_symbol] = {
                    "symbol": waypoint_symbol,
                    "tradeGoods": []
                }
            trade_good = {
                "symbol": marketplace_entry[2],
                "tradeVolume": 1,
                "supply": "NOT SET",
                "purchasePrice": 99999,
                "sellPrice": 0,
                "type": "NOT SET"
            }
            if marketplace_entry[3] > 0:
                trade_good["tradeVolume"] = marketplace_entry[3]
                trade_good["supply"] = marketplace_entry[4]
                trade_good["purchasePrice"] = marketplace_entry[5]
                trade_good["sellPrice"] = marketplace_entry[6]
                trade_good["type"] = marketplace_entry[8]
            marketplaces[waypoint_symbol]["tradeGoods"].append(trade_good)
    finally:
        DB_LOCK.release()

    markets_list = []
    for marketplace in marketplaces.values():
        markets_list.append(marketplace)
    return markets_list


def access_insert_entry(table_name, column_name_list, value_list):
    cmd = "INSERT INTO " + table_name + "(" + column_name_list[0]
    for col_name in column_name_list[1:]:
        cmd += ", " + col_name
    cmd += ") VALUES ('" + str(value_list[0])
    for value in value_list[1:]:
        cmd += "', '" + str(value)
    cmd += "');"
    DB_LOCK.acquire()
    try:
        cursor.execute(cmd)
    finally:
        DB_LOCK.release()


def access_update_entry(table_name, update_column_name_list, update_value_list, where_column_name_list, where_value_list):
    cmd = "UPDATE " + table_name + " SET " + table_name + "." + update_column_name_list[0] + ' = ?'
    for i in range(1, len(update_column_name_list)):
        cmd += ", " + table_name + "." + update_column_name_list[i] + ' = ?'
    cmd += " WHERE (((" + table_name + "." + where_column_name_list[0] + ')=?)'
    for i in range(1, len(where_column_name_list)):
        cmd += " AND ((" + table_name + "." + where_column_name_list[i] + ')=?)'
    cmd += ");"
    params = tuple(update_value_list + where_value_list)
    DB_LOCK.acquire()
    try:
        cursor.execute(cmd, params)
    finally:
        DB_LOCK.release()




def access_get_market(waypoint):
    cmd = "SELECT * FROM Markets WHERE Waypoint=?"
    while not DB_LOCK.acquire(timeout=10):
        time.sleep(1)
    try:
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
                "timeStamp": m[7],
                "type": m[8]
            }
            market_vals.append(good_dict)
    finally:
        DB_LOCK.release()
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
                access_update_entry("Markets", ["TradeVolume", "Supply", "PurchasePrice", "SellPrice", "timestamp", "Type"], [trade_good["tradeVolume"], trade_good["supply"], trade_good["purchasePrice"], trade_good["sellPrice"], current_time, trade_good["type"]], ["Waypoint", "Symbol"], [waypoint, trade_good["symbol"]])
            else:
                access_insert_entry("Markets", ["Waypoint", "Symbol", "TradeVolume", "Supply", "PurchasePrice", "SellPrice", "Type"], [waypoint, trade_good["symbol"], trade_good["tradeVolume"], trade_good["supply"], trade_good["purchasePrice"], trade_good["sellPrice"], trade_good["type"]])
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

