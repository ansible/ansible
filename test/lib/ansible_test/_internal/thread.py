"""Python threading tools."""
from __future__ import annotations

import collections.abc as c
import functools
import sys
import threading
import queue
import typing as t


TCallable = t.TypeVar('TCallable', bound=t.Callable[..., t.Any])


class WrappedThread(threading.Thread):
    """Wrapper around Thread which captures results and exceptions."""
    def __init__(self, action: c.Callable[[], t.Any]) -> None:
        super().__init__()
        self._result: queue.Queue[t.Any] = queue.Queue()
        self.action = action
        self.result = None

    def run(self):
        """
        Run action and capture results or exception.
        Do not override. Do not call directly. Executed by the start() method.
        """
        # We truly want to catch anything that the worker thread might do including call sys.exit.
        # Therefore, we catch *everything* (including old-style class exceptions)
        # noinspection PyBroadException
        try:
            self._result.put((self.action(), None))
        # pylint: disable=locally-disabled, bare-except
        except:  # noqa
            self._result.put((None, sys.exc_info()))

    def wait_for_result(self):
        """
        Wait for thread to exit and return the result or raise an exception.
        :rtype: any
        """
        result, exception = self._result.get()

        if exception:
            raise exception[1].with_traceback(exception[2])

        self.result = result

        return result


def mutex(func: TCallable) -> TCallable:
    """Enforce exclusive access on a decorated function."""
    lock = threading.Lock()

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapper around `func` which uses a lock to provide exclusive access to the function."""
        with lock:
            return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]  # requires https://www.python.org/dev/peps/pep-0612/ support
