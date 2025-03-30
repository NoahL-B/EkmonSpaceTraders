import datetime as dt
import os
import shutil
import time

from __SHARED import get_cursor
from __SECRETS import UNAME
import api_requests.raw_api_requests as rar

cursor = get_cursor()

UTC_NOW = dt.datetime.now(dt.timezone.utc)
TARGET_UNAME = UNAME
STARTING_FACTION = "VOID"

# all_factions = ["COSMIC",   "VOID",     "GALACTIC", "QUANTUM",  "DOMINION",
#                "ASTRO",    "CORSAIRS", "OBSIDIAN", "AEGIS",    "UNITED",
#                "SOLITARY", "COBALT",   "OMEGA",    "ECHO",     "LORDS",
#                "CULT",     "ANCIENTS", "SHADOW",   "ETHEREAL"              ]


def get_weekly_folder():
    folder_name = str(UTC_NOW.month) + "-"
    folder_name += str(UTC_NOW.day) + "-"
    folder_name += str(UTC_NOW.year) + "--"
    folder_name += str(UTC_NOW.hour) + "-"
    folder_name += str(UTC_NOW.minute) + "-"
    folder_name += str(UTC_NOW.second)
    return folder_name


def get_base_folder():
    return os.path.abspath(os.getcwd())


def copy_old_data():
    base_path = get_base_folder()
    old_data_path = os.path.join(base_path, "old_data")
    weekly_folder_path = os.path.join(old_data_path, get_weekly_folder())
    os.mkdir(weekly_folder_path)
    old_db = os.path.join(base_path, "SpaceTradersDatabase.accdb")
    shutil.copy(old_db, weekly_folder_path)


def clear_db():
    for table_name in ["ID", "System", "Waypoint", "Markets", "Charts", "ShipAssignments", "JumpGates", "Shipyards", "Transactions"]:
        cmd = "DELETE FROM {};".format(table_name) # noqa
        cursor.execute(cmd)


def new_secrets():

    cursor.execute("SELECT * FROM Account")
    account_info = cursor.fetchone()

    account_token = account_info[0]
    email = account_info[1]

    down_for_maintenance = True
    while down_for_maintenance:
        status = rar.get_status(None)
        if "error" in status.keys():
            if status["error"]["code"] == 503:
                time.sleep(15)
            else:
                print(status)
                print("Unexpected status error")
                return status
        else:
            down_for_maintenance = False

    response = rar.register_new_agent(account_token, STARTING_FACTION, TARGET_UNAME, email)
    if "data" not in response.keys():
        print("Failed to register new agent")
        return response
    token = response["data"]["token"]

    cmd = "INSERT INTO ID (UNAME, TOKEN) VALUES ('{}', '{}')".format(TARGET_UNAME, token) # noqa
    cursor.execute(cmd)

    return response


def main():
    copy_old_data()
    clear_db()
    return new_secrets()


if __name__ == '__main__':
    main()
