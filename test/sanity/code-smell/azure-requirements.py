#!/usr/bin/env python
"""Make sure the Azure requirements files match."""

import filecmp
import os


def main():
    src = 'packaging/requirements/requirements-azure.txt'
    dst = 'test/runner/requirements/integration.cloud.azure.txt'

    if not filecmp.cmp(src, dst):
        print('%s: must be identical to `%s`' % (dst, src))

    if os.path.islink(dst):
        print('%s: must not be a symbolic link' % dst)


if __name__ == '__main__':
    main()
