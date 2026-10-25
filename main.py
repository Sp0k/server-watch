import sched, time

from monitor import ServerMonitor


def exec_check(monitor, scheduler):
    monitor.check()

    scheduler.enter(3, 1, exec_check, (monitor, scheduler,))



# Create server monitor
server_monitor = ServerMonitor('192.168.7.68', 22)
server_monitor.load_state()
server_monitor.save_state()
server_monitor.load_state()
# server_monitor.check()

# Setup scheduler
# scheduler = sched.scheduler(time.monotonic, time.sleep)
# scheduler.enter(3, 1, exec_check, (server_monitor, scheduler,))
# scheduler.run()
