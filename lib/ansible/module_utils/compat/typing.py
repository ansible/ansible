"""Compatibility layer for the `typing` module, providing all Python versions access to the newest type-hinting features."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# pylint: disable=wildcard-import,unused-wildcard-import

try:
    from typing_extensions import *
except ImportError:
    pass

try:
    from typing import *  # type: ignore[misc]
except ImportError:
    pass
