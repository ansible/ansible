"""Require Unix line endings."""

from __future__ import annotations

import sys


def main():
    """Main entry point."""
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'rb') as path_fd:
            contents = path_fd.read()

        if b'\r' in contents:
            print('%s: use "\\n" for line endings instead of "\\r\\n"' % path)


if __name__ == '__main__':
    main()
