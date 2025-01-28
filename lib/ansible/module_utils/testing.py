"""
Utilities to support unit testing of Ansible Python modules.
Not supported for use cases other than testing.
"""

from __future__ import annotations

from ._internal._testing import (
    patch_module_args,
)

__all__ = (
    'patch_module_args',
)
