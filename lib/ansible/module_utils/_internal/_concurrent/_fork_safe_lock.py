"""A threading.Lock wrapper that remains safe across os.fork()."""

from __future__ import annotations as _annotations

import os as _os
import threading as _threading

_FORK_LOCK_TIMEOUT = 10


class ForkSafeLock:
    """A lock that safely handles os.fork() by acquiring before fork and releasing in both parent and child."""

    def __init__(self) -> None:
        self._lock = _threading.Lock()
        self._acquired_before_fork = False
        _os.register_at_fork(
            before=self._before_fork,
            after_in_parent=self._after_fork,
            after_in_child=self._after_fork,
        )

    def _before_fork(self) -> None:
        self._acquired_before_fork = self._lock.acquire(timeout=_FORK_LOCK_TIMEOUT)
        if not self._acquired_before_fork:
            raise RuntimeError("timed out acquiring lock before fork")

    def _after_fork(self) -> None:
        # Only release if _before_fork actually acquired the lock. CPython swallows
        # exceptions raised by at-fork callbacks and proceeds with the fork anyway, so on a
        # timed-out acquire this still runs; releasing then would either raise "release
        # unlocked lock" or release a lock still held by another thread.
        if self._acquired_before_fork:
            self._acquired_before_fork = False
            self._lock.release()

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
