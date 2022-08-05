"""Timeout management for tests."""
from __future__ import annotations

import datetime
import functools
import os
import signal
import time
import typing as t

from .io import (
    read_json_file,
)

from .config import (
    CommonConfig,
    TestConfig,
)

from .util import (
    display,
    ApplicationError,
)

from .thread import (
    WrappedThread,
)

from .constants import (
    TIMEOUT_PATH,
)

from .test import (
    TestTimeout,
)


def get_timeout() -> t.Optional[dict[str, t.Any]]:
    """Return details about the currently set timeout, if any, otherwise return None."""
    if not os.path.exists(TIMEOUT_PATH):
        return None

    data = read_json_file(TIMEOUT_PATH)
    data['deadline'] = datetime.datetime.strptime(data['deadline'], '%Y-%m-%dT%H:%M:%SZ')

    return data


def configure_timeout(args: CommonConfig) -> None:
    """Configure the timeout."""
    if isinstance(args, TestConfig):
        configure_test_timeout(args)  # only tests are subject to the timeout


def configure_test_timeout(args: TestConfig) -> None:
    """Configure the test timeout."""
    timeout = get_timeout()

    if not timeout:
        return

    timeout_start = datetime.datetime.utcnow()
    timeout_duration = timeout['duration']
    timeout_deadline = timeout['deadline']
    timeout_remaining = timeout_deadline - timeout_start

    test_timeout = TestTimeout(timeout_duration)

    if timeout_remaining <= datetime.timedelta():
        test_timeout.write(args)

        raise ApplicationError('The %d minute test timeout expired %s ago at %s.' % (
            timeout_duration, timeout_remaining * -1, timeout_deadline))

    display.info('The %d minute test timeout expires in %s at %s.' % (
        timeout_duration, timeout_remaining, timeout_deadline), verbosity=1)

    def timeout_handler(_dummy1, _dummy2):
        """Runs when SIGUSR1 is received."""
        test_timeout.write(args)

        raise ApplicationError('Tests aborted after exceeding the %d minute time limit.' % timeout_duration)

    def timeout_waiter(timeout_seconds: int) -> None:
        """Background thread which will kill the current process if the timeout elapses."""
        time.sleep(timeout_seconds)
        os.kill(os.getpid(), signal.SIGUSR1)

    signal.signal(signal.SIGUSR1, timeout_handler)

    instance = WrappedThread(functools.partial(timeout_waiter, timeout_remaining.seconds))
    instance.daemon = True
    instance.start()
