#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys


def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'rb') as path_fd:
            lines = path_fd.read().splitlines()

        missing = True
        if not lines:
            # Files are allowed to be empty of everything including boilerplate
            missing = False

        for text in lines:
            if text == b'__metaclass__ = type':
                missing = False
                break

        if missing:
            print('%s: missing: __metaclass__ = type' % path)


if __name__ == '__main__':
    main()
