#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys


def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'rb') as path_fd:
            contents = path_fd.read()

        if b'\r' in contents:
            print('%s: use "\\n" for line endings instead of "\\r\\n"' % path)


if __name__ == '__main__':
    main()
