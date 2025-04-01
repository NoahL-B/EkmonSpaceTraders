import time

import Reset_Procedure
import SECRETS
import __SHARED as SHARED



def verify_reset_status():
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
    new_token = Reset_Procedure.main()["data"]["token"]
    SECRETS.TOKEN = new_token
    import Startup_Procedure
    Startup_Procedure.fill_table_defaults()
    SHARED.stop_threads_and_wait()
    import main
    main.init_globals()



if __name__ == '__main__':
    try:
        wait_for_end_of_server_maintenance()
        import main
        import Startup_Procedure

        while True:
            try:
                main.main()
            except SHARED.ServerMaintenanceException:
                SHARED.stop_flag.set()
                wait_for_end_of_server_maintenance()
                SHARED.stop_threads_and_wait()
    except KeyboardInterrupt as k:
        print("HALTING ALL THREADS")
        SHARED.stop_threads_and_wait()
        SHARED.conn.close()
        raise k
