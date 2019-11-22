#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import sys

ASSERT_RE = re.compile(r'^.*\bunwrap_var\(')

WHITELIST = frozenset((
    'lib/ansible/utils/unsafe_proxy.py',
))

def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path in WHITELIST:
            continue
        with open(path, 'r') as f:
            for i, line in enumerate(f.readlines()):
                matches = ASSERT_RE.findall(line)
                if matches:
                    lineno = i + 1
                    colno = line.index('unwrap_var') + 1
                    print(
                        '%s:%d:%d: use of unwrap_var is strictly monitored for incorrect use: %s' % (path, lineno, colno, matches[0][colno - 1:])
                    )


if __name__ == '__main__':
    main()
