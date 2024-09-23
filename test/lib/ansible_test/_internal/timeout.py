"""Timeout management for tests."""
from __future__ import annotations

import dataclasses
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
    TimeoutExpiredError,
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


@dataclasses.dataclass(frozen=True)
class TimeoutDetail:
    """Details required to enforce a timeout on test execution."""

    _DEADLINE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'  # format used to maintain backwards compatibility with previous versions of ansible-test

    deadline: datetime.datetime
    duration: int | float  # minutes

    @property
    def remaining(self) -> datetime.timedelta:
        """The amount of time remaining before the timeout occurs. If the timeout has passed, this will be a negative duration."""
        return self.deadline - datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0)

    def to_dict(self) -> dict[str, t.Any]:
        """Return timeout details as a dictionary suitable for JSON serialization."""
        return dict(
            deadline=self.deadline.strftime(self._DEADLINE_FORMAT),
            duration=self.duration,
        )

    @staticmethod
    def from_dict(value: dict[str, t.Any]) -> TimeoutDetail:
        """Return a TimeoutDetail instance using the value previously returned by to_dict."""
        return TimeoutDetail(
            deadline=datetime.datetime.strptime(value['deadline'], TimeoutDetail._DEADLINE_FORMAT).replace(tzinfo=datetime.timezone.utc),
            duration=value['duration'],
        )

    @staticmethod
    def create(duration: int | float) -> TimeoutDetail | None:
        """Return a new TimeoutDetail instance for the specified duration (in minutes), or None if the duration is zero."""
        if not duration:
            return None

        if duration == int(duration):
            duration = int(duration)

        return TimeoutDetail(
            deadline=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0) + datetime.timedelta(seconds=int(duration * 60)),
            duration=duration,
        )


def get_timeout() -> TimeoutDetail | None:
    """Return details about the currently set timeout, if any, otherwise return None."""
    try:
        return TimeoutDetail.from_dict(read_json_file(TIMEOUT_PATH))
    except FileNotFoundError:
        return None


def configure_timeout(args: CommonConfig) -> None:
    """Configure the timeout."""
    if isinstance(args, TestConfig):
        configure_test_timeout(args)  # only tests are subject to the timeout


def configure_test_timeout(args: TestConfig) -> None:
    """Configure the test timeout."""
    timeout = get_timeout()

    if not timeout:
        return

    timeout_remaining = timeout.remaining

    test_timeout = TestTimeout(timeout.duration)

    if timeout_remaining <= datetime.timedelta():
        test_timeout.write(args)

        raise TimeoutExpiredError(f'The {timeout.duration} minute test timeout expired {timeout_remaining * -1} ago at {timeout.deadline}.')

    display.info(f'The {timeout.duration} minute test timeout expires in {timeout_remaining} at {timeout.deadline}.', verbosity=1)

    def timeout_handler(_dummy1: t.Any, _dummy2: t.Any) -> None:
        """Runs when SIGUSR1 is received."""
        test_timeout.write(args)

        raise TimeoutExpiredError(f'Tests aborted after exceeding the {timeout.duration} minute time limit.')

    def timeout_waiter(timeout_seconds: float) -> None:
        """Background thread which will kill the current process if the timeout elapses."""
        time.sleep(timeout_seconds)
        os.kill(os.getpid(), signal.SIGUSR1)

    signal.signal(signal.SIGUSR1, timeout_handler)

    instance = WrappedThread(functools.partial(timeout_waiter, timeout_remaining.total_seconds()))
    instance.daemon = True
    instance.start()
