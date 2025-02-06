from datetime import datetime, timezone
import time

import api_requests.raw_api_requests as raw_api_requests
from api_requests.raw_api_requests import get_status, register_new_agent, get_agent, list_agents, get_public_agent, list_contracts, get_contract, accept_contract, deliver_cargo_to_contract, fulfill_contract, list_factions, get_faction, list_ships, purchase_ship, get_ship, get_ship_cargo, orbit_ship, ship_refine, create_chart, get_ship_cooldown, dock_ship, create_survey, extract_resources, siphon_resources, extract_resources_with_survey, jettison_cargo, jump_ship, navigate_ship, patch_ship_nav, get_ship_nav, warp_ship, scan_systems, scan_waypoints, scan_ships, negotiate_contract, get_mounts, install_mount, remove_mount, get_scrap_ship, get_repair_ship, list_systems, get_system, list_waypoints_in_system, get_waypoint, get_construction_site, supply_construction_site # noqa
from database.dbFunctions import access_record_market, access_record_shipyard, access_record_jump_gate, access_insert_entry


def reset_pacing():
    raw_api_requests.RH.start_pacing()


def waypoint_name_to_system_name(waypoint_name: str):
    name_list = waypoint_name.split("-")
    system_name = name_list[0] + "-" + name_list[1]
    return system_name


def get_jump_gate(token: str | None, systemSymbol: str, waypointSymbol: str, priority: str = "NORMAL"):
    jump_gate = raw_api_requests.get_jump_gate(token, systemSymbol, waypointSymbol, priority)
    if "data" in jump_gate.keys():
        access_record_jump_gate(jump_gate)
    return jump_gate


def get_shipyard(token: str | None, systemSymbol: str, waypointSymbol: str, priority: str = "NORMAL"):
    shipyard = raw_api_requests.get_shipyard(token, systemSymbol, waypointSymbol, priority)
    if "data" in shipyard.keys():
        access_record_shipyard(shipyard)
    return shipyard


def get_all_contracts(token: str):
    page_num = 1
    page = list_contracts(token, page=page_num)
    num_contracts = page["meta"]["total"]
    all_contracts = page["data"]

    while num_contracts > len(all_contracts):
        page_num += 1
        page = list_contracts(token, page=page_num)
        all_contracts.extend(page["data"])
    return all_contracts


def get_credits(token: str):
    a = get_agent(token)
    c = a['data']['credits']
    return c


def refuel_ship(token: str, shipSymbol: str, units: int = 0, fromCargo: bool = False,  priority: str = "NORMAL"):
    if fromCargo and units == 0:
        raise ValueError("Units must be specified when refueling from cargo")

    result = raw_api_requests.refuel_ship(token, shipSymbol, units, fromCargo, priority)

    if "data" in result.keys():
        waypoint = result["data"]["transaction"]["waypointSymbol"]
        system = waypoint_name_to_system_name(waypoint)
        credits = result["data"]["transaction"]["totalPrice"] * -1
        timeStamp = datetime.now(timezone.utc)

        if fromCargo:
            trade_units = units // 100 + (units % 100 > 0)
            trade_units *= -1
            access_insert_entry("Transactions", ["Ship", "Waypoint", "System", "Refuel", "TradeGood", "Quantity", "transactionTime"],
                                [shipSymbol, waypoint, system, True, "FUEL", trade_units, timeStamp])
        else:
            access_insert_entry("Transactions", ["Ship", "Waypoint", "System", "Credits", "Refuel", "transactionTime"],
                                [shipSymbol, waypoint, system, credits, True, timeStamp])
    return result




def purchase_cargo(token: str, shipSymbol: str, symbol: str, units: int, priority: str = "NORMAL"):
    result = raw_api_requests.purchase_cargo(token, shipSymbol, symbol, units, priority)
    if 'data' in result.keys():
        waypoint = result['data']['transaction']['waypointSymbol']
        system = waypoint_name_to_system_name(waypoint)
        credits = result["data"]["transaction"]["totalPrice"] * -1
        timeStamp = datetime.now(timezone.utc)
        access_insert_entry("Transactions", ["Ship", "Waypoint", "System", "Credits", "TradeGood", "Quantity", "transactionTime"],
                            [shipSymbol, waypoint, system, credits, symbol, units, timeStamp])

        get_market(token, system, waypoint)
    return result


def sell_cargo(token: str, shipSymbol: str, symbol: str, units: int, priority: str = "NORMAL"):
    result = raw_api_requests.sell_cargo(token, shipSymbol, symbol, units, priority)
    if 'data' in result.keys():
        waypoint = result['data']['transaction']['waypointSymbol']
        system = waypoint_name_to_system_name(waypoint)
        credits = result["data"]["transaction"]["totalPrice"]
        timeStamp = datetime.now(timezone.utc)
        access_insert_entry("Transactions", ["Ship", "Waypoint", "System", "Credits", "TradeGood", "Quantity", "transactionTime"],
                            [shipSymbol, waypoint, system, credits, symbol, units * -1, timeStamp])
        get_market(token, system, waypoint)
    return result


def transfer_cargo(token: str, fromShipSymbol: str, toShipSymbol: str, tradeSymbol: str, units: int, priority: str = "NORMAL"):
    result = raw_api_requests.transfer_cargo(token, fromShipSymbol, toShipSymbol, tradeSymbol, units, priority)
    if "data" in result.keys():
        timeStamp = datetime.now(timezone.utc)
        access_insert_entry("Transactions", ["Ship", "TradeGood", "Quantity", "Transfer", "ToShip", "transactionTime"],
                            [fromShipSymbol, tradeSymbol, units, True, toShipSymbol, timeStamp])
    return result


def get_all_ships(token: str):
    page_num = 1
    page = list_ships(token, page=page_num)
    num_ships = page["meta"]["total"]
    all_ships = page["data"]

    while num_ships > len(all_ships):
        page_num += 1
        page = list_ships(token, page=page_num)
        all_ships.extend(page["data"])
    return all_ships


def extract(token: str, shipSymbol: str, survey: dict = None):
    if survey:
        extraction = extract_resources_with_survey(token, shipSymbol, survey)
    else:
        extraction = extract_resources(token, shipSymbol)

    if "data" in extraction.keys():
        symbol = extraction["data"]["extraction"]["yield"]["symbol"]
        units = extraction["data"]["extraction"]["yield"]["units"]
        timeStamp = datetime.now(timezone.utc)
        if units > 0:
            access_insert_entry("Transactions", ["Ship", "TradeGood", "Quantity", "transactionTime"],
                                [shipSymbol, symbol, units, timeStamp])
    return extraction


def nav_to_time_delay(nav):
    try:
        end = nav["data"]["nav"]["route"]["arrival"]
        start_dt = datetime.utcnow()
        end_dt = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S.%fZ')
        diff = end_dt - start_dt
        sec = diff.total_seconds()
        return sec
    except (TypeError, KeyError) as e:
        if "error" in nav.keys() and nav["error"]["code"] == 4214:
            sec = nav["error"]["data"]["secondsToArrival"]
            return sec
        print("NAV ERROR:", nav)
        raise e


def cooldown_to_time_delay(cooldown):
    if not cooldown:  # Occurs when cooldown returns a 204 response instead of a 200 response
        return 0
    try:
        sec = cooldown["data"]["remainingSeconds"]
        return sec
    except TypeError or KeyError as e:
        print("COOLDOWN ERROR:", cooldown)
        raise e


def navigate(token, ship, location, nav_and_sleep=False):
    to_return = navigate_ship(token, ship, location)

    if "data" not in to_return.keys():
        ship_status = get_ship(token, ship)
        nav = ship_status['data']['nav']
        if nav['status'] == 'IN_TRANSIT':
            if nav['route']['destination']['symbol'] == location:
                if nav_and_sleep:
                    time.sleep(nav_to_time_delay(ship_status))
                return ship_status
            else:
                return to_return
        elif nav['status'] == 'DOCKED':
            orbit_ship(token, ship)
            return navigate(ship, location, nav_and_sleep)
        elif nav['status'] == 'IN_ORBIT':
            if nav['route']['destination']['symbol'] == location:
                return ship_status
            else:
                return to_return

    if nav_and_sleep:
        try:
            time.sleep(nav_to_time_delay(to_return))
        except ValueError:
            pass
    return to_return



def findShipyard(system, ship_type):
    from database.dbFunctions import get_waypoints_from_access, get_shipyards_from_access

    shipyards = get_shipyards_from_access()

    for shipyard in shipyards:
        if system in shipyard["symbol"]:
            for shipType in shipyard["shipTypes"]:
                if shipType["type"] == ship_type:
                    return shipyard["symbol"]

    print("Something messed up in the findShipyard routine. Trying something else...")

    waypoints = get_waypoints_from_access(system)
    for wp in waypoints:
        for t in wp['traits']:
            if t['symbol'] == "SHIPYARD":
                shipyard = get_shipyard(None, system, wp['symbol'])
                for s in shipyard['data']['shipTypes']:
                    if s['type'] == ship_type:
                        return wp['symbol']


def buyShip(token: str, shipyard: str, shipType: str):
    purchasedShip = purchase_ship(token, shipType, shipyard)
    if "data" in purchasedShip.keys():
        shipName = purchasedShip["data"]["ship"]["symbol"]
        orbit_ship(token, shipName)
        patch_ship_nav(token, shipName, "BURN")
        print("Purchased new ship:", shipName)

        waypoint = purchasedShip["data"]["ship"]["nav"]["waypointSymbol"]
        system = purchasedShip["data"]["ship"]["nav"]["systemSymbol"]
        credits = purchasedShip["data"]["transaction"]["price"] * -1
        timeStamp = datetime.now(timezone.utc)
        access_insert_entry("Transactions", ["Ship", "Waypoint", "System", "Credits", "ShipPurchase", "transactionTime"],
                            [shipName, waypoint, system, credits, True, timeStamp])
        return shipName
    else:
        return purchasedShip


def scrap_ship(token: str, shipSymbol: str, priority="NORMAL"):
    sold_ship = raw_api_requests.scrap_ship(token, shipSymbol, priority)
    if "data" in sold_ship.keys():
        waypoint = sold_ship["data"]["transaction"]["waypointSymbol"]
        system = waypoint_name_to_system_name(waypoint)
        credits = sold_ship["data"]["transaction"]["totalPrice"]
        timeStamp = datetime.now(timezone.utc)
        access_insert_entry("Transactions", ["Ship", "Waypoint", "System", "Credits", "ShipPurchase", "transactionTime"],
                            [shipSymbol, waypoint, system, credits, True, timeStamp])

    return sold_ship


def repair_ship(token: str, shipSymbol: str, priority="NORMAL"):
    ship_repair = raw_api_requests.repair_ship(token, shipSymbol, priority)
    if "data" in ship_repair.keys():
        waypoint = ship_repair["data"]["transaction"]["waypointSymbol"]
        system = waypoint_name_to_system_name(waypoint)
        credits = ship_repair["data"]["transaction"]["totalPrice"] * -1
        timeStamp = datetime.now(timezone.utc)
        access_insert_entry("Transactions", ["Ship", "Waypoint", "System", "Credits", "ShipPurchase", "transactionTime"],
                            [shipSymbol, waypoint, system, credits, True, timeStamp])
    return ship_repair



def get_market(token, systemSymbol, waypointSymbol, priority="NORMAL"):
    market_obj = raw_api_requests.get_market(token, systemSymbol, waypointSymbol, priority)
    if "data" in market_obj.keys():
        access_record_market(market_obj)
    return market_obj


def buyLightHauler(token, shipyard):
    return buyShip(token, shipyard, "SHIP_LIGHT_HAULER")


def buyRefiningFreighter(token, shipyard):
    return buyShip(token, shipyard, "SHIP_REFINING_FREIGHTER")


def buyMiningDrone(token, shipyard):
    return buyShip(token, shipyard, "SHIP_MINING_DRONE")


def buyExplorer(token, shipyard):
    return buyShip(token, shipyard, "SHIP_EXPLORER")


def buyOreHound(token, shipyard):
    return buyShip(token, shipyard, "SHIP_ORE_HOUND")


def buySurveyor(token, shipyard):
    return buyShip(token, shipyard, "SHIP_SURVEYOR")


def buyProbe(token, shipyard):
    return buyShip(token, shipyard, "SHIP_PROBE")


def buySiphonDrone(token, shipyard):
    return buyShip(token, shipyard, "SHIP_SIPHON_DRONE")


def queue_len():
    return raw_api_requests.RH.queue_len()


if __name__ == '__main__':
    raw_api_requests.list_agents(None)