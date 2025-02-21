from main import *
from api_requests import api_functions as api
import economy


def trade_cycle(ship, product, system, origin_waypoint, destination_waypoint, destination_type="MARKET",
                stop_on_unprofitable_origin=True, stop_on_unprofitable_destination=True):
    sell_off_existing_cargo(ship)

    print("Flying", ship, "from", origin_waypoint, "to", destination_waypoint, "transporting", product, "to a",
          destination_type)

    ship_stats = get_ship(ship)
    cargo = ship_stats['data']['cargo']
    capacity = cargo['capacity']

    while True:
        auto_nav(ship, origin_waypoint)
        dock(ship)

        origin_market = api.get_market(TOKEN, system, origin_waypoint)

        origin_target_good = None
        origin_trade_goods = origin_market['data']['tradeGoods']

        for good in origin_trade_goods:
            if good['symbol'] == product:
                origin_target_good = good

        if origin_target_good is None:
            print("Product not sold at origin")
            return

        if stop_on_unprofitable_origin:
            if type(stop_on_unprofitable_origin) is bool:
                if origin_target_good['type'] == 'IMPORT':
                    print("Unprofitable origin: product is an IMPORT")
                    return

                if origin_target_good['supply'] not in ['ABUNDANT', 'HIGH', 'MODERATE']:
                    print("Unprofitable origin: supply is too low")
                    return
            else:
                if origin_target_good['purchasePrice'] > stop_on_unprofitable_origin:
                    print("Unprofitable origin: product is too expensive")
                    return


        num_to_buy = capacity - cargo['units']
        trade_volume = origin_target_good['tradeVolume']
        p = None
        while num_to_buy >= trade_volume:
            p = purchase(ship, product, trade_volume)
            num_to_buy -= trade_volume
        if num_to_buy > 0:
            p = purchase(ship, product, num_to_buy)

        if p:
            cargo = p['data']['cargo']
        else:
            cargo = get_ship(ship)['data']['cargo']

        orbit(ship)


        num_to_offload = 0
        for item in cargo['inventory']:
            if item['symbol'] == product:
                num_to_offload = item['units']

        if num_to_offload == 0:
            print("No items to offload")
            return


        auto_nav(ship, destination_waypoint)
        dock(ship)
        refuel(ship)

        if destination_type == 'MARKET':

            destination_market = api.get_market(TOKEN, system, destination_waypoint)

            target_good = None
            trade_goods = destination_market['data']['tradeGoods']

            for good in trade_goods:
                if good['symbol'] == product:
                    target_good = good

            if target_good is None:
                print("Product not bought at destination")
                return


            trade_volume = target_good['tradeVolume']
            s = None
            while num_to_offload >= trade_volume:
                s = sell(ship, product, trade_volume)
                num_to_offload -= trade_volume
            if num_to_offload > 0:
                s = sell(ship, product, num_to_offload)

            if s:
                cargo = s['data']['cargo']
            else:
                cargo = get_ship(ship)['data']['cargo']

            if stop_on_unprofitable_destination:
                if target_good['type'] == 'EXPORT':
                    print("Unprofitable destination: product is an EXPORT")
                    return

                if target_good['supply'] not in ['MODERATE', 'LIMITED', 'SCARCE']:
                    print("Unprofitable destination: supply is too high")
                    return

        if destination_type == 'CONSTRUCTION':
            c = get_construction(system, destination_waypoint)
            target_good = None
            for item in c['data']['materials']:
                if item['tradeSymbol'] == product:
                    target_good = item
            if not target_good:
                print(product, "is not needed at", destination_waypoint, "construction site")
                return
            num_needed = target_good['required'] - target_good['fulfilled']

            num_to_offload = min(num_needed, num_to_offload)

            if num_to_offload > 0:
                s = supply_construction(ship, system, destination_waypoint, product, num_to_offload)
                cargo = s['data']['cargo']
                print(ship, s)
            else:
                print(product, "is not needed at", destination_waypoint, "construction site")
                return

        if destination_type == 'CONTRACT':
            contract_map = get_active_contracts(get_all_contracts(), True)[0]
            contract_target_good = None
            for term in contract_map['terms']['deliver']:
                if term['tradeSymbol'] == product:
                    contract_target_good = term

            if contract_target_good is None:
                print("Contract does not include correct product")
                return

            num_required = contract_target_good['unitsRequired'] - contract_target_good['unitsFulfilled']
            num_to_deliver = min(num_required, num_to_offload)
            if num_to_deliver == 0:
                print('Completed contract for this product')
                fulfill = api.fulfill_contract(TOKEN, contract_map['id'])
                if fulfill:
                    print('Completed entire contract')
                return

            d = deliver(ship, product, num_to_deliver, contract_map['id'])
            cargo = d['data']['cargo']

        orbit(ship)


def trade_run(ship, product, system, origin_waypoint, destination_waypoint, destination_type="MARKET", ship_stats=None):

    origin_target_good = None
    origin_trade_goods = dbFunctions.access_get_market(origin_waypoint)

    for good in origin_trade_goods:
        if good['symbol'] == product:
            origin_target_good = good
    if origin_target_good is None:
        print("Product not sold at origin")
        return ship_stats


    print("Flying", ship, "to", origin_waypoint, "to load up", product)

    if ship_stats is None:
        ship_stats = get_ship(ship)

    cargo = ship_stats['data']['cargo']
    capacity = cargo['capacity']

    ship_stats = auto_nav(ship, origin_waypoint, ship_stats)
    dock(ship)

    max_buy_price = False

    if destination_type == "MARKET":
        destination_target_good = None
        destination_trade_goods = dbFunctions.access_get_market(destination_waypoint)
        for good in destination_trade_goods:
            if good['symbol'] == product:
                destination_target_good = good
        if destination_target_good is None:
            print("Product not bought at destination")
            return ship_stats
        max_buy_price = (origin_target_good['purchasePrice'] + destination_target_good['sellPrice'])/2

    num_to_buy = capacity - cargo['units']
    trade_volume = origin_target_good['tradeVolume']
    p = None

    while num_to_buy >= trade_volume and (not max_buy_price or origin_target_good['purchasePrice'] < max_buy_price):
        p = purchase(ship, product, trade_volume)

        if not p or 'data' not in p.keys():
            a = api.get_agent(TOKEN)
            c = a['data']['credits'] - 5000
            num_can_buy = c // origin_target_good['purchasePrice']
            num_to_buy = min(num_can_buy, num_to_buy)
        else:
            num_to_buy -= trade_volume
            ship_stats["data"]["cargo"] = p["data"]["cargo"]

        origin_target_good = None
        origin_trade_goods = dbFunctions.access_get_market(origin_waypoint)

        for good in origin_trade_goods:
            if good['symbol'] == product:
                origin_target_good = good

    if num_to_buy > 0 and (not max_buy_price or origin_target_good['purchasePrice'] < max_buy_price):
        p = purchase(ship, product, num_to_buy)

    if not p or "data" not in p.keys():
        a = api.get_agent(TOKEN)
        c = a['data']['credits'] - 5000
        num_can_buy = c // origin_target_good['purchasePrice']
        num_to_buy = min(num_can_buy, num_to_buy)
        if num_to_buy > 0:
            p = purchase(ship, product, num_to_buy)

    if p and 'data' in p.keys():
        cargo = p['data']['cargo']
        ship_stats["data"]["cargo"] = cargo


    o = orbit(ship)
    ship_stats["data"]["nav"] = o["data"]["nav"]

    num_to_offload = 0
    for item in cargo['inventory']:
        if item['symbol'] == product:
            num_to_offload = item['units']

    if num_to_offload == 0:
        print("No items to offload")
        return ship_stats

    print("Flying", ship, "from", origin_waypoint, "to", destination_waypoint, "transporting", product, "to a",
          destination_type)

    ship_stats = auto_nav(ship, destination_waypoint, ship_stats)
    d = dock(ship)
    r = refuel(ship)
    ship_stats["data"]["fuel"] = r["data"]["fuel"]
    ship_stats["data"]["nav"] = d["data"]["nav"]

    if destination_type == 'MARKET':

        trade_volume = destination_target_good['tradeVolume']  # noqa
        s = None
        while num_to_offload >= trade_volume:
            s = sell(ship, product, trade_volume)
            num_to_offload -= trade_volume
        if num_to_offload > 0:
            s = sell(ship, product, num_to_offload)
        if s is not None:
            if "data" in s.keys():
                ship_stats["data"]["cargo"] = s["data"]["cargo"]
            else:
                ship_stats = get_ship(ship)

    if destination_type == 'CONSTRUCTION':
        c = get_construction(system, destination_waypoint)
        target_good = None
        for item in c['data']['materials']:
            if item['tradeSymbol'] == product:
                target_good = item
        if not target_good:
            print(product, "is not needed at", destination_waypoint, "construction site")
            return ship_stats
        num_needed = target_good['required'] - target_good['fulfilled']

        num_to_offload = min(num_needed, num_to_offload)

        if num_to_offload > 0:
            supply = supply_construction(ship, system, destination_waypoint, product, capacity)
            ship_stats["data"]["cargo"] = supply["data"]["cargo"]
        else:
            print(product, "is not needed at", destination_waypoint, "construction site")
            return ship_stats

    if destination_type == 'CONTRACT':
        contract_map = get_active_contracts(get_all_contracts(), True)[0]
        contract_target_good = None
        for term in contract_map['terms']['deliver']:
            if term['tradeSymbol'] == product:
                contract_target_good = term

        if contract_target_good is None:
            print("Contract does not include correct product")
            return ship_stats

        num_required = contract_target_good['unitsRequired'] - contract_target_good['unitsFulfilled']
        num_to_deliver = min(num_required, num_to_offload)
        if num_to_deliver == 0:
            print('Completed contract for this product')
            fulfill = api.fulfill_contract(TOKEN, contract_map['id'])
            if "data" in fulfill.keys():
                print('Completed entire contract')
            return ship_stats

        d = deliver(ship, product, num_to_deliver, contract_map['id'])
        if "data" in d.keys():
            ship_stats["data"]["cargo"] = d["data"]["cargo"]
        else:
            raise Exception("Unknown error occurred while trying to fulfill a contract")

    o = orbit(ship)
    ship_stats["data"]["nav"] = o["data"]["nav"]

    return ship_stats


def sell_off_existing_cargo(ship, ship_stats=None):
    if ship_stats is None:
        ship_stats = get_ship(ship)
    inventory = ship_stats['data']['cargo']['inventory']
    if len(inventory) == 0:
        return ship_stats
    system = ship_stats['data']['nav']['systemSymbol']
    all_markets = dbFunctions.get_markets_from_access()
    local_markets = []
    for marketplace in all_markets:
        if system in marketplace['symbol']:
            local_markets.append(marketplace)

    highest_sell_prices = {}
    for marketplace in local_markets:
        for item in marketplace['tradeGoods']:
            if item['symbol'] not in highest_sell_prices.keys():
                highest_sell_prices[item['symbol']] = (marketplace['symbol'], item['sellPrice'], item['tradeVolume'])
            else:
                if item['sellPrice'] > highest_sell_prices[item['symbol']][1]:
                    highest_sell_prices[item['symbol']] = (marketplace['symbol'], item['sellPrice'], item['tradeVolume'])

    sale_locations = {}

    for item in inventory:
        sell_location = highest_sell_prices[item['symbol']][0]
        if sell_location in sale_locations.keys():
            sale_locations[sell_location].append(item)
        else:
            sale_locations[sell_location] = [item]

    for location in sale_locations.keys():
        print("Flying", ship, "from", ship_stats['data']['nav']['waypointSymbol'], 'to', location, 'transporting', len(sale_locations[location]), 'item(s) to a MARKET')
        ship_stats = auto_nav(ship, location, ship_stats)
        dock(ship)
        for item in sale_locations[location]:
            num_to_offload = item['units']
            trade_volume = highest_sell_prices[item['symbol']][2]
            sale = None
            while num_to_offload >= trade_volume:
                sale = sell(ship, item['symbol'], trade_volume)
                num_to_offload -= trade_volume
            if num_to_offload > 0:
                sale = sell(ship, item['symbol'], num_to_offload)
            if sale is not None:
                ship_stats["data"]["cargo"] = sale["data"]["cargo"]

        orbit(ship)

    return ship_stats


def choose_trade_loop(system, ship, ignored_goods=None):

    if ignored_goods is None:
        ignored_goods = ()

    profitable_trades = dbFunctions.access_profitable_trades(system)


    i = 0
    while i < len(profitable_trades):
        if profitable_trades[i]["tradeSymbol"] in ignored_goods:
            profitable_trades.pop(i)
        else:
            i += 1

    if len(profitable_trades) == 0:
        print(ship, "has no available profitable trades in", system)
        return

    weights = []
    for p in profitable_trades:
        weight = p["profit"]
        weights.append(weight)

    selected_trade = random.choices(profitable_trades, weights)[0]

    trade_cycle(ship, selected_trade["tradeSymbol"], system, selected_trade["originWaypoint"], selected_trade["destinationWaypoint"])
    return


def choose_trade_run_loop(system, ship, ignored_goods=None, loop=True, ship_data=None):
    initial_profitable_trades = dbFunctions.access_profitable_trades(system)
    if len(initial_profitable_trades) == 0:
        print(ship, "has no available profitable trades in", system)
        return ship_data

    ship_data = sell_off_existing_cargo(ship, ship_stats=ship_data)
    if ignored_goods is None:
        ignored_goods = ()
    do_once = True

    while loop or do_once:
        do_once = False
        profitable_trades = dbFunctions.access_profitable_trades(system)

        i = 0
        while i < len(profitable_trades):
            if profitable_trades[i]["tradeSymbol"] in ignored_goods:
                profitable_trades.pop(i)
            else:
                i += 1

        if len(profitable_trades) == 0:
            print(ship, "has no available profitable trades in", system)
            return ship_data

        local_trades = []
        for p in profitable_trades:
            if p["originWaypoint"] == ship_data["data"]["nav"]["waypointSymbol"]:
                local_trades.append(p)
        if len(local_trades) > 0:
            profitable_trades = local_trades

        weights = []
        for p in profitable_trades:
            weight = p["profit"]
            weights.append(weight)

        selected_trade = random.choices(profitable_trades, weights)[0]

        ship_data = trade_run(ship, selected_trade["tradeSymbol"], system, selected_trade["originWaypoint"], selected_trade["destinationWaypoint"], ship_stats=ship_data)

    return ship_data


def stimulate_economy(system, ship, good):
    predecessors = economy.get_immediate_predecessors([good])
    traded_goods = False
    if len(predecessors) == 0:
        return traded_goods
    waypoints = dbFunctions.get_waypoints_from_access(system)
    markets = dbFunctions.find_all_with_trait_2(waypoints, "MARKETPLACE")
    destinations = dbFunctions.search_marketplaces_for_item(markets, good, imports=False, exchange=False)
    for destination in destinations:
        market_stats = dbFunctions.access_get_market(destination['symbol'])

        for trade_good in market_stats:
            if trade_good['symbol'] in predecessors and trade_good['supply'] != "ABUNDANT":
                origins = dbFunctions.search_marketplaces_for_item(markets, trade_good['symbol'], imports=False, exchange=False)
                for origin in origins:
                    market_2_stats = dbFunctions.access_get_market(origin['symbol'])
                    for trade_good_2 in market_2_stats:
                        if trade_good_2['symbol'] == trade_good['symbol'] and trade_good_2['supply'] != "SCARCE":
                            trade_run(ship, trade_good['symbol'], system, origin['symbol'], destination['symbol'])
                            traded_goods = True
    return traded_goods


def replenish_economy(system, ship, ship_stats=None, loop=True, avoid_sourcing=None):
    do_once = True
    if avoid_sourcing is None:
        avoid_sourcing = []
    while loop or do_once:
        do_once = False

        replenishing_trades = dbFunctions.access_replenishing_trades(system)

        acceptable_replenishing_trades = []

        for trade in replenishing_trades:
            if trade["tradeSymbol"] not in avoid_sourcing:
                acceptable_replenishing_trades.append(trade)

        if not acceptable_replenishing_trades:
            print(ship, "has no available replenishing trades in", system)
            return ship_stats



        trade_to_replenish = random.choice(acceptable_replenishing_trades)
        ship_stats = trade_run(ship, trade_to_replenish["tradeSymbol"], system, trade_to_replenish["originWaypoint"], trade_to_replenish["destinationWaypoint"], ship_stats=ship_stats)

    return ship_stats