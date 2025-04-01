# RUN RESET PROCEDURE BEFORE THE STARTUP PROCEDURE!!!

from SECRETS import *
from main import *
import hauling


def fill_table_defaults():
    command_ship_name = UNAME + "-1"
    satellite_ship_name = UNAME + "-2"

    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM ShipAssignments")
        need_to_add = [command_ship_name, satellite_ship_name]
        for row in cursor:
            try:
                need_to_add.remove(row[0])
            except ValueError:
                pass
        if command_ship_name in need_to_add:
            dbFunctions.access_add_ship_assignment(command_ship_name, True, "COMMAND_PHASE_A", SYSTEM)
        if satellite_ship_name in need_to_add:
            dbFunctions.access_add_ship_assignment(satellite_ship_name, True, "MARKET_SCOUT", SYSTEM)

        cursor.execute("SELECT * FROM Transactions")
        if cursor.fetchone() is None:
            agent = api_functions.get_agent(TOKEN)
            starting_credits = agent["data"]["credits"]
            hq = agent["data"]["headquarters"]
            dbFunctions.access_insert_entry("Transactions", ["Ship", "Waypoint", "System", "Credits", "transactionTime"], [command_ship_name, hq, SYSTEM, starting_credits, datetime.now(timezone.utc)])


    # all_systems = dbFunctions.get_all_systems()
    all_systems = dbFunctions.get_systems_dot_json()
    dbFunctions.populate_systems(all_systems)

    for s in all_systems:
        if s['symbol'] == SYSTEM:
            dbFunctions.populate_waypoints([s])
            dbFunctions.populate_markets()

    api_functions.patch_ship_nav(TOKEN, command_ship_name, "BURN")

    x = threading.Thread(target=scout_markets, args=(command_ship_name, False))
    x.start()

    y = threading.Thread(target=dbFunctions.populate_waypoints, args=(all_systems,))
    y.start()

    x.join()
    x = threading.Thread(name=UNAME + " threaded main", target=main, daemon=True)
    x.start()

    y.join()
    y = threading.Thread(target=dbFunctions.populate_markets)
    y.start()
    y.join()

    y = threading.Thread(target=dbFunctions.populate_shipyards)
    y.start()
    y.join()

    y = threading.Thread(target=dbFunctions.populate_jump_gates)
    y.start()
    y.join()




if __name__ == '__main__':
    fill_table_defaults()