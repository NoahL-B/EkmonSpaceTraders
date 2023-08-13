import os
import pyodbc
from SpacePyTraders import client
from SECRETS import *

myClient = client.Client(UNAME, TOKEN)

base_path = os.path.dirname(__file__)
db_path = os.path.join(base_path, "SpaceTradersDatabase.accdb")

driver = 'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + db_path
conn = pyodbc.connect(driver)
conn.autocommit = True

cursor = conn.cursor()