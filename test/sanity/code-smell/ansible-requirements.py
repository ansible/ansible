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
        print('%s:%d:%d: unable to read required file %s' % (path, 0, 0, re.sub(r'\s+', ' ', str(ex))))
        return None


def main():
    ORIGINAL_FILE = 'requirements.txt'
    VENDORED_COPY = 'test/lib/ansible_test/_data/requirements/sanity.import-plugins.txt'

    original_requirements = read_file(ORIGINAL_FILE)
    vendored_requirements = read_file(VENDORED_COPY)

    if original_requirements is not None and vendored_requirements is not None:
        if original_requirements != vendored_requirements:
            print('%s:%d:%d: must be identical to %s' % (VENDORED_COPY, 0, 0, ORIGINAL_FILE))


if __name__ == '__main__':
    main()
