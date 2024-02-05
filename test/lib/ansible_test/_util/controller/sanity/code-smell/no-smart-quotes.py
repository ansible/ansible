"""Disallow use of Unicode quotes."""
# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import sys


def main():
    """Main entry point."""
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'rb') as path_fd:
            for line, text in enumerate(path_fd.readlines()):
                try:
                    text = text.decode('utf-8')
                except UnicodeDecodeError as ex:
                    print('%s:%d:%d: UnicodeDecodeError: %s' % (path, line + 1, ex.start + 1, ex))
                    continue

                match = re.search('([‘’“”])', text)

                if match:
                    print('%s:%d:%d: use ASCII quotes `\'` and `"` instead of Unicode quotes' % (
                        path, line + 1, match.start(1) + 1))


if __name__ == '__main__':
    main()
