#!/usr/bin/env python
"""Test to verify action plugins have an associated module to provide documentation."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys


def main():
    """Main entry point."""
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    module_names = set()

    for path in paths:
        if not path.startswith('lib/ansible/modules/'):
            continue

        name = os.path.splitext(os.path.basename(path))[0]

        if name != '__init__':
            if name.startswith('_'):
                name = name[1:]

            module_names.add(name)

    for path in paths:
        if not path.startswith('lib/ansible/plugins/action/'):
            continue

        name = os.path.splitext(os.path.basename(path))[0]

        if name not in module_names:
            print('%s: action plugin has no matching module to provide documentation' % path)


if __name__ == '__main__':
    main()
