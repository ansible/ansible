"""Prevent files from being added to directories that are now obsolete."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys


def main():
    """Main entry point."""
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    for path in paths:
        print('%s: directory "%s/" is obsolete and should not contain any files' % (path, os.path.dirname(path)))


if __name__ == '__main__':
    main()
