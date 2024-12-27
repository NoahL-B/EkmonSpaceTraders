from datetime import datetime
import time

import api_requests.raw_api_requests as raw_api_requests
from api_requests.raw_api_requests import get_status, register_new_agent, get_agent, list_agents, get_public_agent, list_contracts, get_contract, accept_contract, deliver_cargo_to_contract, fulfill_contract, list_factions, get_faction, list_ships, purchase_ship, get_ship, get_ship_cargo, orbit_ship, ship_refine, create_chart, get_ship_cooldown, dock_ship, create_survey, extract_resources, siphon_resources, extract_resources_with_survey, jettison_cargo, jump_ship, navigate_ship, patch_ship_nav, get_ship_nav, warp_ship, scan_systems, scan_waypoints, scan_ships, refuel_ship,  transfer_cargo, negotiate_contract, get_mounts, install_mount, remove_mount, get_scrap_ship, scrap_ship, get_repair_ship, repair_ship, list_systems, get_system, list_waypoints_in_system, get_waypoint, get_shipyard, get_jump_gate, get_construction_site, supply_construction_site
from database.dbFunctions import access_record_market


def waypoint_name_to_system_name(waypoint_name: str):
    name_list = waypoint_name.split("-")
    system_name = name_list[0] + "-" + name_list[1]
    return system_name


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


def purchase_cargo(token: str, shipSymbol: str, symbol: str, units: int, priority: str = "NORMAL"):
    result = raw_api_requests.purchase_cargo(token, shipSymbol, symbol, units, priority)
    if 'data' in result.keys():
        waypoint = result['data']['transaction']['waypointSymbol']
        system = waypoint_name_to_system_name(waypoint)
        get_market(token, system, waypoint)
    return result


def sell_cargo(token: str, shipSymbol: str, symbol: str, units: int, priority: str = "NORMAL"):
    result = raw_api_requests.sell_cargo(token, shipSymbol, symbol, units, priority)
    if 'data' in result.keys():
        waypoint = result['data']['transaction']['waypointSymbol']
        system = waypoint_name_to_system_name(waypoint)
        get_market(token, system, waypoint)
    return result


def get_all_ships(token: str):
    page_num = 1
    page = list_ships(token, page=page_num)
    num_contracts = page["meta"]["total"]
    all_ships = page["data"]

    while num_contracts > len(all_ships):
        page_num += 1
        page = list_ships(token, page=page_num)
        all_ships.extend(page["data"])
    return all_ships


def extract(token: str, shipSymbol: str, survey: dict = None):
    if survey:
        return extract_resources_with_survey(token, shipSymbol, survey)
    else:
        return extract_resources(token, shipSymbol)


def nav_to_time_delay(nav):
    try:
        end = nav["data"]["nav"]["route"]["arrival"]
        start_dt = datetime.utcnow()
        end_dt = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S.%fZ')
        diff = end_dt - start_dt
        sec = diff.total_seconds()
        return sec
    except TypeError:
        return 60


def navigate(token, ship, location, nav_and_sleep=False):
    to_return = navigate_ship(token, ship, location)

    if not to_return:
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
        time.sleep(nav_to_time_delay(to_return))
    return to_return



def findShipyard(system, ship_type):
    from database.dbFunctions import get_waypoints_from_access

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
    shipName = purchasedShip["data"]["ship"]["symbol"]
    orbit_ship(token, shipName)
    patch_ship_nav(token, shipName, "BURN")
    print("Purchased new ship:", shipName)
    return shipName


def get_market(token, systemSymbol, waypointSymbol):
    market_obj = raw_api_requests.get_market(token, systemSymbol, waypointSymbol)
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


if __name__ == '__main__':
    raw_api_requests.list_agents(None)