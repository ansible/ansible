"""Patch broken ClassVar support in dataclasses when ClassVar is accessed via a module other than `typing`."""
# deprecated: description='verify ClassVar support in dataclasses has been fixed in Python before removing this patching code', python_version='3.12'

from __future__ import annotations

import dataclasses
import sys
import typing as t

# trigger the bug by exposing typing.ClassVar via a module reference that is not `typing`
_ts = sys.modules[__name__]
ClassVar = t.ClassVar


def patch_dataclasses_is_type() -> None:
    if not _is_patch_needed():
        return  # pragma: nocover

    try:
        real_is_type = dataclasses._is_type  # type: ignore[attr-defined]
    except AttributeError:  # pragma: nocover
        raise RuntimeError("unable to patch broken dataclasses ClassVar support") from None

    # patch dataclasses._is_type - impl from https://github.com/python/cpython/blob/4c6d4f5cb33e48519922d635894eef356faddba2/Lib/dataclasses.py#L709-L765
    def _is_type(annotation, cls, a_module, a_type, is_type_predicate):
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

    _is_type._orig_impl = real_is_type  # type: ignore[attr-defined]  # stash this away to allow unit tests to undo the patch

    dataclasses._is_type = _is_type  # type: ignore[attr-defined]

    try:
        if _is_patch_needed():
            raise RuntimeError("patching had no effect")  # pragma: nocover
    except Exception as ex:  # pragma: nocover
        dataclasses._is_type = real_is_type  # type: ignore[attr-defined]
        raise RuntimeError("dataclasses ClassVar support is still broken after patching") from ex


def _is_patch_needed() -> bool:
    @dataclasses.dataclass
    class CheckClassVar:
        # this is the broken case requiring patching: ClassVar dot-referenced from a module that is not `typing` is treated as an instance field
        # DTFIX-RELEASE: add link to CPython bug report to-be-filed (or update associated deprecation comments if we don't)
        a_classvar: _ts.ClassVar[int]  # type: ignore[name-defined]
        a_field: int

    return len(dataclasses.fields(CheckClassVar)) != 1
