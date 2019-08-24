#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys


def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if not os.path.islink(path.rstrip(os.path.sep)):
            continue

        if not os.path.exists(path):
            print('%s: broken symlinks are not allowed' % path)

        if path.endswith(os.path.sep):
            print('%s: symlinks to directories are not allowed' % path)


if __name__ == '__main__':
    main()
