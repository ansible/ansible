from __future__ import annotations

import os
import signal

from ansible.module_utils._internal._concurrent._fork_safe_lock import ForkSafeLock
from ansible.plugins.callback import CallbackBase

# This callback plugin reliably delivers a SIGINT (a Ctrl-C) as the fifth worker starts, where CPython discards any exception the controller's handler raises.
# With DELIVER_SIGINT=fork it arrives at the start of a ForkSafeLock's after-fork callback, where that exception also leaves the lock held.
# With DELIVER_SIGINT=finalizer it arrives in a finalizer.


class _SignalsWhenFinalized:
    def __del__(self) -> None:
        signal.raise_signal(signal.SIGINT)


class _SignalsAfterFork(ForkSafeLock):
    def __init__(self) -> None:
        self._parent_pid = os.getpid()

        super().__init__()

        # runs after the lock's callback, and hangs if that left the lock held, as the next use of a real one does
        os.register_at_fork(after_in_parent=self._use)

    def _after_fork(self) -> None:
        if os.getpid() == self._parent_pid:
            signal.raise_signal(signal.SIGINT)

        super()._after_fork()

    def _use(self) -> None:
        with self:
            pass


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'deliver_sigint'
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self) -> None:
        super().__init__()

        self._where = os.environ['DELIVER_SIGINT']
        self._starts = 0

    def v2_runner_on_start(self, host, task) -> None:
        self._starts += 1

        if self._starts != 5:
            return

        if self._where == 'fork':
            _SignalsAfterFork()  # the worker is forked next
        else:
            _SignalsWhenFinalized()
