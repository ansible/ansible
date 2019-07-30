#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import sys


def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'r') as path_fd:
            for line, text in enumerate(path_fd.readlines()):
                match = re.search(r'^(?:[^#]*?)(urlopen)', text)

                if match:
                    print('%s:%d:%d: use `ansible.module_utils.urls.open_url` instead of `urlopen`' % (
                        path, line + 1, match.start(1) + 1))


if __name__ == '__main__':
    main()
