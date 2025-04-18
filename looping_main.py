import time

import Reset_Procedure
import SECRETS
import __SHARED as SHARED



def verify_reset_status():
    if SHARED.stop_flag.is_set():
        SHARED.stop_threads_and_wait()
    agent = Reset_Procedure.rar.get_agent(SECRETS.TOKEN, "HIGH")
    if "error" in agent.keys():
        if agent["error"]["code"] == 503:
            raise SHARED.ServerMaintenanceException()
        if agent["error"]["code"] == 4104 or agent["error"]["code"] == 401:
            raise SHARED.WrongResetException()
        else:
            print(agent)
            raise Exception("UNKNOWN EXCEPTION")
    return


def wait_for_end_of_server_maintenance():
    while True:
        try:
            verify_reset_status()
            return
        except SHARED.ServerMaintenanceException:
            time.sleep(5)
        except SHARED.WrongResetException:
            handle_wrong_reset()
            return


def handle_wrong_reset():
    SHARED.stop_threads_and_wait()
    from api_requests.raw_api_requests import RH
    RH.flush_queue()  # Get rid of all outstanding requests from the previous reset using the previous token

    new_token = Reset_Procedure.main()["data"]["token"]
    SECRETS.TOKEN = new_token
    import Startup_Procedure
    import main
    main.TOKEN = new_token
    time.sleep(5)  # Sometimes the universe takes a few seconds after a reset to have all the proper data available

    RH.start_pacing()
    Startup_Procedure.fill_table_defaults()
    SHARED.stop_threads_and_wait()
    RH.start_pacing()


if __name__ == '__main__':
    try:
        wait_for_end_of_server_maintenance()
        import main
        import Startup_Procedure
        import database.dbFunctions as dbFunctions

        while True:
            try:
                ID_info = dbFunctions.access_select_star("ID", ["UNAME"], [SECRETS.UNAME])
                if not ID_info[0][2]:
                    Startup_Procedure.fill_table_defaults()

                main.main()
            except (SHARED.ServerMaintenanceException, SHARED.WrongResetException, SHARED.ThreadStoppedException):
                SHARED.stop_flag.set()
                wait_for_end_of_server_maintenance()
                SHARED.stop_threads_and_wait()

    except KeyboardInterrupt as k:
        print("HALTING ALL THREADS")
        SHARED.stop_threads_and_wait()
        SHARED.conn.close()
        raise k
