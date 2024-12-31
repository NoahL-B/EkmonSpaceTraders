from api_requests.make_requests import RequestHandler

RH = RequestHandler(printouts=True)


### OVERALL REQUESTS ###

def get_status(token: str | None, priority: str = "NORMAL"):
    response = RH.get("", token=token, priority=priority).json()
    return response


def register_new_agent(faction: str, agent_name: str, email: str = None, priority: str = "NORMAL"):
    payload = {
        "faction": faction,
        "symbol": agent_name
    }
    if email:
        payload["email"] = email
    response = RH.post("register", payload, priority=priority).json()
    return response


### AGENT REQUESTS ###

def get_agent(token: str, priority: str = "NORMAL"):
    response = RH.get("my/agent", token=token, priority=priority).json()
    return response


def list_agents(token: str | None, limit: int = 20, page: int = 1, priority: str = "NORMAL"):
    payload = {
        "page": page,
        "limit": limit
    }
    response = RH.get("agents", payload, token=token, priority=priority).json()
    return response


def get_public_agent(token: str | None, agentSymbol: str, priority: str = "NORMAL"):
    response = RH.get("agents/" + agentSymbol, token=token, priority=priority).json()
    return response


### CONTRACT REQUESTS ###

def list_contracts(token: str, limit: int = 20, page: int = 1, priority: str = "NORMAL"):
    payload = {
        "page": page,
        "limit": limit
    }
    response = RH.get("my/contracts", payload, token=token, priority=priority).json()
    return response


def get_contract(token: str, contractId: str, priority: str = "NORMAL"):
    response = RH.get("my/contracts/" + contractId, token=token, priority=priority).json()
    return response


def accept_contract(token: str, contractId: str, priority: str = "NORMAL"):
    response = RH.post("my/contracts/" + contractId + "/accept", token=token, priority=priority).json()
    return response


def deliver_cargo_to_contract(token: str, contractId: str, shipSymbol: str, tradeSymbol: str, units: int, priority: str = "NORMAL"):
    payload = {
        "shipSymbol": shipSymbol,
        "tradeSymbol": tradeSymbol,
        "units": units
    }
    response = RH.post("my/contracts/" + contractId, payload, token=token, priority=priority).json()
    return response


def fulfill_contract(token: str, contractId: str, priority: str = "NORMAL"):
    response = RH.post("my/contracts/" + contractId + "/fulfill", token=token, priority=priority).json()
    return response


### FACTION REQUESTS ###

def list_factions(token: str | None, limit: int = 20, page: int = 1, priority: str = "NORMAL"):
    payload = {
        "page": page,
        "limit": limit
    }
    response = RH.get("factions", payload, token=token, priority=priority).json()
    return response


def get_faction(token: str, factionSymbol: str, priority: str = "NORMAL"):
    response = RH.get("factions/" + factionSymbol, token=token, priority=priority).json()
    return response


### FLEET REQUESTS ####

def list_ships(token: str, limit: int = 20, page: int = 1, priority: str = "NORMAL"):
    payload = {
        "page": page,
        "limit": limit
    }
    response = RH.get("my/ships", payload, token=token, priority=priority).json()
    return response


def purchase_ship(token: str, shipType: str, waypointSymbol: str, priority: str = "NORMAL"):
    payload = {
        "shipType": shipType,
        "waypointSymbol": waypointSymbol
    }
    response = RH.post("my/ships", payload, token=token, priority=priority).json()
    return response


def get_ship(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.get("my/ships/" + shipSymbol, token=token, priority=priority).json()
    return response


def get_ship_cargo(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.get("my/ships/" + shipSymbol + "/cargo", token=token, priority=priority).json()
    return response


def orbit_ship(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/orbit", token=token, priority=priority).json()
    return response


def ship_refine(token: str, shipSymbol: str, produce: str, priority: str = "NORMAL"):
    payload = {
        "produce": produce
    }
    response = RH.post("my/ships/" + shipSymbol + "/orbit", payload, token=token, priority=priority).json()
    return response


def create_chart(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/chart", token=token, priority=priority).json()
    return response


def get_ship_cooldown(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.get("my/ships/" + shipSymbol + "/cooldown", token=token, priority=priority)
    if response.status_code == 204:
        return False
    else:
        return response.json()


def dock_ship(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/dock", token=token, priority=priority).json()
    return response


def create_survey(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/survey", token=token, priority=priority).json()
    return response


def extract_resources(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/extract", token=token, priority=priority).json()
    return response


def siphon_resources(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/siphon", token=token, priority=priority).json()
    return response


def extract_resources_with_survey(token: str, shipSymbol: str, survey: dict, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/extract/survey", survey, token=token, priority=priority).json()
    return response


def jettison_cargo(token: str, shipSymbol: str, symbol: str, units: int, priority: str = "NORMAL"):
    payload = {
        "symbol": symbol,
        "units": units
    }
    response = RH.post("my/ships/" + shipSymbol + "/jettison", payload, token=token, priority=priority).json()
    return response


def jump_ship(token: str, shipSymbol: str, waypointSymbol: str, priority: str = "NORMAL"):
    payload = {
        "waypointSymbol": waypointSymbol
    }
    response = RH.post("my/ships/" + shipSymbol + "/jump", payload, token=token, priority=priority).json()
    return response


def navigate_ship(token: str, shipSymbol: str, waypointSymbol: str, priority: str = "NORMAL"):
    payload = {
        "waypointSymbol": waypointSymbol
    }
    response = RH.post("my/ships/" + shipSymbol + "/navigate", payload, token=token, priority=priority).json()
    return response


def patch_ship_nav(token: str, shipSymbol: str, flightMode: str, priority: str = "NORMAL"):
    payload = {
        "flightMode": flightMode
    }
    response = RH.patch("my/ships/" + shipSymbol + "/nav", payload, token=token, priority=priority).json()
    return response


def get_ship_nav(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.get("my/ships/" + shipSymbol + "/nav", token=token, priority=priority).json()
    return response


def warp_ship(token: str, shipSymbol: str, waypointSymbol: str, priority: str = "NORMAL"):
    payload = {
        "waypointSymbol": waypointSymbol
    }
    response = RH.post("my/ships/" + shipSymbol + "/warp", payload, token=token, priority=priority).json()
    return response


def sell_cargo(token: str, shipSymbol: str, symbol: str, units: int, priority: str = "NORMAL"):
    payload = {
        "symbol": symbol,
        "units": units
    }
    response = RH.post("my/ships/" + shipSymbol + "/sell", payload, token=token, priority=priority).json()
    return response


def scan_systems(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/scan/systems", token=token, priority=priority).json()
    return response


def scan_waypoints(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/scan/waypoints", token=token, priority=priority).json()
    return response


def scan_ships(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/scan/ships", token=token, priority=priority).json()
    return response


def refuel_ship(token: str, shipSymbol: str, units: int = 0, fromCargo: bool = False,  priority: str = "NORMAL"):
    payload = {}
    if units:
        payload['units'] = units
    if fromCargo:
        payload["fromCargo"] = fromCargo
    response = RH.post("my/ships/" + shipSymbol + "/refuel", payload, token=token, priority=priority).json()
    return response


def purchase_cargo(token: str, shipSymbol: str, symbol: str, units: int, priority: str = "NORMAL"):
    payload = {
        "symbol": symbol,
        "units": units
    }
    response = RH.post("my/ships/" + shipSymbol + "/purchase", payload, token=token, priority=priority).json()
    return response


def transfer_cargo(token: str, fromShipSymbol: str, toShipSymbol: str, tradeSymbol: str, units: int, priority: str = "NORMAL"):
    payload = {
        "tradeSymbol": tradeSymbol,
        "units": units,
        "shipSymbol": toShipSymbol
    }
    response = RH.post("my/ships/" + fromShipSymbol + "/transfer", payload, token=token, priority=priority).json()
    return response


def negotiate_contract(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/negotiate/contract", token=token, priority=priority).json()
    return response


def get_mounts(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.get("my/ships/" + shipSymbol + "/mounts", token=token, priority=priority).json()
    return response


def install_mount(token: str, shipSymbol: str, symbol: str, priority: str = "NORMAL"):
    payload = {
        "symbol": symbol
    }
    response = RH.get("my/ships/" + shipSymbol + "/mounts/install", payload, token=token, priority=priority).json()
    return response


def remove_mount(token: str, shipSymbol: str, symbol: str, priority: str = "NORMAL"):
    payload = {
        "symbol": symbol
    }
    response = RH.get("my/ships/" + shipSymbol + "/mounts/remove", payload, token=token, priority=priority).json()
    return response


def get_scrap_ship(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.get("my/ships/" + shipSymbol + "/scrap", token=token, priority=priority).json()
    return response


def scrap_ship(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/scrap", token=token, priority=priority).json()
    return response


def get_repair_ship(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.get("my/ships/" + shipSymbol + "/repair", token=token, priority=priority).json()
    return response


def repair_ship(token: str, shipSymbol: str, priority: str = "NORMAL"):
    response = RH.post("my/ships/" + shipSymbol + "/repair", token=token, priority=priority).json()
    return response


### SYSTEM REQUESTS ###

def list_systems(token: str | None, limit: int = 20, page: int = 1, priority: str = "NORMAL"):
    payload = {
        "page": page,
        "limit": limit
    }
    response = RH.get("systems", payload, token=token, priority=priority).json()
    return response


def get_system(token: str | None, systemSymbol: str, priority: str = "NORMAL"):
    response = RH.get("systems/" + systemSymbol, token=token, priority=priority).json()
    return response


def list_waypoints_in_system(token: str | None, systemSymbol: str, traits: str | list[str] = None, waypointType: str = None, limit: int = 20, page: int = 1, priority: str = "NORMAL"):
    payload = {
        "page": page,
        "limit": limit
    }
    if traits:
        payload['traits'] = traits
    if waypointType:
        payload["type"] = waypointType
    response = RH.get("systems/" + systemSymbol + "/waypoints", payload, token=token, priority=priority).json()
    return response


def get_waypoint(token: str | None, systemSymbol: str, waypointSymbol: str, priority: str = "NORMAL"):
    response = RH.get("systems/" + systemSymbol + "/waypoints/" + waypointSymbol, token=token, priority=priority).json()
    return response


def get_market(token: str | None, systemSymbol: str, waypointSymbol: str, priority: str = "NORMAL"):
    response = RH.get("systems/" + systemSymbol + "/waypoints/" + waypointSymbol + "/market", token=token, priority=priority).json()
    return response


def get_shipyard(token: str | None, systemSymbol: str, waypointSymbol: str, priority: str = "NORMAL"):
    response = RH.get("systems/" + systemSymbol + "/waypoints/" + waypointSymbol + "/shipyard", token=token, priority=priority).json()
    return response


def get_jump_gate(token: str | None, systemSymbol: str, waypointSymbol: str, priority: str = "NORMAL"):
    response = RH.get("systems/" + systemSymbol + "/waypoints/" + waypointSymbol + "/jump-gate", token=token, priority=priority).json()
    return response


def get_construction_site(token: str | None, systemSymbol: str, waypointSymbol: str, priority: str = "NORMAL"):
    response = RH.get("systems/" + systemSymbol + "/waypoints/" + waypointSymbol + "/construction", token=token, priority=priority).json()
    return response


def supply_construction_site(token: str, systemSymbol: str, waypointSymbol: str, shipSymbol: str, tradeSymbol: str, units: int, priority: str = "NORMAL"):
    payload = {
        "shipSymbol": shipSymbol,
        "tradeSymbol": tradeSymbol,
        "units": units
    }
    response = RH.post("systems/" + systemSymbol + "/waypoints/" + waypointSymbol + "/construction/supply", payload, token=token, priority=priority).json()
    return response


if __name__ == '__main__':
    print(list_systems(None))