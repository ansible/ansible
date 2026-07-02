from __future__ import annotations

import os
import sys
import time

child_pid = os.fork()

if child_pid > 0:
    time.sleep(60)
else:
    sys.exit()
