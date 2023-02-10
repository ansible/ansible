"""Compatibility layer for the `typing` module, providing all Python versions access to the newest type-hinting features."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# pylint: disable=wildcard-import,unused-wildcard-import

# catch *all* exceptions to prevent type annotation support module bugs causing runtime failures
# (eg, https://github.com/ansible/ansible/issues/77857)

try:
    from typing_extensions import *
except Exception:  # pylint: disable=broad-except
    pass

try:
    from typing import *  # type: ignore[assignment]
except Exception:  # pylint: disable=broad-except
    pass


try:
    cast  # type: ignore[used-before-def]
except NameError:
    def cast(typ, val):  # type: ignore[no-redef]
        return val
