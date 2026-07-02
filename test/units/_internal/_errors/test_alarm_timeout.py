from __future__ import annotations

import contextlib
import signal
import time
import typing as t

import pytest

from ansible._internal._errors import _alarm_timeout
from ansible._internal._errors._alarm_timeout import AnsibleTimeoutError

pytestmark = pytest.mark.usefixtures("assert_sigalrm_state")


@pytest.fixture
def assert_sigalrm_state() -> t.Iterator[None]:
    """Fixture to ensure that SIGALRM state is as-expected before and after each test."""
    assert signal.alarm(0) == 0  # disable alarm before resetting the default handler
    assert signal.signal(signal.SIGALRM, signal.SIG_DFL) == signal.SIG_DFL

    try:
        yield
    finally:
        assert signal.alarm(0) == 0
        assert signal.signal(signal.SIGALRM, signal.SIG_DFL) == signal.SIG_DFL


@pytest.mark.parametrize("timeout", (0, 1, None))
def test_alarm_timeout_success(timeout: int | None) -> None:
    """Validate a non-timeout success scenario."""
    ran = False

    with _alarm_timeout.AnsibleTimeoutError.alarm_timeout(timeout):
        time.sleep(0.01)
        ran = True

    assert ran


def test_alarm_timeout_timeout() -> None:
    """Validate a happy-path timeout scenario."""
    ran = False
    timeout_sec = 1

    with pytest.raises(AnsibleTimeoutError) as error:
        with _alarm_timeout.AnsibleTimeoutError.alarm_timeout(timeout_sec):
            time.sleep(timeout_sec + 1)
            ran = True  # pragma: nocover

    assert not ran
    assert error.value.timeout == timeout_sec


@pytest.mark.parametrize("timeout,expected_error_type,expected_error_pattern", (
    (-1, ValueError, "Timeout.*invalid.*between"),
    (100_000_001, ValueError, "Timeout.*invalid.*between"),
    (0.1, TypeError, "requires 'int' argument.*'float'"),
    ("1", TypeError, "requires 'int' argument.*'str'"),
))
def test_alarm_timeout_bad_values(timeout: t.Any, expected_error_type: type[Exception], expected_error_pattern: str) -> None:
    """Validate behavior for invalid inputs."""
    ran = False

    with pytest.raises(expected_error_type, match=expected_error_pattern):
        with _alarm_timeout.AnsibleTimeoutError.alarm_timeout(timeout):
            ran = True  # pragma: nocover

    assert not ran


def test_alarm_timeout_bad_state() -> None:
    """Validate alarm state error handling."""
    def call_it():
        ran = False

        with pytest.raises(RuntimeError, match="existing alarm"):
            with _alarm_timeout.AnsibleTimeoutError.alarm_timeout(1):
                ran = True  # pragma: nocover

        assert not ran

    try:
        # non-default SIGALRM handler present
        signal.signal(signal.SIGALRM, lambda _s, _f: None)
        call_it()
    finally:
        signal.signal(signal.SIGALRM, signal.SIG_DFL)

    try:
        # alarm already set
        signal.alarm(10000)
        call_it()
    finally:
        signal.signal(signal.SIGALRM, signal.SIG_DFL)

    ran_outer = ran_inner = False

    # nested alarm_timeouts
    with pytest.raises(RuntimeError, match="existing alarm"):
        with _alarm_timeout.AnsibleTimeoutError.alarm_timeout(1):
            ran_outer = True

            with _alarm_timeout.AnsibleTimeoutError.alarm_timeout(1):
                ran_inner = True  # pragma: nocover

    assert not ran_inner
    assert ran_outer


def test_alarm_timeout_raise():
    """Ensure that an exception raised in the wrapped scope propagates correctly."""
    with pytest.raises(NotImplementedError):
        with _alarm_timeout.AnsibleTimeoutError.alarm_timeout(1):
            raise NotImplementedError()


def test_alarm_timeout_escape_broad_exception():
    """Ensure that the timeout exception can escape a broad exception handler in the wrapped scope."""
    with pytest.raises(AnsibleTimeoutError):
        with _alarm_timeout.AnsibleTimeoutError.alarm_timeout(1):
            with contextlib.suppress(Exception):
                time.sleep(3)
