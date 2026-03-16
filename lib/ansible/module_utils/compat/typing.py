"""Compatibility layer for the `typing` module, providing all Python versions access to the newest type-hinting features."""
from __future__ import annotations

# pylint: disable=wildcard-import,unused-wildcard-import

# catch *all* exceptions to prevent type annotation support module bugs causing runtime failures
# (eg, https://github.com/ansible/ansible/issues/77857)

TYPE_CHECKING = False

try:
    from typing_extensions import *
except Exception:  # pylint: disable=broad-except
    pass

try:
    from typing import *  # type: ignore[assignment,no-redef]
except Exception:  # pylint: disable=broad-except
    pass


# this import and patch occur after typing_extensions/typing imports since the presence of those modules affects dataclasses behavior
from .._internal._patches import _dataclass_annotation_patch

_dataclass_annotation_patch.DataclassesIsTypePatch.patch()
