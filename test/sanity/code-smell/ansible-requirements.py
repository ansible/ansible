#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import sys


def read_file(path):
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as ex:  # pylint: disable=broad-except
        print('%s:%d:%d: Reading file failed: %s' % (path, 0, 0, re.sub(r'\s+', ' ', str(ex))))
        return None


def main():
    ORIGINAL_FILE = 'requirements.txt'
    VENDORED_COPY = 'test/lib/ansible_test/_data/requirements/sanity.import-plugins.txt'

    requirements_1 = read_file(ORIGINAL_FILE)
    requirements_2 = read_file(VENDORED_COPY)
    if requirements_1 is not None and requirements_2 is not None:
        if requirements_1 != requirements_2:
            print('%s:%d:%d: Not identical to %s' % (VENDORED_COPY, 0, 0, ORIGINAL_FILE))
            sys.exit()


if __name__ == '__main__':
    main()
