import sys

from powercfg import powercfg_daemon
from powermetrics import powermetrics_daemon
from push import push_powermetrics

if __name__ == '__main__':
    system = sys.platform.lower()
    if system.startswith("darwin"):
        print('try powermetrics')
        powermetrics_daemon(lambda x: push_powermetrics(x), report_interval=5)
    else:
        print('try powercfg')
        powercfg_daemon(lambda x: print(x), report_interval=5)
