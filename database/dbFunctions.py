import datetime
import math
import random
import time

import pyodbc

from database import Waypoint
from database.System import *
from SHARED import *
from SECRETS import UNAME



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
    dist = round(dist)
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
            pass
            # print(len(wp_list), "/", counter)
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
            pass
            # print(len(wp_list), "/", counter)
    len(wp_list), "/", counter
    return wp_list


def search_marketplaces_for_item(waypoint_list, item, imports=True, exports=True, exchange=True):
    stocked_markets = []
    for wp in waypoint_list:
        wp_name = wp["symbol"]
        wp_system = wp["systemSymbol"]
        mark = api.get_market(TOKEN, wp_system, wp_name)
        if search_marketplace_for_item(mark, item, imports, exports, exchange):
            stocked_markets.append(wp)
    return stocked_markets


def search_marketplace_for_item(marketplace, item, imports=True, exports=True, exchange=True):
    if "data" in marketplace.keys():
        marketplace = marketplace["data"]

    goods = []
    if imports:
        goods.extend(marketplace["imports"])
    if exports:
        goods.extend(marketplace["exports"])
    if exchange:
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
    if type(system) is str:
        system = access_get_detailed_systems(system)[0]

    if len(system["waypoints"]) == 0:
        return True

    wp = system["waypoints"][0]

    if "traits" in wp.keys():
        traits = wp["traits"]
    else:
        wp_obj = Waypoint.getWaypoint(system["symbol"], wp["symbol"])
        traits = wp_obj.traits
    for t in traits:
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
    endpoint = "systems.json"
    return api.raw_api_requests.RH.get(endpoint).json()


def get_all_waypoints_in_system(systemSymbol, noToken=False):
    system_waypoints = []

    waypoints_per_page = 20

    first_page = listWaypointsInSystem(systemSymbol, waypoints_per_page, noToken=noToken)
    for i in range(len(first_page['data'])):
        system_waypoints.append(first_page["data"][i])

    num_waypoints = first_page["meta"]["total"]
    num_pages = num_waypoints // waypoints_per_page

    if num_waypoints % waypoints_per_page != 0:
        num_pages += 1

    for page in range(2, num_pages + 1):
        l = listWaypointsInSystem(systemSymbol, waypoints_per_page, page, noToken=noToken)
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


def get_all_waypoints_generator(all_systems, unknown_only=False, noToken=False):
    notable_systems = get_notable_systems(all_systems)

    if unknown_only:
        notable_systems = get_unknown_systems(notable_systems)



    for s in notable_systems:
        systemSymbol = s["symbol"]
        system_waypoints = get_all_waypoints_in_system(systemSymbol, noToken=noToken)
        for wp in system_waypoints:
            yield wp


def get_notable_systems(all_systems):
    # a notable system is a system that contains a non-zero number of waypoints
    notable_systems = []
    for s in all_systems:
        if len(s["waypoints"]) > 0:
            notable_systems.append(s)
    return notable_systems


def get_unknown_systems(all_systems):
    unknown_systems = []
    recorded_waypoint_count = {}
    recorded_waypoints = get_waypoints_from_access()
    for wp in recorded_waypoints:
        system = wp['systemSymbol']
        if system in recorded_waypoint_count.keys():
            recorded_waypoint_count[system] += 1
        else:
            recorded_waypoint_count[system] = 1

    for s in all_systems:
        num_waypoints = len(s['waypoints'])
        system_name = s['symbol']
        num_waypoints_recorded = 0
        if system_name in recorded_waypoint_count.keys():
            num_waypoints_recorded = recorded_waypoint_count[system_name]
        if num_waypoints != num_waypoints_recorded:
            unknown_systems.append(s)
    return unknown_systems


def too_many_tables_handler(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except pyodbc.OperationalError as e:
            time.sleep(random.randint(1, 100))
            result = func(*args, **kwargs)
            return result
    return wrapper




def populate_markets():
    all_waypoints = get_waypoints_from_access()
    for wp in all_waypoints:
        for trait in wp["traits"]:
            if trait["symbol"] == "MARKETPLACE":
                api.get_market(TOKEN, wp["systemSymbol"], wp["symbol"])


def populate_jump_gates():
    all_waypoints = get_waypoints_from_access()
    for wp in all_waypoints:
        if wp["type"] == "JUMP_GATE":
            uncharted = False
            for trait in wp["traits"]:
                if trait["symbol"] == "UNCHARTED":
                    uncharted = True
            if not uncharted:
                if access_get_jump_gate(wp["systemSymbol"]) is None:
                    api.get_jump_gate(TOKEN, wp["systemSymbol"], wp["symbol"])


def populate_shipyards():
    all_waypoints = get_waypoints_from_access()
    shipyard_waypoints = find_all_with_trait_2(all_waypoints, "SHIPYARD")

    access_shipyards = get_shipyards_from_access()
    shipyard_names = []
    for s in access_shipyards:
        if s["symbol"] not in shipyard_names:
            shipyard_names.append(s["symbol"])

    for wp in shipyard_waypoints:
        wp_name = wp["symbol"]
        wp_system = wp["systemSymbol"]
        if wp_name not in shipyard_names:
            api.get_shipyard(TOKEN, wp_system, wp_name)


def populate_waypoints(all_systems, noToken=False):
    access_waypoints = get_waypoints_from_access()
    access_waypoint_symbols = []
    for awp in access_waypoints:
        access_waypoint_symbols.append(awp["symbol"])

    counter = 0

    for wp in get_all_waypoints_generator(all_systems, True, noToken=noToken):
        wp_obj = Waypoint.Waypoint(wp)
        populate_waypoint(wp_obj, access_waypoint_symbols)
        counter += 1
        # print("\r", counter, wp["symbol"], end="")


@too_many_tables_handler
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
        with get_cursor() as cursor:
            cursor.execute(cmd)


    if wp_object.chart is not None:
        record_chart(wp_object)


@too_many_tables_handler
def populate_systems(all_systems):
    access_systems = get_systems_from_access()
    access_system_symbols = []
    for asp in access_systems:
        access_system_symbols.append(asp["symbol"])

    for s in all_systems:
        if s["symbol"] not in access_system_symbols:
            cmd = sector_to_sql(s)
            with get_cursor() as cursor:
                cursor.execute(cmd)


@too_many_tables_handler
def record_chart(wp):
    chart = wp.chart
    symbol = wp.symbol
    cmd = "SELECT * FROM Charts WHERE (Charts.waypointSymbol='" + symbol + "');"

    with get_cursor() as cursor:
        cursor.execute(cmd)
        needs_recording = False
        if cursor.fetchone() is None:
            needs_recording = True

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


@too_many_tables_handler
def get_systems_from_access():
    raw_systems = []

    with get_cursor() as cursor:
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


@too_many_tables_handler
def access_get_detailed_systems(system=None):
    raw_systems = []

    with get_cursor() as cursor:
        params = ()
        cmd = "SELECT * FROM System"
        if system:
            cmd += " WHERE symbol=?"
            params = (system,)
        cursor.execute(cmd, params)
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

    all_waypoints = get_waypoints_from_access(system=system)

    for full_wp in all_waypoints:
        faction = None
        if "faction" in full_wp.keys():
            faction = {"symbol": full_wp["faction"]}
        active_system = sys_dicts_by_name[full_wp["systemSymbol"]]
        active_system["waypoints"].append(full_wp)
        if faction is not None:
            if faction not in active_system["factions"]:
                active_system["factions"].append(faction)

    sys_list = []
    for sys in sys_dicts_by_name.values():
        sys_list.append(sys)
    return sys_list


@too_many_tables_handler
def get_shipyards_from_access():
    shipyards = {}

    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM Shipyards")
        for shipyard_entry in cursor:
            waypoint_symbol = shipyard_entry[1]
            if waypoint_symbol not in shipyards.keys():
                shipyards[waypoint_symbol] = {
                    "symbol": waypoint_symbol,
                    "shipTypes": []
                }
            shipyards[waypoint_symbol]["shipTypes"].append({"type": shipyard_entry[2]})

            if shipyard_entry[4]:
                if "ships" not in shipyards[waypoint_symbol].keys():
                    shipyards[waypoint_symbol]["ships"] = []

                ship = {
                    "type": shipyard_entry[1],
                    "name": shipyard_entry[2],
                    "supply": shipyard_entry[3],
                    "activity": shipyard_entry[4],
                    "purchasePrice": shipyard_entry[5],
                    "timeStamp": shipyard_entry[6]
                }
                shipyards[waypoint_symbol]["ships"].append(ship)

    shipyards_list = []
    for s in shipyards.values():
        shipyards_list.append(s)
    return shipyards_list


@too_many_tables_handler
def get_waypoints_from_access(system=None):
    waypoints = []

    params = ()

    cmd = "SELECT * FROM (Waypoint LEFT JOIN Charts ON (Waypoint.symbol = Charts.WaypointSymbol))"
    if system:
        cmd += 'WHERE ((Waypoint.systemSymbol)=?)'
        params = (system,)

    with get_cursor() as cursor:
        cursor.execute(cmd, params)

        for raw_wp in cursor:
            if system is None or raw_wp[2] == system:
                traits = []
                dict_wp = {
                    "symbol": raw_wp[0],
                    "type": raw_wp[1],
                    "systemSymbol": raw_wp[2],
                    "x": raw_wp[3],
                    "y": raw_wp[4],
                    "traits": traits,
                    "isUnderConstruction": raw_wp[6]
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

    return waypoints


@too_many_tables_handler
def get_ship_roles_from_access():
    ship_roles = []

    with get_cursor() as cursor:
        cursor.execute('SELECT * FROM ShipAssignments')

        for c in cursor:
            ship_role = {}
            ship_role['shipName'] = c[0]
            ship_role['hasAssignment'] = c[1]
            ship_role['assignmentType'] = c[2]
            ship_role['systemSymbol'] = c[3]
            ship_role['waypointSymbol'] = c[4]
            if UNAME + "-" in ship_role['shipName']:
                ship_roles.append(ship_role)

    return ship_roles


@too_many_tables_handler
def get_markets_from_access(system=None):
    marketplaces = {}

    cmd = "SELECT * FROM Markets"
    params = ()
    if system is not None:
        params = (system, )
        cmd = "SELECT Markets.* FROM Waypoint INNER JOIN Markets ON Waypoint.symbol = Markets.Waypoint WHERE (((Waypoint.systemSymbol)=?));"

    with get_cursor() as cursor:
        cursor.execute(cmd, params)
        for marketplace_entry in cursor:
            waypoint_symbol = marketplace_entry[1]
            this_system = api.waypoint_name_to_system_name(waypoint_symbol)
            if system is None or this_system == system:
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
                    trade_good["timeStamp"] = marketplace_entry[7]
                    trade_good["type"] = marketplace_entry[8]
                marketplaces[waypoint_symbol]["tradeGoods"].append(trade_good)

    markets_list = []
    for marketplace in marketplaces.values():
        markets_list.append(marketplace)
    return markets_list


def access_add_ship_assignment(shipName, hasAssignment=False, assignmentType="", assignmentSystem="", assignmentWaypoint=""):
    access_insert_entry('ShipAssignments',
                        ["shipName", "hasAssignment", "assignmentType", "assignmentSystem", "assignmentWaypoint"],
                        [shipName, hasAssignment, assignmentType, assignmentSystem, assignmentWaypoint])


def access_update_ship_assignment(shipName, hasAssignment=None, assignmentType=None, assignmentSystem=None, assignmentWaypoint=None):
    if hasAssignment is not None:
        access_update_entry('ShipAssignments', ["hasAssignment"], [hasAssignment], ["shipName"], [shipName])
    if assignmentType is not None:
        access_update_entry('ShipAssignments', ["assignmentType"], [assignmentType], ["shipName"], [shipName])
    if assignmentSystem is not None:
        access_update_entry('ShipAssignments', ["assignmentSystem"], [assignmentSystem], ["shipName"], [shipName])
    if assignmentWaypoint is not None:
        access_update_entry('ShipAssignments', ["assignmentWaypoint"], [assignmentWaypoint], ["shipName"], [shipName])


@too_many_tables_handler
def access_insert_entry(table_name, column_name_list, value_list):
    cmd = "INSERT INTO " + table_name + " (" + column_name_list[0]
    for col_name in column_name_list[1:]:
        cmd += ", " + col_name
    cmd += ") VALUES ("
    i = 0
    while i < len(value_list):
        if i > 0:
            cmd += "?, "
        i += 1
    cmd += "?)"

    with get_cursor() as cursor:
        cursor.execute(cmd, value_list)


@too_many_tables_handler
def access_update_entry(table_name, update_column_name_list, update_value_list, where_column_name_list, where_value_list):
    cmd = "UPDATE " + table_name + " SET " + table_name + "." + update_column_name_list[0] + ' = ?'
    for i in range(1, len(update_column_name_list)):
        cmd += ", " + table_name + "." + update_column_name_list[i] + ' = ?'
    cmd += " WHERE (((" + table_name + "." + where_column_name_list[0] + ')=?)'
    for i in range(1, len(where_column_name_list)):
        cmd += " AND ((" + table_name + "." + where_column_name_list[i] + ')=?)'
    cmd += ");"
    params = tuple(update_value_list + where_value_list)

    with get_cursor() as cursor:
        cursor.execute(cmd, params)


@too_many_tables_handler
def access_get_market(waypoint):
    cmd = "SELECT * FROM Markets WHERE Waypoint=?"

    with get_cursor() as cursor:
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

    return market_vals


def access_record_jump_gate(jump_gate_dict):
    origin_waypoint = jump_gate_dict["data"]["symbol"]
    origin_system = api.waypoint_name_to_system_name(origin_waypoint)

    access_connections = access_get_jump_gate(origin_waypoint)

    for connection_waypoint in jump_gate_dict["data"]["connections"]:
        connection_system = api.waypoint_name_to_system_name(connection_waypoint)
        if access_connections is None or connection_waypoint not in access_connections["connections"]:
            access_insert_entry("JumpGates", ["originWaypointSymbol", "originSystemSymbol", "connectedWaypointSymbol", "connectedSystemSymbol"], [origin_waypoint, origin_system, connection_waypoint, connection_system])


@too_many_tables_handler
def access_get_jump_gate(waypoint):
    cmd = "SELECT * FROM JumpGates WHERE originWaypointSymbol=?"

    jump_gate = {"symbol": waypoint, "connections": []}

    with get_cursor() as cursor:
        cursor.execute(cmd, (waypoint,))
        for connection in cursor:
            jump_gate["connections"].append(connection[2])


    if len(jump_gate["connections"]) > 0:
        return jump_gate
    else:
        return None


@too_many_tables_handler
def access_get_all_jump_gates():
    cmd = "SELECT * FROM JumpGates"

    jump_gates = {}

    with get_cursor() as cursor:
        cursor.execute(cmd)
        for connection in cursor:
            if connection[0] not in jump_gates.keys():
                jump_gates[connection[0]] = {"symbol": connection[0], "connections": [connection[2]]}
            else:
                jump_gates[connection[0]]["connections"].append(connection[2])


    jump_gate_list = []
    for j in jump_gates.values():
        jump_gate_list.append(j)

    return jump_gate_list


@too_many_tables_handler
def access_get_available_jumps():
    cmd = "SELECT * FROM JumpsAvailable"
    jumps = []

    with get_cursor() as cursor:
        cursor.execute(cmd)
        for row in cursor:
            jumps.append(row)

    return jumps


@too_many_tables_handler
def access_get_transactions(ship=None, system=None):
    if ship is not None:
        cmd = "SELECT * FROM Transactions WHERE Transactions.Ship=?"
        args = (ship,)
    elif system is not None:
        cmd = "SELECT * FROM Transactions WHERE Transactions.System=?"
        args = (system,)
    else:
        cmd = "SELECT * FROM Transactions"
        args = ()

    transaction_list = []
    with get_cursor() as cursor:
        cursor.execute(cmd, args)
        for row in cursor:
            transaction = {"ID": row[0], "Ship": row[1], "Waypoint": row[2], "System": row[3], "Credits": row[4],
                           "ShipPurchase": row[5], "Refuel": row[6], "Repair": row[7], "Transfer": row[8],
                           "toShip": row[9], "TradeGood": row[10], "Quantity": row[11], "transactionTime": row[12]}
            transaction_list.append(transaction)
    return transaction_list


def access_record_shipyard(shipyard_dict):
    current_time = datetime.datetime.now(datetime.timezone.utc)
    waypoint = shipyard_dict["data"]["symbol"]

    existing_shipyard = access_get_shipyard(waypoint)

    dict_ships = shipyard_dict["data"]["shipTypes"]

    for shipType in dict_ships:
        entry_present = False
        for ship in existing_shipyard["shipTypes"]:
            if ship["type"] == shipType["type"]:
                entry_present = True

        if not entry_present:
            access_insert_entry("Shipyards", ["Waypoint", "type"], [waypoint, shipType["type"]])

    if "ships" in shipyard_dict["data"].keys():
        for ship in shipyard_dict["data"]["ships"]:
            access_update_entry("Shipyards", ["shipName", "supply", "activity", "purchasePrice", "timestamp"], [ship["name"], ship["supply"], ship["activity"], ship["purchasePrice"], current_time], ["Waypoint", "type"], [waypoint, ship["type"]])


@too_many_tables_handler
def jump_connection_exists(origin, destination):
    def __jump_connection_exists(origin, destination):

        with get_cursor() as cursor:

            # origin waypoint, destination waypoint
            cmd = "SELECT * FROM JumpGates WHERE originWaypointSymbol=? AND connectedWaypointSymbol=?"
            cursor.execute(cmd, (origin, destination))
            row = cursor.fetchone()
            if row:
                return row

            # origin system, destination system
            cmd = "SELECT * FROM JumpGates WHERE originSystemSymbol=? AND connectedSystemSymbol=?"
            cursor.execute(cmd, (origin, destination))
            row = cursor.fetchone()
            if row:
                return row

            # origin waypoint, destination system
            cmd = "SELECT * FROM JumpGates WHERE originWaypointSymbol=? AND connectedSystemSymbol=?"
            cursor.execute(cmd, (origin, destination))
            row = cursor.fetchone()
            if row:
                return row

            # origin system, destination waypoint
            cmd = "SELECT * FROM JumpGates WHERE originWaypointSymbol=? AND connectedWaypointSymbol=?"
            cursor.execute(cmd, (origin, destination))
            row = cursor.fetchone()
            if row:
                return row

        return False

    row = __jump_connection_exists(origin, destination)
    if row:
        return (row[0], row[2])
    row = __jump_connection_exists(destination, origin)
    if row:
        return (row[2], row[0])

    return False


@too_many_tables_handler
def access_get_shipyard(waypoint):
    cmd = "SELECT * FROM Shipyards WHERE Waypoint=?"

    with get_cursor() as cursor:
        cursor.execute(cmd, (waypoint,))

        shipyard_dict = {"symbol": waypoint,
                         "shipTypes": []}

        ships = []
        for m in cursor:
            shipyard_dict["shipTypes"].append({"type": m[2]})
            ship_dict = {
                "waypoint": m[1],
                "type": m[2],
                "name": m[3],
                "supply": m[4],
                "activity": m[5],
                "purchasePrice": m[6],
                "timeStamp": m[7]
            }
            if m[6]:
                ships.append(ship_dict)

        if len(ships) > 0:
            shipyard_dict["ships"] = ships

    return shipyard_dict


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


@too_many_tables_handler
def access_replenishing_trades(system):
    cmd = "EXEC ReplenishingTrades @System = ?"
    possible_trades = []
    with get_cursor() as cursor:
        cursor.execute(cmd, system)

        for row in cursor:
            possible_trade = {
                "tradeSymbol": row[1],
                "originWaypoint": row[2],
                "originSupply": row[3],
                "originPrice": row[5],
                "destinationWaypoint": row[6],
                "destinationSupply": row[7],
                "destinationPrice": row[9],
                "profit": row[10]
            }
            possible_trades.append(possible_trade)
    return possible_trades


@too_many_tables_handler
def access_profitable_trades(system):
    cmd = "EXEC ProfitableTrades @System = ?"
    possible_trades = []
    with get_cursor() as cursor:
        cursor.execute(cmd, system)

        for row in cursor:
            possible_trade = {
                "tradeSymbol": row[1],
                "originWaypoint": row[2],
                "originSupply": row[3],
                "originPrice": row[5],
                "destinationWaypoint": row[6],
                "destinationSupply": row[7],
                "destinationPrice": row[9],
                "profit": row[10]
            }
            possible_trades.append(possible_trade)
    return possible_trades


@too_many_tables_handler
def access_system_profits(system):
    cmd = "SELECT * FROM SystemProfits WHERE System=?"
    with get_cursor() as cursor:
        cursor.execute(cmd, system)
        try:
            system_profits = cursor.fetchone()[1]
        except TypeError:
            system_profits = 0
    return system_profits


if __name__ == '__main__':
    all_systems = get_systems_from_access()
    populate_waypoints(all_systems)

