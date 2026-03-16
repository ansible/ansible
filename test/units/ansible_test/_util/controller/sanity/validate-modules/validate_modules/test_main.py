"""Tests for validate-module's main module."""
from __future__ import annotations


def test_dict_members() -> None:
    from validate_modules.constants import FORBIDDEN_DICTIONARY_KEYS  # type: ignore[import-not-found]

    expected_keys = [key for key in dict.__dict__ if not key.startswith("__")]

    assert FORBIDDEN_DICTIONARY_KEYS == frozenset(expected_keys)
