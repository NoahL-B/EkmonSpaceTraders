import datetime as dt
import os
import shutil

from SHARED import cursor
from SpacePyTraders import client

myClient = client.Client("", "")

UTC_NOW = dt.datetime.now(dt.timezone.utc)
TARGET_UNAME = "EKMON"
STARTING_FACTION = "COSMIC"
EMAIL = None

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
    for table_name in ["ID", "System", "Waypoint", "Markets", "Charts"]:
        cmd = "DELETE FROM {};".format(table_name) # noqa
        cursor.execute(cmd)


def new_secrets():
    endpoint = "v2/register"
    params = {
        "faction": STARTING_FACTION,
        "symbol": TARGET_UNAME
    }
    if EMAIL is not None:
        params["email"] = EMAIL
    response = myClient.generic_api_call("POST", endpoint, params, "")
    if not response:
        print("Failed to register new agent")
        return response
    token = response["data"]["token"]

    cmd = "INSERT INTO ID (UNAME, TOKEN) VALUES ('{}', '{}')".format(TARGET_UNAME, token) # noqa
    cursor.execute(cmd)

    return response


def main():
    copy_old_data()
    clear_db()
    new_secrets()


if __name__ == '__main__':
    main()
