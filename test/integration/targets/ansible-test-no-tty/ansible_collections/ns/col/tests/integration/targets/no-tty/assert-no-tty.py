#!/usr/bin/env python
"""Assert no TTY is available."""

import sys

status = 0

for handle in sys.stdin, sys.stdout, sys.stderr:
    if handle.isatty():
        print(f'{handle} is a TTY', file=sys.stderr)
        status += 1

sys.exit(status)
