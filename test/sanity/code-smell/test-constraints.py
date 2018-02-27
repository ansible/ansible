#!/usr/bin/env python

import re
import sys


def main():
    skip = set([
        'test/runner/requirements/constraints.txt',
        'test/runner/requirements/integration.cloud.azure.txt',
    ])

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path in skip:
            continue

        with open(path, 'r') as path_fd:
            for line, text in enumerate(path_fd.readlines()):
                match = re.search(r'^[^;#]*?([<>=])(?!.*sanity_ok.*)', text)

                if match:
                    print('%s:%d:%d: put constraints in `test/runner/requirements/constraints.txt`' % (
                        path, line + 1, match.start(1) + 1))


if __name__ == '__main__':
    main()
