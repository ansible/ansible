#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys


def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if os.path.getsize(path) > 0:
            print('%s: empty __init__.py required' % path)


if __name__ == '__main__':
    main()
