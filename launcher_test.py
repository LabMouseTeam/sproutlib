from labmouse.launcher.process import ProcessLauncher
from labmouse.common.log import LogHelper
import time
import yaml
import sys


if __name__ == "__main__":
    s = sys.argv[1]
    f = open(s, 'r')
    d = f.read()

    # We load YAML here for the Logger.
    y = yaml.safe_load(d)

    # Create logger for us and the process
    L = LogHelper(y['log'])
    l = L[L.logger]

    # Let ProcessLauncher change the TZ. Don't log before that.
    p = ProcessLauncher(L, y['process'])
    p.start()
