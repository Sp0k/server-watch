from checker import check_connection
from datetime import datetime, timedelta, timezone
from notifier import sendEmail
from pathlib import Path

import logging, json, os

logger = logging.getLogger(__name__)

STATE_FILE = Path(
    os.getenv(
        "STATE_FILE",
        str(Path(__file__).resolve().parent / "watch_state.json")
    )
)

POSITIVE_MESSAGE = dict()
POSITIVE_MESSAGE['message'] = 'The Linux server is back online.'
POSITIVE_MESSAGE['subject'] = 'Server Online'

FIRST_NEGATIVE_MESSAGE = dict()
FIRST_NEGATIVE_MESSAGE['message'] = 'Warning: The Linux server failed two consecutive checks.'
FIRST_NEGATIVE_MESSAGE['subject'] = 'Server Offline'

REPEAT_NEGATIVE_MESSAGE = dict()
REPEAT_NEGATIVE_MESSAGE['message'] = 'Warning: The Linux server has not come back online since failing two consecutive checks.'
REPEAT_NEGATIVE_MESSAGE['subject'] = 'Server Still Offline'

class ServerMonitor:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.failure_count = 0
        self.is_offline = False
        self.last_notification = None
        self.recovering_pending = False


    def check(self):
        found = check_connection(self.host, self.port)

        if found is True:
            self.handle_success()
        else:
            self.handle_failure()

        self.save_state()


    def handle_failure(self):
        self.failure_count += 1

        logger.warning(
            "Connection to %s:%s failed (%d consecutive failures)",
            self.host,
            self.port,
            self.failure_count
        )

        if self.failure_count < 2:
            return

        if not self.is_offline:
            self.is_offline = True
            logger.error("Server %s is now considered OFFLINE", self.host)

        now = datetime.now(timezone.utc)

        if self.last_notification is None:
            message = FIRST_NEGATIVE_MESSAGE

        elif now - self.last_notification >= timedelta(hours=12):
            message = REPEAT_NEGATIVE_MESSAGE

        else:
            return

        try:
            sendEmail(message["message"], message["subject"])

        except Exception:
            logger.exception(
                "Failed to send outrage notification for %s",
                self.host
            )

        else:
            self.last_notification = datetime.now(timezone.utc)
            logger.info(
                "Outage notification submitted successfully for %s",
                self.host
            )


    def handle_success(self):
        logger.info("Connection to %s successful", self.host)

        if self.is_offline:
            logger.info("Server %s has recovered", self.host)

            self.is_offline = False
            self.last_notification = None
            self.recovering_pending = True

        self.failure_count = 0

        if self.recovering_pending:
            try:
                sendEmail(POSITIVE_MESSAGE["message"], POSITIVE_MESSAGE["subject"])

            except Exception:
                logger.exception("Failed to send recovery notification")

            else:
                self.recovering_pending = False
                logger.info("Recovery notification submitted successfully")


    def save_state(self):
        data = {
            "failure_count": self.failure_count,
            "is_offline": self.is_offline,
            "last_notification": (
                self.last_notification.isoformat()
                if self.last_notification is not None
                else None
            ),
            "recovering_pending": self.recovering_pending
        }

        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

        with STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


    def load_state(self):
        if not STATE_FILE.exists():
            logger.info("No previous state found. Starting fresh.")
            return

        with STATE_FILE.open("r") as f:
            data = json.load(f)

        self.failure_count = data.get("failure_count", 0)
        self.is_offline = data.get("is_offline", False)

        timestamp = data.get("last_notification")

        self.last_notification = (
            datetime.fromisoformat(timestamp)
            if timestamp is not None
            else None
        )

        self.recovering_pending = data.get("recovering_pending", False)
