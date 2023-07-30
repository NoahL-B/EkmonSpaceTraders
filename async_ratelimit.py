import time
import datetime
import asyncio
import http.client
from SECRETS import *


def connect(connection_type: str, path: str, params: dict = None):
    auth = "Bearer " + TOKEN
    headers = {
        "Accept": "application/json",
        "Authorization": auth
    }
    if params is not None:
        headers["Content-Type"] = "application/json"

    conn = http.client.HTTPSConnection("api.spacetraders.io")
    conn.request(connection_type, path, params, headers)

    res = conn.getresponse()
    data = res.read().decode("utf-8")

    time.sleep(0.5)

    return data




