#!/usr/bin/env python
"""Make sure the Azure requirements files match."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import filecmp
import os


def main():
    src = 'packaging/requirements/requirements-azure.txt'
    dst = 'test/lib/ansible_test/_data/requirements/integration.cloud.azure.txt'

    missing = [p for p in [src, dst] if not os.path.isfile(p)]

    if missing:
        for path in missing:
            print('%s: missing required file' % path)

        return

    if not filecmp.cmp(src, dst):
        print('%s: must be identical to `%s`' % (dst, src))

    if os.path.islink(dst):
        print('%s: must not be a symbolic link' % dst)


if __name__ == '__main__':
    main()
