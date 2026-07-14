"""
Testing utilities for use in integration tests, not unit tests or non-test code.
Provides better error behavior than Python's `assert` statement.
"""

from __future__ import annotations

import contextlib
import typing as t


class _Checker:
    @staticmethod
    def check(value: object, msg: str | None = 'Value is not truthy.') -> None:
        """Raise an `AssertionError` if the given `value` is not truthy."""
        if not value:
            raise AssertionError(msg)


@contextlib.contextmanager
def hard_fail_context(msg: str) -> t.Generator[_Checker]:
    """Enter a context which converts all exceptions to `BaseException` and provides a `Checker` instance for making assertions."""
    try:
        yield _Checker()
    except BaseException as ex:
        raise BaseException(f"Hard failure: {msg}") from ex
