from checker import check_connection
from datetime import datetime
from pathlib import Path

import json

STATE_FILE = Path(__file__).resolve().parent / "sample.json"

class ServerMonitor:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.failure_count = 0
        self.is_offline = False
        self.last_notification = None


    def check(self):
        found = check_connection(self.host, self.port)

        if found is True:
            self.handle_success()
        else:
            self.handle_failure()


    def handle_failure(self):
        self.failure_count += 1

        print("Failed to connect")

        if self.failure_count >= 2 and not self.is_offline:
            self.is_offline = True
            # send initial email

        if self.is_offline:
            pass
        # check 12 hour timespan and resend email


    def handle_success(self):
        print("Connection successful")

        if self.is_offline is True:
            self.is_offline = False
            # send recovery email

        self.failure_count = 0


    def save_state(self):
        data = {
            "failure_count": self.failure_count,
            "is_offline": self.is_offline,
            "last_notification": self.last_notification
        }

        with open("sample.json", "w") as f:
            json.dump(data, f)


    def load_state(self):
        with open("sample.json", "r") as f:
            data = json.load(f)

        print(data)
