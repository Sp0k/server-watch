import logging, os, sched, time

from monitor import ServerMonitor


def exec_check(monitor, scheduler):
    try:
        logger.info("Starting scheduled server check")
        monitor.check()

    except Exception:
        logger.exception("Unexpected error during monitoring")

    finally:
        scheduler.enter(
            int(os.getenv("CHECK_INTERVAL", "1800")),
            1,
            exec_check,
            (monitor, scheduler,)
        )



# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

# Create server monitor
server_monitor = ServerMonitor(
    os.getenv("TARGET_HOST", "192.168.7.68"),
    int(os.getenv("TARGET_PORT", "22"))
)
server_monitor.load_state()

# Setup scheduler
scheduler = sched.scheduler(time.monotonic, time.sleep)
scheduler.enter(0, 1, exec_check, (server_monitor, scheduler,))
scheduler.run()
