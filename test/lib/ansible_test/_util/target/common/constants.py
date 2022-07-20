"""Constants used by ansible-test's CLI entry point (as well as the rest of ansible-test). Imports should not be used in this file."""

# NOTE: This file resides in the _util/target directory to ensure compatibility with all supported Python versions.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

REMOTE_ONLY_PYTHON_VERSIONS = (
    '2.7',
    '3.5',
    '3.6',
    '3.7',
    '3.8',
)

CONTROLLER_PYTHON_VERSIONS = (
    '3.9',
    '3.10',
    '3.11',
)
