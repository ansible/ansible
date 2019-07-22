#!/usr/bin/env python

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

    cmd = ['packaging/release/changelogs/changelog.py', 'lint'] + paths
    subprocess.check_call(cmd)


if __name__ == '__main__':
    main()
