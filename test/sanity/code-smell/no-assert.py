#!/usr/bin/env python
from __future__ import print_function

import re
import sys

ASSERT_RE = re.compile(r'.*(?<![-:a-zA-Z#][ -])\bassert\b(?!:).*')


def main():
    failed = False

    for path in sys.argv[1:]:
        with open(path, 'r') as f:
            for i, line in enumerate(f.readlines()):
                matches = ASSERT_RE.findall(line)

                if matches:
                    failed = True
                    lineno = i + 1
                    colno = line.index('assert') + 1
                    print('%s:%d:%d: raise AssertionError instead of: %s' % (path, lineno, colno, matches[0][colno - 1:]))

    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
