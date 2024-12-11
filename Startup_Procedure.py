# RUN RESET PROCEDURE BEFORE THE STARTUP PROCEDURE!!!

from SECRETS import *
from main import *
import hauling


def fill_table_defaults():
    command_ship_name = UNAME + "-1"
    satellite_ship_name = UNAME + "-2"

    dbFunctions.access_add_ship_assignment(command_ship_name, True, "COMMAND_PHASE_A", SYSTEM)
    dbFunctions.access_add_ship_assignment(satellite_ship_name, True, "MARKET_SCOUT", SYSTEM)

    # all_systems = dbFunctions.get_all_systems()
    all_systems = dbFunctions.get_systems_dot_json()
    dbFunctions.populate_systems(all_systems)

    for s in all_systems:
        if s['symbol'] == SYSTEM:
            dbFunctions.populate_waypoints([s])
            dbFunctions.populate_markets()

    otherFunctions.patchShipNav(command_ship_name, "BURN")

    x = threading.Thread(target=scout_markets(command_ship_name, False))
    x.start()

    y = threading.Thread(target=dbFunctions.populate_waypoints, args=(all_systems,))
    y.start()

    x.join()
    x = threading.Thread(target=hauling.choose_trade_run_loop, args=(SYSTEM, command_ship_name, ("FUEL", "FAB_MATS", "ADVANCED_CIRCUITRY")), daemon=True)
    x.start()

    y.join()
    y = threading.Thread(target=dbFunctions.populate_markets)
    y.start()
    y.join()




if __name__ == '__main__':
    fill_table_defaults()