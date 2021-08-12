#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys


def main():
    root_dir = os.getcwd() + os.path.sep

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if not os.path.islink(path.rstrip(os.path.sep)):
            continue

        if not os.path.exists(path):
            print('%s: broken symlinks are not allowed' % path)
            continue

        if path.endswith(os.path.sep):
            print('%s: symlinks to directories are not allowed' % path)
            continue

        real_path = os.path.realpath(path)

        if not real_path.startswith(root_dir):
            print('%s: symlinks outside content tree are not allowed: %s' % (path, os.path.relpath(real_path, os.path.dirname(path))))
            continue


if __name__ == '__main__':
    main()
