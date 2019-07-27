#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys


def main():
    # These files pre-date the boilerplate test and should be fixed up as time goes on
    prune = (
        'contrib/inventory/',
        'contrib/vault/',
        'docs/',
        'examples/',
        'test/integration/',
        'test/legacy/',
        'test/units/',
    )

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if any(path.startswith(p) for p in prune):
            continue

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
