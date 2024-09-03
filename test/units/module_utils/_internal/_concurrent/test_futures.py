from __future__ import annotations

import concurrent.futures as _cf
import subprocess
import sys
import time

import pytest

from ansible.module_utils._internal._concurrent import _futures


def test_daemon_thread_pool_nonblocking_cm_exit() -> None:
    """Ensure that the ThreadPoolExecutor context manager exit is not blocked by in-flight tasks."""
    with _futures.DaemonThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(time.sleep, 5)

        with pytest.raises(_cf.TimeoutError):  # deprecated: description='aliased to stdlib TimeoutError in 3.11' python_version='3.10'
            future.result(timeout=1)

    assert future.running()  # ensure the future is still going (ie, we didn't have to wait for it to return)


_task_success_msg = "work completed"
_process_success_msg = "exit success"
_timeout_sec = 3
_sleep_time_sec = _timeout_sec * 2


def test_blocking_shutdown() -> None:
    """Run with the DaemonThreadPoolExecutor patch disabled to verify that shutdown is blocked by in-flight tasks."""
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(args=[sys.executable, __file__, 'block'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, timeout=_timeout_sec)


def test_non_blocking_shutdown() -> None:
    """Run with the DaemonThreadPoolExecutor patch enabled to verify that shutdown is not blocked by in-flight tasks."""
    cp = subprocess.run(args=[sys.executable, __file__, ''], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, timeout=_timeout_sec)

    assert _task_success_msg in cp.stdout
    assert _process_success_msg in cp.stdout


def _run_blocking_exit_test(use_patched: bool) -> None:  # pragma: nocover
    """Helper for external process integration test."""
    tpe_type = _futures.DaemonThreadPoolExecutor if use_patched else _cf.ThreadPoolExecutor

    with tpe_type(max_workers=2) as tp:
        fs_non_blocking = tp.submit(lambda: print(_task_success_msg))
        assert [tp.submit(time.sleep, _sleep_time_sec) for _idx in range(4)]  # not a pointless statement
        fs_non_blocking.result(timeout=1)

    print(_process_success_msg)


def main() -> None:  # pragma: nocover
    """Used by test_(non)blocking_shutdown as a script-style run."""
    _run_blocking_exit_test(sys.argv[1] != 'block')


if __name__ == '__main__':  # pragma: nocover
    main()
