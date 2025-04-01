import os
import threading
import time

import pyodbc
import datetime

base_path = os.path.dirname(__file__)
db_path = os.path.join(base_path, "SpaceTradersDatabase.accdb")

driver = 'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + db_path
conn = pyodbc.connect(driver)
conn.autocommit = True

stop_flag = threading.Event()


class ThreadStoppedException(Exception):
    def __init__(self, message=""):
        super().__init__(message)


class ServerMaintenanceException(Exception):
    def __init__(self, message=""):
        super().__init__(message)


class WrongResetException(Exception):
    def __init__(self, message=""):
        super().__init__(message)


def tka_sleep(secs, tk_timeout=20):  # tka stands for Thread Kill Aware
    if stop_flag.is_set():
        raise ThreadStoppedException()
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(seconds=secs)
    tk_delta = datetime.timedelta(seconds=tk_timeout)
    while end_time - datetime.datetime.now() > tk_delta:
        if stop_flag.is_set():
            raise ThreadStoppedException()
        time.sleep(tk_timeout)
    remaining_time = end_time - datetime.datetime.now()
    remaining_seconds = remaining_time.total_seconds()
    time.sleep(remaining_seconds)


def stop_threads_and_wait():
    stop_flag.set()
    from SECRETS import UNAME
    if UNAME in threading.current_thread().name:
        raise ThreadStoppedException()
    threads = threading.enumerate()
    for t in threads:
        if UNAME in t.name:
            while t.is_alive():
                print(t)
                t.join(20)
    stop_flag.clear()


def get_cursor():
    cursor = conn.cursor()
    return cursor