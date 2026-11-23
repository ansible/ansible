# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for the wait_for_connection action plugin."""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from ansible.playbook.task import Task
from ansible.plugins.action.wait_for_connection import ActionModule, TimedOutException


class FakeClock:
    """A monotonic clock that advances only when the plugin sleeps."""

    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class DriftingClock(FakeClock):
    """A clock that advances a little on every reading, like a real one."""

    def monotonic(self):
        self.now += 0.001
        return self.now


@pytest.fixture
def action_plugin():
    """Return the action plugin without running its constructor."""
    return ActionModule.__new__(ActionModule)


@pytest.mark.parametrize(
    'timeout, connect_timeout, expected',
    [
        (1, 1, [1]),
        (3, 1, [1, 1]),
        (7, 4, [4, 2]),
    ],
)
def test_attempts_use_whole_seconds(action_plugin, monkeypatch, timeout, connect_timeout, expected):
    """Each attempt is capped by connect_timeout and by the whole seconds left."""
    clock = DriftingClock()
    monkeypatch.setattr(time, 'monotonic', clock.monotonic)
    monkeypatch.setattr(time, 'sleep', clock.sleep)

    attempts = []

    def what(attempt_timeout):
        attempts.append(attempt_timeout)
        clock.now += attempt_timeout + 0.01  # a connection attempt overshoots slightly
        raise RuntimeError('not reachable')

    with pytest.raises(TimedOutException, match='not reachable'):
        action_plugin.do_until_success_or_timeout(
            what, timeout=timeout, connect_timeout=connect_timeout, what_desc='test', sleep=1,
        )

    assert attempts == expected
    # A failed wait reaches the deadline and never runs a whole second past it.
    assert timeout <= clock.now < timeout + 1


def test_attempt_uses_the_whole_time_left(action_plugin, monkeypatch):
    """A host that answers late in the window is not cut off a second early."""
    clock = DriftingClock()
    monkeypatch.setattr(time, 'monotonic', clock.monotonic)
    monkeypatch.setattr(time, 'sleep', clock.sleep)

    attempts = []

    def what(attempt_timeout):
        attempts.append(attempt_timeout)
        clock.now += attempt_timeout

        if attempt_timeout < 2.4:
            # Too short to reach a host that answers at 2.4 seconds.
            raise RuntimeError('not reachable yet')

    action_plugin.do_until_success_or_timeout(
        what, timeout=3, connect_timeout=5, what_desc='test', sleep=1,
    )

    assert attempts == [3]


def test_sleep_is_capped_to_remaining_time(action_plugin, monkeypatch):
    """The sleep between attempts does not run past the overall deadline."""
    clock = FakeClock()
    monkeypatch.setattr(time, 'monotonic', clock.monotonic)
    monkeypatch.setattr(time, 'sleep', clock.sleep)

    attempts = []

    def what(attempt_timeout):
        attempts.append(attempt_timeout)
        clock.now += attempt_timeout
        raise RuntimeError('not reachable')

    with pytest.raises(TimedOutException):
        action_plugin.do_until_success_or_timeout(
            what, timeout=3, connect_timeout=1, what_desc='test', sleep=10,
        )

    assert attempts == [1]
    assert clock.now == 3


@pytest.mark.parametrize(
    'timeout, connect_timeout',
    [
        (10, 0),
        (0, 1),
    ],
)
def test_invalid_limits_make_no_attempt(action_plugin, monkeypatch, timeout, connect_timeout):
    """A non-positive timeout or connect_timeout fails before any attempt."""
    clock = FakeClock()
    monkeypatch.setattr(time, 'monotonic', clock.monotonic)
    monkeypatch.setattr(time, 'sleep', clock.sleep)

    attempts = []

    def what(attempt_timeout):
        attempts.append(attempt_timeout)

    with pytest.raises(TimedOutException, match='timed out waiting for test'):
        action_plugin.do_until_success_or_timeout(
            what, timeout=timeout, connect_timeout=connect_timeout, what_desc='test',
        )

    assert attempts == []


class FakeConnection:
    """A connection plugin that records option changes."""

    def __init__(self):
        self.options = {'timeout': 10, 'reconnection_retries': 3}
        self.set_calls = []
        self._shell = SimpleNamespace(tmpdir='/tmp')

    def has_option(self, option):
        return option in self.options

    def get_option(self, option):
        return self.options[option]

    def set_option(self, option, value):
        self.set_calls.append((option, value))
        self.options[option] = value

    def reset(self):
        pass


def test_run_sets_and_restores_connection_options(mocker):
    """Set per-attempt options once and restore the originals afterwards."""
    task = mocker.MagicMock(Task)
    task.action = 'wait_for_connection'
    task.args = {'sleep': 0}
    task.async_val = False
    task.check_mode = False

    connection = FakeConnection()
    action_plugin = ActionModule(task, connection, mocker.MagicMock(), None, None)
    mocker.patch.object(action_plugin, '_execute_module', side_effect=[RuntimeError('not yet'), {'ping': 'pong'}])
    mocker.patch.object(action_plugin, '_remove_tmp_path', return_value=None)

    result = action_plugin.run(task_vars={})

    assert 'failed' not in result
    assert connection.set_calls == [
        ('reconnection_retries', 0),
        ('timeout', 5),
        ('timeout', 5),
        ('timeout', 10),
        ('reconnection_retries', 3),
    ]


def test_run_restores_connection_options_after_timeout(mocker, monkeypatch):
    """The finally block restores the options even when the wait fails."""
    clock = FakeClock()
    monkeypatch.setattr(time, 'monotonic', clock.monotonic)
    monkeypatch.setattr(time, 'sleep', clock.sleep)

    task = mocker.MagicMock(Task)
    task.action = 'wait_for_connection'
    task.args = {'timeout': 1, 'connect_timeout': 1, 'sleep': 1}
    task.async_val = False
    task.check_mode = False

    connection = FakeConnection()
    action_plugin = ActionModule(task, connection, mocker.MagicMock(), None, None)
    mocker.patch.object(action_plugin, '_execute_module', side_effect=RuntimeError('not yet'))
    mocker.patch.object(action_plugin, '_remove_tmp_path', return_value=None)

    result = action_plugin.run(task_vars={})

    assert result['failed'] is True
    assert connection.options == {'timeout': 10, 'reconnection_retries': 3}


def test_run_leaves_connections_without_timeout_options_alone(mocker):
    """local and WinRM expose neither timeout nor reconnection_retries."""
    task = mocker.MagicMock(Task)
    task.action = 'wait_for_connection'
    task.args = {}
    task.async_val = False
    task.check_mode = False

    connection = FakeConnection()
    connection.options = {}
    action_plugin = ActionModule(task, connection, mocker.MagicMock(), None, None)
    mocker.patch.object(action_plugin, '_execute_module', return_value={'ping': 'pong'})
    mocker.patch.object(action_plugin, '_remove_tmp_path', return_value=None)

    result = action_plugin.run(task_vars={})

    assert 'failed' not in result
    assert connection.set_calls == []
