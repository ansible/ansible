#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import subprocess


def main():
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    allowed_extensions = ('.yml', '.yaml')

    for path in paths:
        ext = os.path.splitext(path)[1]

        if ext not in allowed_extensions:
            print('%s:%d:%d: extension must be one of: %s' % (path, 0, 0, ', '.join(allowed_extensions)))

        if os.path.basename(path).startswith('.'):
            print('%s:%d:%d: file must not be a dotfile' % (path, 0, 0))

    cmd = ['packaging/release/changelogs/changelog.py', 'lint'] + paths
    subprocess.check_call(cmd)


if __name__ == '__main__':
    main()
