from __future__ import annotations

import contextlib
import enum
import typing as t

from ansible.utils.display import Display
from ansible.constants import config

display = Display()

# FUTURE: add sanity test to detect use of skip_on_ignore without Skippable (and vice versa)


class ErrorAction(enum.Enum):
    """Action to take when an error is encountered."""

    IGNORE = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()

    @classmethod
    def from_config(cls, setting: str, variables: dict[str, t.Any] | None = None) -> t.Self:
        """Return an `ErrorAction` enum from the specified Ansible config setting."""
        return cls[config.get_config_value(setting, variables=variables).upper()]


class _SkipException(BaseException):
    """Internal flow control exception for skipping code blocks within a `Skippable` context manager."""

    def __init__(self) -> None:
        super().__init__('Skipping ignored action due to use of `skip_on_ignore`. It is a bug to encounter this message outside of debugging.')


class _SkippableContextManager:
    """Internal context manager to support flow control for skipping code blocks."""

    def __enter__(self) -> None:
        pass

    def __exit__(self, exc_type, _exc_val, _exc_tb) -> bool:
        if exc_type is None:
            raise RuntimeError('A `Skippable` context manager was entered, but a `skip_on_ignore` handler was never invoked.')

        return exc_type is _SkipException  # only mask a _SkipException, allow all others to raise


Skippable = _SkippableContextManager()
"""Context manager singleton required to enclose `ErrorHandler.handle` invocations when `skip_on_ignore` is `True`."""


class ErrorHandler:
    """
    Provides a configurable error handler context manager for a specific list of exception types.
    Unhandled errors leaving the context manager can be ignored, treated as warnings, or allowed to raise by setting `ErrorAction`.
    """

    def __init__(self, action: ErrorAction) -> None:
        self.action = action

    @contextlib.contextmanager
    def handle(self, *args: type[BaseException], skip_on_ignore: bool = False) -> t.Iterator[None]:
        """
        Handle the specified exception(s) using the defined error action.
        If `skip_on_ignore` is `True`, the body of the context manager will be skipped for `ErrorAction.IGNORE`.
        Use of `skip_on_ignore` requires enclosure within the `Skippable` context manager.
        """
        if not args:
            raise ValueError('At least one exception type is required.')

        if skip_on_ignore and self.action == ErrorAction.IGNORE:
            raise _SkipException()  # skipping ignored action

        try:
            yield
        except args as ex:
            match self.action:
                case ErrorAction.WARNING:
                    display.error_as_warning(msg=None, exception=ex)
                case ErrorAction.ERROR:
                    raise
                case _:  # ErrorAction.IGNORE
                    pass

        if skip_on_ignore:
            raise _SkipException()  # completed skippable action, ensures the `Skippable` context was used

    @classmethod
    def from_config(cls, setting: str, variables: dict[str, t.Any] | None = None) -> t.Self:
        """Return an `ErrorHandler` instance configured using the specified Ansible config setting."""
        return cls(ErrorAction.from_config(setting, variables=variables))
