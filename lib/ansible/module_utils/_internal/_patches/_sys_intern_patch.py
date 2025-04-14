"""Patches for the builtin `sys` module."""

from __future__ import annotations

import contextlib
import sys
import typing as t

from . import CallablePatch


class _CustomStr(str):
    """Wrapper around `str` to test if subclasses are accepted."""


class SysInternPatch(CallablePatch):
    """Patch `sys.intern` so that subclasses of `str` are accepted."""

    target_container: t.ClassVar = sys
    target_attribute = 'intern'

    @classmethod
    def is_patch_needed(cls) -> bool:
        with contextlib.suppress(TypeError):
            sys.intern(_CustomStr("x"))
            return False

        return True

    def __call__(self, value: str):
        if type(value) is not str and isinstance(value, str):  # pylint: disable=unidiomatic-typecheck
            value = str(value)

        return type(self).unpatched_implementation(value)
