#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Command line entry point for ansible-test."""

# NOTE: This file resides in the _util/target directory to ensure compatibility with all supported Python versions.

from __future__ import annotations

import importlib
import os
import sys


def main(args=None):
    """Main program entry point."""
    ansible_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_root = os.path.join(ansible_root, 'test', 'lib')

    if os.path.exists(os.path.join(source_root, 'ansible_test', '_internal', '__init__.py')):
        # running from source, use that version of ansible-test instead of any version that may already be installed
        sys.path.insert(0, source_root)

    # noinspection PyProtectedMember
    from ansible_test._util.target.common.constants import CONTROLLER_PYTHON_VERSIONS

    if version_to_str(sys.version_info[:2]) not in CONTROLLER_PYTHON_VERSIONS:
        raise SystemExit('This version of ansible-test cannot be executed with Python version %s. Supported Python versions are: %s' % (
            version_to_str(sys.version_info[:3]), ', '.join(CONTROLLER_PYTHON_VERSIONS)))

    if any(not os.get_blocking(handle.fileno()) for handle in (sys.stdin, sys.stdout, sys.stderr)):
        raise SystemExit('Standard input, output and error file handles must be blocking to run ansible-test.')

    # avoid using import to hide it from mypy
    internal = importlib.import_module('ansible_test._internal')
    cli_main = getattr(internal, 'main')

    cli_main(args)


def version_to_str(version):
    """Return a version string from a version tuple."""
    return '.'.join(str(n) for n in version)


if __name__ == '__main__':
    main()
