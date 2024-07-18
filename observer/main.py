import sys

from push import push
from powercfg import powercfg_daemon
from powermetrics import powermetrics_daemon

if __name__ == '__main__':
    system = sys.platform.lower()
    if system.startswith("darwin"):
        print('try powermetrics')
        powermetrics_daemon(lambda x: push(x), report_interval=60*10)
    else:
        print('try powercfg')
        powercfg_daemon(lambda x: print(x), report_interval=60*2)