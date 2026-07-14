from __future__ import annotations

import contextlib
import signal
import types
import typing as _t

from ansible.module_utils import datatag


class AnsibleTimeoutError(BaseException):
    """A general purpose timeout."""

    _MAX_TIMEOUT = 100_000_000
    """
    The maximum supported timeout value.
    This value comes from BSD's alarm limit, which is due to that function using setitimer.
    """

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

        super().__init__(f"Timed out after {timeout} second(s).")

    @classmethod
    @contextlib.contextmanager
    def alarm_timeout(cls, timeout: int | None) -> _t.Iterator[None]:
        """
        Context for running code under an optional timeout.
        Raises an instance of this class if the timeout occurs.

        New usages of this timeout mechanism are discouraged.
        """
        if timeout is not None:
            if not isinstance(timeout, int):
                raise TypeError(f"Timeout requires 'int' argument, not {datatag.native_type_name(timeout)!r}.")

            if timeout < 0 or timeout > cls._MAX_TIMEOUT:
                # On BSD based systems, alarm is implemented using setitimer.
                # If out-of-bounds values are passed to alarm, they will return -1, which would be interpreted as an existing timer being set.
                # To avoid that, bounds checking is performed in advance.
                raise ValueError(f'Timeout {timeout} is invalid, it must be between 0 and {cls._MAX_TIMEOUT}.')

        if not timeout:
            yield  # execute the context manager's body
            return  # no timeout to deal with, exit immediately

        def on_alarm(_signal: int, _frame: types.FrameType) -> None:
            raise cls(timeout)

        if signal.signal(signal.SIGALRM, on_alarm):
            raise RuntimeError("An existing alarm handler was present.")

        try:
            try:
                if signal.alarm(timeout):
                    raise RuntimeError("An existing alarm was set.")

                yield  # execute the context manager's body
            finally:
                # Disable the alarm.
                # If the alarm fires inside this finally block, the alarm is still disabled.
                # This guarantees the cleanup code in the outer finally block runs without risk of encountering the `TaskTimeoutError` from the alarm.
                signal.alarm(0)
        finally:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
