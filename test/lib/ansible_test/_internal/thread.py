"""Python threading tools."""
from __future__ import annotations

import collections.abc as c
import contextlib
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

    def run(self) -> None:
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

    def wait_for_result(self) -> t.Any:
        """Wait for thread to exit and return the result or raise an exception."""
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


__named_lock = threading.Lock()
__named_locks: dict[str, threading.Lock] = {}


@contextlib.contextmanager
def named_lock(name: str) -> c.Iterator[bool]:
    """
    Context manager that provides named locks using threading.Lock instances.
    Once named lock instances are created they are not deleted.
    Returns True if this is the first instance of the named lock, otherwise False.
    """
    with __named_lock:
        if lock_instance := __named_locks.get(name):
            first = False
        else:
            first = True
            lock_instance = __named_locks[name] = threading.Lock()

    with lock_instance:
        yield first
