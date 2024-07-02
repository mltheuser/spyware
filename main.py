import sys

from powercfg import powercfg_daemon
from powermetrics import powermetrics_deamon

if __name__ == '__main__':
    system = sys.platform.lower()
    if system.startswith("darwin"):
        print('try powermetrics')
        powermetrics_deamon(lambda x: print(x), report_interval=5)
    else:
        print('try powercfg')
        powercfg_daemon(lambda x: print(x), report_interval=5)
