"""Disallow use of assert."""
from __future__ import annotations

import re
import sys

ASSERT_RE = re.compile(r'^\s*assert[^a-z0-9_:]')


def main():
    """Main entry point."""
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'r', encoding='utf-8') as file:
            for i, line in enumerate(file.readlines()):
                matches = ASSERT_RE.findall(line)

                if matches:
                    lineno = i + 1
                    colno = line.index('assert') + 1
                    print('%s:%d:%d: raise AssertionError instead of: %s' % (path, lineno, colno, matches[0][colno - 1:]))


if __name__ == '__main__':
    main()
