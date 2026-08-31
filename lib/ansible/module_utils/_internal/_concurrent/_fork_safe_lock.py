"""A threading.Lock wrapper that remains safe across os.fork()."""

from __future__ import annotations as _annotations

import os as _os
import threading as _threading

_FORK_LOCK_TIMEOUT = 10


class ForkSafeLock:
    """A lock that safely handles os.fork() by acquiring before fork and releasing in both parent and child."""

    def __init__(self) -> None:
        self._lock = _threading.Lock()
        _os.register_at_fork(
            before=self._before_fork,
            after_in_parent=self._lock.release,
            after_in_child=self._lock.release,
        )

    def _before_fork(self) -> None:
        if not self._lock.acquire(timeout=_FORK_LOCK_TIMEOUT):
            raise RuntimeError("timed out acquiring lock before fork")

    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        return self._lock.acquire(blocking=blocking, timeout=timeout)

    def release(self) -> None:
        self._lock.release()

    def locked(self) -> bool:
        return self._lock.locked()

    def __enter__(self) -> ForkSafeLock:
        self._lock.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._lock.__exit__(exc_type, exc_val, exc_tb)
