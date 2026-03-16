"""Constants used by ansible-test's CLI entry point (as well as the rest of ansible-test). Imports should not be used in this file."""

# NOTE: This file resides in the _util/target directory to ensure compatibility with all supported Python versions.

from __future__ import annotations

REMOTE_ONLY_PYTHON_VERSIONS = (
    '3.9',
    '3.10',
    '3.11',
)

CONTROLLER_PYTHON_VERSIONS = (
    '3.12',
    '3.13',
    '3.14',
)
