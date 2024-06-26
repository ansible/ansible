"""Require empty __init__.py files."""
from __future__ import annotations

import os
import sys


def main():
    """Main entry point."""
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if os.path.getsize(path) > 0:
            print('%s: empty __init__.py required' % path)


if __name__ == '__main__':
    main()
