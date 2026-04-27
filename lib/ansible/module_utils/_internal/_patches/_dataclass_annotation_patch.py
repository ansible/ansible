"""Patches for builtin `dataclasses` module."""

from __future__ import annotations

import dataclasses
import sys
import typing as t

from . import CallablePatch

# trigger the bug by exposing typing.ClassVar via a module reference that is not `typing`
_ts = sys.modules[__name__]
ClassVar = t.ClassVar


class DataclassesIsTypePatch(CallablePatch):
    """Patch broken ClassVar support in dataclasses when ClassVar is accessed via a module other than `typing`."""

    target_container: t.ClassVar = dataclasses
    target_attribute = '_is_type'

    @classmethod
    def is_patch_needed(cls) -> bool:
        @dataclasses.dataclass
        class CheckClassVar:
            # this is the broken case requiring patching: ClassVar dot-referenced from a module that is not `typing` is treated as an instance field
            # DTFIX-FUTURE: file/link CPython bug report, deprecate this patch if/when it's fixed in CPython
            a_classvar: _ts.ClassVar[int]  # type: ignore[name-defined]
            a_field: int

        return len(dataclasses.fields(CheckClassVar)) != 1

    def __call__(self, annotation, cls, a_module, a_type, is_type_predicate) -> bool:
        """
        This is a patched copy of `_is_type` from dataclasses.py in Python 3.13.
        It eliminates the redundant source module reference equality check for the ClassVar type that triggers the bug.
        """
        match = dataclasses._MODULE_IDENTIFIER_RE.match(annotation)  # type: ignore[attr-defined]
        if match:
            ns = None
            module_name = match.group(1)
            if not module_name:
                # No module name, assume the class's module did
                # "from dataclasses import InitVar".
                ns = sys.modules.get(cls.__module__).__dict__
            else:
                # Look up module_name in the class's module.
                module = sys.modules.get(cls.__module__)
                if module and module.__dict__.get(module_name):  # this is the patched line; removed `is a_module`
                    ns = sys.modules.get(a_type.__module__).__dict__
            if ns and is_type_predicate(ns.get(match.group(2)), a_module):
                return True
        return False
