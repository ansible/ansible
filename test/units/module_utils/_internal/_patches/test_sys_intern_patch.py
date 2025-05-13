"""Test the `sys.intern` patch."""

from __future__ import annotations

import sys

from ansible.module_utils._internal._datatag._tags import Deprecated


def test_sys_intern() -> None:
    """Verify that `sys.intern` works with a tagged value."""
    assert sys.intern(Deprecated(msg='').tag('x')) == 'x'


def test_reference_equality() -> None:
    """Verify that `sys.intern` returns identical string references for the same string value."""
    class CustomStr(str):
        pass

    custom_str = CustomStr('hello')
    plain_str = "hello"

    assert sys.intern(custom_str) is sys.intern(plain_str)
