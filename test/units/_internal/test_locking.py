from __future__ import annotations

import time
import threading
import os

from concurrent.futures import ThreadPoolExecutor, wait

from ansible._internal import _locking


def test_blocking_lock(tmp_path: str) -> None:
    """Validate synchronization behavior of `named_mutex`."""
    work_count = 0
    running_threads: set[int] = set()

    def exercise_lock() -> None:
        nonlocal work_count

        with _locking.named_mutex(os.path.join(tmp_path, "ansible-core")):
            thread_id = threading.current_thread().native_id

            try:
                assert not running_threads

                running_threads.add(thread_id)
                work_count += 1
                time.sleep(0.1)
            finally:
                running_threads.remove(thread_id)

    with ThreadPoolExecutor(max_workers=10) as executor:
        jobs = [executor.submit(exercise_lock) for _idx in range(10)]

        wait(jobs, 5)

        assert all(job.result() is None for job in jobs)
        assert work_count == 10
