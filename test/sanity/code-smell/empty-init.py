#!/usr/bin/env python

import os
import re
import sys


def main():
    skip = set([
        'test/sanity/code-smell/%s' % os.path.basename(__file__),
        # facts is grandfathered in but will break namespacing
        # the only way to fix it is to deprecate and eventually remove it
        # six will break namespacing but because it is bundled we should not be overriding it
        'lib/ansible/module_utils/facts/__init__.py',
        'lib/ansible/module_utils/six/__init__.py',
    ])

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path in skip:
            continue

        if os.path.getsize(path) > 0:
            print('%s: empty __init__.py required' % path)


if __name__ == '__main__':
    main()
