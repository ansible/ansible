#!/usr/bin/env python

import sys


def main():
    skip = set([
        'test/integration/targets/template/files/foo.dos.txt',
        'test/integration/targets/win_regmerge/templates/win_line_ending.j2',
        'test/integration/targets/win_template/files/foo.dos.txt',
    ])

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path in skip:
            continue

        with open(path, 'rb') as path_fd:
            contents = path_fd.read()

        if b'\r' in contents:
            print('%s: use "\\n" for line endings instead of "\\r\\n"' % path)


if __name__ == '__main__':
    main()
