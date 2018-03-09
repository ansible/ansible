#!/usr/bin/env python

import os
import re
import sys


def main():
    skip = set([
        'test/sanity/code-smell/%s' % os.path.basename(__file__),
    ])

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path in skip:
            continue

        with open(path, 'r') as path_fd:
            for line, text in enumerate(path_fd.readlines()):
                match = re.search(r'(FieldAttribute.*(default|required).*(default|required))', text)

                if match:
                    print('%s:%d:%d: use only one of `default` or `required` with `FieldAttribute`' % (
                          path, line + 1, match.start(1) + 1))


if __name__ == '__main__':
    main()
