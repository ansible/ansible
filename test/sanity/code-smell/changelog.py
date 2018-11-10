#!/usr/bin/env python

import sys
import subprocess


def main():
    paths = sys.argv[1:] or sys.stdin.read().splitlines()
    cmd = ['packaging/release/changelogs/changelog.py', 'lint'] + paths
    subprocess.check_call(cmd)


if __name__ == '__main__':
    main()
