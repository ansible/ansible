#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Command line entry point for ansible-test."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys

if __name__ == '__main__':
    ansible_root = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__))))
    source_root = os.path.join(ansible_root, 'test', 'lib')

    if os.path.exists(os.path.join(ansible_root, 'setup.py')) and os.path.exists(os.path.join(source_root, 'ansible_test', '_internal', 'cli.py')):
        # running from source, use that version of ansible-test instead of any version that may already be installed
        sys.path.insert(0, source_root)

    from ansible_test._internal.cli import main

    main()
