#!/usr/bin/env python

import os
import re
import sys


def main():
    skip = set([
        'test/sanity/code-smell/%s' % os.path.basename(__file__),
        'lib/ansible/module_utils/six/__init__.py',
        'lib/ansible/module_utils/urls.py',
        'test/units/module_utils/urls/test_Request.py',
        'test/units/module_utils/urls/test_fetch_url.py',
    ])

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path in skip:
            continue

        with open(path, 'r') as path_fd:
            for line, text in enumerate(path_fd.readlines()):
                match = re.search(r'^(?:[^#]*?)(urlopen)', text)

                if match:
                    print('%s:%d:%d: use `ansible.module_utils.urls.open_url` instead of `urlopen`' % (
                        path, line + 1, match.start(1) + 1))


if __name__ == '__main__':
    main()
