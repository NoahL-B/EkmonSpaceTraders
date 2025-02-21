import pyodbc
import os

UNAME = "EKMON"

base_path = os.path.dirname(__file__)
db_path = os.path.join(base_path, "SpaceTradersDatabase.accdb")

driver = 'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + db_path
conn = pyodbc.connect(driver)
conn.autocommit = True
cursor = conn.cursor()
cmd = "SELECT TOKEN FROM ID WHERE ((UNAME = '{0}'));".format(UNAME)  # noqa
cursor.execute(cmd)

try:
    TOKEN = next(cursor)[0]
except StopIteration as e:
    TOKEN = ""

cursor.close()

if __name__ == '__main__':
    print(UNAME)
    print(TOKEN)
