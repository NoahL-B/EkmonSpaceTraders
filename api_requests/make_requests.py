import datetime
import json
import time
import threading
import requests

BASE_URL = "https://api.staging.spacetraders.io/v2/"


def rate_limit_retry(func, max_tries=10):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        tries = 0
        while result.status_code == 429 and tries < max_tries:
            tries += 1
            print("RATE LIMITED")
            result_dict = result.json()
            sleep_time = result_dict["error"]["data"]["retryAfter"]
            time.sleep(sleep_time)
            result = func(*args, **kwargs)
        return result
    return wrapper


def server_error_retry(func, max_tries=3):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        tries = 0
        while 500 <= result.status_code <= 599 and tries < max_tries:
            if result.status_code != 503 or tries == 0:
                print("SERVER FAILURE", result)
                print(result.json())
            tries += 1
            time.sleep(2 ** tries / 2)
            result = func(*args, **kwargs)

        if result.status_code == 503:
            import SHARED
            SHARED.stop_flag.set()
            raise SHARED.ServerMaintenanceException()

        return result
    return wrapper


def print_builder(*args, min_spaces=2, spaces=7):
    out_str = ""
    for a in args:
        if a is not None:
            str_a = str(a) + " " * min_spaces
            while len(str_a) < spaces:
                str_a += " "
            out_str += str_a
    return out_str


class RequestHandler:
    def __init__(self, rate_limit: int = 2, burst_limit: int = 30, printouts=False):
        self.rate_limit = rate_limit
        self.burst_limit = burst_limit
        self.recent_request_times = []
        self.recent_burst_times = []
        self.init_time = datetime.datetime.utcnow()
        self.request_count = 0
        self.successful_request_count = 0
        self.pacing_time = datetime.datetime.utcnow()
        self.pacing_rc = 0
        self.pacing_src = 0
        self.request_queue = {"HIGH": [], "NORMAL": [], "LOW": []}
        self.queue_lock = threading.Lock()
        self.request_lock = threading.Lock()
        self.print_lock = threading.Lock()
        self.printouts = printouts

    def __fulfill_queue(self):
        if not self.request_lock.locked():
            self.queue_lock.acquire()
            if self.request_queue["HIGH"]:
                result, func, args = self.request_queue["HIGH"].pop(0)
            elif self.request_queue["NORMAL"]:
                result, func, args = self.request_queue["NORMAL"].pop(0)
            elif self.request_queue["LOW"]:
                result, func, args = self.request_queue["LOW"].pop(0)
            else:
                self.queue_lock.release()
                return
            self.queue_lock.release()

            if self.printouts:
                printout = print_builder(self.queue_len(), self.request_count, self.successful_request_count, str(self.get_rpm())[:5], *args[:4])
                with self.print_lock:
                    print(printout)

            self.request_lock.acquire()
            try:
                result.append(func(*args, ))
                self.successful_request_count += 1
                self.pacing_src += 1
            finally:
                self.request_lock.release()

        else:
            time.sleep(1)

    def __add_to_queue(self, queue_item, priority="NORMAL"):
        if priority not in ["HIGH", "NORMAL", "LOW"]:
            raise ValueError
        self.queue_lock.acquire()
        priority_queue = self.request_queue[priority]
        priority_queue.append(queue_item)
        self.queue_lock.release()

    def queue_len(self):
        self.queue_lock.acquire()
        total_len = len(self.request_queue["HIGH"])
        total_len += len(self.request_queue["NORMAL"])
        total_len += len(self.request_queue["LOW"])
        self.queue_lock.release()
        return total_len

    def __queue_request(self, func, args, priority="NORMAL"):
        result = []
        queue_item = (result, func, args)
        self.__add_to_queue(queue_item, priority=priority)
        while not result:
            self.__fulfill_queue()

        return result[0]

    def __clear_old_requests(self):
        now = datetime.datetime.utcnow()
        rate_delta = datetime.timedelta(seconds=1)
        burst_delta = datetime.timedelta(seconds=60)
        if self.recent_request_times:
            old = self.recent_request_times[0]
            if (now - old) > rate_delta:
                self.recent_request_times = []
        if self.recent_burst_times:
            old = self.recent_burst_times[0]
            if (now - old) > burst_delta:
                self.recent_burst_times = []

    def start_pacing(self):
        self.pacing_rc = 0
        self.pacing_src = 0
        self.pacing_time = datetime.datetime.utcnow()

    def get_rpm(self, success_only=True, pacing=False):
        if pacing:
            start_time = self.pacing_time
            if success_only:
                request_count = self.pacing_src
            else:
                request_count = self.pacing_rc
        else:
            start_time = self.init_time
            if success_only:
                request_count = self.successful_request_count
            else:
                request_count = self.request_count

        now = datetime.datetime.utcnow()
        alive_time = now - start_time
        minute = datetime.timedelta(minutes=1)
        minutes_alive = alive_time / minute
        if minutes_alive == 0:
            return 0
        rpm = request_count / minutes_alive
        return rpm

    def __wait_to_request(self):
        self.__clear_old_requests()
        while len(self.recent_request_times) >= self.rate_limit and len(self.recent_burst_times) >= self.burst_limit:
            time.sleep(self.__get_time_to_request())
            self.__clear_old_requests()

    def __get_time_to_request(self):
        if len(self.recent_request_times) < self.rate_limit:
            return 0
        if len(self.recent_burst_times) < self.burst_limit:
            return 0

        now = datetime.datetime.utcnow()
        rate_delta = datetime.timedelta(seconds=1)
        burst_delta = datetime.timedelta(seconds=60)
        rate_next_clear_time = self.recent_request_times[0] + rate_delta
        burst_next_clear_time = self.recent_burst_times[0] + burst_delta
        timedelta_to_rate_clear = rate_next_clear_time - now # noqa
        timedelta_to_burst_clear = burst_next_clear_time - now # noqa
        seconds_to_rate_clear = timedelta_to_rate_clear / datetime.timedelta(seconds=1)
        seconds_to_burst_clear = timedelta_to_burst_clear / datetime.timedelta(seconds=1)
        return min(seconds_to_rate_clear, seconds_to_burst_clear)

    def __record_request_time(self):
        now = datetime.datetime.utcnow()
        if len(self.recent_request_times) < self.rate_limit:
            self.recent_request_times.append(now)
        else:
            self.recent_burst_times.append(now)

    def get(self, endpoint: str, params: dict = None, headers: dict = None, token: str = None, priority="NORMAL"):
        return self.__queue_request(self.__make_request, ("GET", endpoint, params, headers, token), priority=priority)

    def post(self, endpoint: str, params: dict = None, headers: dict = None, token: str = None, priority="NORMAL"):
        return self.__queue_request(self.__make_request, ("POST", endpoint, params, headers, token), priority=priority)

    def patch(self, endpoint: str, params: dict = None, headers: dict = None, token: str = None, priority="NORMAL"):
        return self.__queue_request(self.__make_request, ("PATCH", endpoint, params, headers, token), priority=priority)

    @server_error_retry
    @rate_limit_retry
    def __make_request(self, request_type: str, endpoint: str, params: dict = None, headers: dict = None, token: str = None):
        if request_type not in ["GET", "POST", "PATCH"]:
            raise ValueError

        self.request_count += 1
        self.pacing_rc += 1

        if params is None:
            params = dict()
        if headers is None:
            headers = dict()

        full_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if token is not None:
            full_headers['Authorization'] = 'Bearer ' + token
        for header in headers.keys():
            full_headers[header] = headers[header]

        url = BASE_URL + endpoint
        params_json = json.dumps(params)

        self.__wait_to_request()

        result = None
        if request_type == "GET":
            result = requests.request(request_type, url, headers=full_headers, params=params)
        elif request_type == "PATCH" or request_type == "POST":
            result = requests.request(request_type, url, headers=full_headers, data=params_json)
        self.__record_request_time()

        if result.status_code == 429:
            while len(self.recent_request_times) < self.rate_limit or len(self.recent_burst_times) < self.burst_limit:
                self.__record_request_time()

        return result

    def get_success_rate(self, pacing_only=False):
        if pacing_only:
            return self.pacing_src / self.pacing_rc
        else:
            return self.successful_request_count / self.request_count


def main():
    rh = RequestHandler()
    for i in range(100):
        response = rh.get('')
        print(i, response)
    print(rh.get_rpm())


if __name__ == '__main__':
    main()
