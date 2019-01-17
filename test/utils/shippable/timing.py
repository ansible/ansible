#!/usr/bin/env python3.7

import sys
import time

start = time.time()

sys.stdin.reconfigure(errors='surrogateescape')
sys.stdout.reconfigure(errors='surrogateescape')

for line in sys.stdin:
    seconds = time.time() - start
    sys.stdout.write('%02d:%02d %s' % (seconds // 60, seconds % 60, line))
    sys.stdout.flush()
