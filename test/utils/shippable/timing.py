#!/usr/bin/env python3

import sys
import time

start = time.time()

for line in sys.stdin:
    seconds = time.time() - start
    sys.stdout.write('%02d:%02d %s' % (seconds // 60, seconds % 60, line))
    sys.stdout.flush()
