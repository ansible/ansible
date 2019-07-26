#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

MAIN_DISPLAY_IMPORT = 'from __main__ import display'


def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'r') as f:
            for i, line in enumerate(f.readlines()):
                if MAIN_DISPLAY_IMPORT in line:
                    lineno = i + 1
                    colno = line.index(MAIN_DISPLAY_IMPORT) + 1
                    print('%s:%d:%d: Display is a singleton, just import and instantiate' % (path, lineno, colno))


if __name__ == '__main__':
    main()
