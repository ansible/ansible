from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import sys
import time

child_pid = os.fork()

if child_pid > 0:
    time.sleep(60)
else:
    sys.exit()
