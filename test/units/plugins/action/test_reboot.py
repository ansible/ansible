# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for the reboot action plugin."""
import os

import pytest

from ansible.errors import AnsibleConnectionFailure
from ansible.playbook.play_context import PlayContext
from ansible.playbook.task import Task
from ansible.plugins.action.reboot import ActionModule as RebootAction
from ansible.plugins.loader import connection_loader


@pytest.fixture
def task_args(request):
    """Return playbook task args."""
    return getattr(request, 'param', {})


@pytest.fixture
def module_task(mocker, task_args):
    """Construct a task object."""
    task = mocker.MagicMock(Task)
    task.action = 'reboot'
    task.args = task_args
    task.async_val = False
    return task


@pytest.fixture
def play_context(mocker):
    """Construct a play context."""
    ctx = mocker.MagicMock()
    ctx.check_mode = False
    ctx.shell = 'sh'
    return ctx


@pytest.fixture
def action_plugin(play_context, module_task):
    """Initialize an action plugin."""
    connection = connection_loader.get('local', play_context, os.devnull)
    loader = None
    templar = None
    shared_loader_obj = None

    return RebootAction(
        module_task,
        connection,
        play_context,
        loader,
        templar,
        shared_loader_obj,
    )


_SENTINEL_REBOOT_COMMAND = '/reboot-command-mock --arg'
_SENTINEL_SHORT_REBOOT_COMMAND = '/reboot-command-mock'
_SENTINEL_TEST_COMMAND = 'cmd-stub'


def _connection_with_options(mocker, **options):
    """Build a connection mock whose get_option()/set_option() behave like a real connection plugin's."""
    connection = mocker.Mock()
    state = dict(options)

    def get_option(name):
        try:
            return state[name]
        except KeyError:
            raise KeyError(name)

    def set_option(name, value):
        state[name] = value

    connection.get_option = mocker.Mock(side_effect=get_option)
    connection.set_option = mocker.Mock(side_effect=set_option)
    return connection


@pytest.mark.parametrize(
    'task_args',
    (
        {
            'reboot_timeout': 5,
            'reboot_command': _SENTINEL_REBOOT_COMMAND,
            'test_command': _SENTINEL_TEST_COMMAND,
        },
        {
            'reboot_timeout': 5,
            'reboot_command': _SENTINEL_SHORT_REBOOT_COMMAND,
            'test_command': _SENTINEL_TEST_COMMAND,
        },
    ),
    ids=('reboot command with spaces', 'reboot command without spaces'),
    indirect=('task_args', ),
)
def test_reboot_command(action_plugin, mocker, monkeypatch, task_args):
    """Check that the reboot command gets called and reboot verified."""
    def _patched_low_level_execute_command(cmd, *args, **kwargs):
        return {
            _SENTINEL_TEST_COMMAND: {
                'rc': 0,
                'stderr': '<test command stub-stderr>',
                'stdout': '<test command stub-stdout>',
            },
            _SENTINEL_REBOOT_COMMAND: {
                'rc': 0,
                'stderr': '<reboot command stub-stderr>',
                'stdout': '<reboot command stub-stdout>',
            },
            f'{_SENTINEL_SHORT_REBOOT_COMMAND} ': {  # no args is concatenated
                'rc': 0,
                'stderr': '<short reboot command stub-stderr>',
                'stdout': '<short reboot command stub-stdout>',
            },
        }[cmd]

    monkeypatch.setattr(
        action_plugin,
        '_low_level_execute_command',
        _patched_low_level_execute_command,
    )

    action_plugin._connection = mocker.Mock()

    monkeypatch.setattr(action_plugin, 'check_boot_time', lambda *_a, **_kw: 5)
    monkeypatch.setattr(action_plugin, 'get_distribution', mocker.MagicMock())
    monkeypatch.setattr(action_plugin, 'get_system_boot_time', lambda d: 0)

    low_level_cmd_spy = mocker.spy(action_plugin, '_low_level_execute_command')

    action_result = action_plugin.run()

    assert low_level_cmd_spy.called

    expected_reboot_command = (
        task_args['reboot_command'] if ' ' in task_args['reboot_command']
        else f'{task_args["reboot_command"] !s} '
    )
    low_level_cmd_spy.assert_any_call(expected_reboot_command, sudoable=True)
    low_level_cmd_spy.assert_any_call(task_args['test_command'], sudoable=True)

    assert low_level_cmd_spy.call_count == 2
    assert low_level_cmd_spy.spy_return == {
        'rc': 0,
        'stderr': '<test command stub-stderr>',
        'stdout': '<test command stub-stdout>',
    }
    assert low_level_cmd_spy.spy_exception is None

    assert 'failed' not in action_result
    assert action_result == {'rebooted': True, 'changed': True, 'elapsed': 0}


@pytest.mark.parametrize(
    'task_args',
    (
        {
            'reboot_timeout': 5,
            'reboot_command': _SENTINEL_REBOOT_COMMAND,
            'test_command': _SENTINEL_TEST_COMMAND,
        },
    ),
    ids=('reboot command with spaces', ),
    indirect=('task_args', ),
)
def test_reboot_command_connection_fail(action_plugin, mocker, monkeypatch, task_args):
    """Check that the reboot command gets called and reboot verified."""
    def _patched_low_level_execute_command(cmd, *args, **kwargs):
        if cmd == _SENTINEL_REBOOT_COMMAND:
            raise AnsibleConnectionFailure('Fake connection drop')
        return {
            _SENTINEL_TEST_COMMAND: {
                'rc': 0,
                'stderr': '<test command stub-stderr>',
                'stdout': '<test command stub-stdout>',
            },
        }[cmd]

    monkeypatch.setattr(
        action_plugin,
        '_low_level_execute_command',
        _patched_low_level_execute_command,
    )

    action_plugin._connection = mocker.Mock()

    monkeypatch.setattr(action_plugin, 'check_boot_time', lambda *_a, **_kw: 5)
    monkeypatch.setattr(action_plugin, 'get_distribution', mocker.MagicMock())
    monkeypatch.setattr(action_plugin, 'get_system_boot_time', lambda d: 0)

    low_level_cmd_spy = mocker.spy(action_plugin, '_low_level_execute_command')

    action_result = action_plugin.run()

    assert low_level_cmd_spy.called

    low_level_cmd_spy.assert_any_call(
        task_args['reboot_command'], sudoable=True,
    )
    low_level_cmd_spy.assert_any_call(task_args['test_command'], sudoable=True)

    assert low_level_cmd_spy.call_count == 2
    assert low_level_cmd_spy.spy_return == {
        'rc': 0,
        'stderr': '<test command stub-stderr>',
        'stdout': '<test command stub-stdout>',
    }

    assert 'failed' not in action_result
    assert action_result == {'rebooted': True, 'changed': True, 'elapsed': 0}


@pytest.mark.parametrize(
    'task_args',
    (
        {
            'reboot_timeout': 5,
            'reboot_command': _SENTINEL_REBOOT_COMMAND,
            'test_command': _SENTINEL_TEST_COMMAND,
        },
    ),
    ids=('reboot command with spaces', ),
    indirect=('task_args', ),
)
def test_reboot_command_disables_reconnection_retries_during_reboot(action_plugin, mocker, monkeypatch, task_args):
    """reconnection_retries must be 0 only while the reboot command runs, then restored."""
    original_retries = 3
    connection = _connection_with_options(mocker, reconnection_retries=original_retries)
    action_plugin._connection = connection

    retries_during_reboot_command = []

    def _patched_low_level_execute_command(cmd, *args, **kwargs):
        if cmd == _SENTINEL_REBOOT_COMMAND:
            retries_during_reboot_command.append(connection.get_option('reconnection_retries'))
            return {
                'rc': 0,
                'stderr': '<reboot command stub-stderr>',
                'stdout': '<reboot command stub-stdout>',
            }
        return {
            _SENTINEL_TEST_COMMAND: {
                'rc': 0,
                'stderr': '<test command stub-stderr>',
                'stdout': '<test command stub-stdout>',
            },
        }[cmd]

    monkeypatch.setattr(
        action_plugin,
        '_low_level_execute_command',
        _patched_low_level_execute_command,
    )

    monkeypatch.setattr(action_plugin, 'check_boot_time', lambda *_a, **_kw: 5)
    monkeypatch.setattr(action_plugin, 'get_distribution', mocker.MagicMock())
    monkeypatch.setattr(action_plugin, 'get_system_boot_time', lambda d: 0)

    low_level_cmd_spy = mocker.spy(action_plugin, '_low_level_execute_command')

    # A: before the reboot command is sent, the original value is untouched.
    assert connection.get_option('reconnection_retries') == original_retries

    action_result = action_plugin.run()

    # B: while the reboot command was executing, reconnection_retries was forced to 0.
    assert retries_during_reboot_command == [0]

    # C: after a successful reboot command, the original value is restored.
    assert connection.get_option('reconnection_retries') == original_retries

    # G: the reboot command itself was only sent once.
    reboot_command_calls = [
        call for call in low_level_cmd_spy.call_args_list
        if call.args and call.args[0] == _SENTINEL_REBOOT_COMMAND
    ]
    assert len(reboot_command_calls) == 1

    assert 'failed' not in action_result
    assert action_result == {'rebooted': True, 'changed': True, 'elapsed': 0}


@pytest.mark.parametrize(
    'task_args',
    (
        {
            'reboot_timeout': 5,
            'reboot_command': _SENTINEL_REBOOT_COMMAND,
            'test_command': _SENTINEL_TEST_COMMAND,
        },
    ),
    ids=('reboot command with spaces', ),
    indirect=('task_args', ),
)
def test_reboot_command_connection_fail_restores_reconnection_retries(action_plugin, mocker, monkeypatch, task_args):
    """reconnection_retries is restored even when the reboot command raises AnsibleConnectionFailure (E)."""
    original_retries = 5
    connection = _connection_with_options(mocker, reconnection_retries=original_retries)
    action_plugin._connection = connection

    retries_during_reboot_command = []

    def _patched_low_level_execute_command(cmd, *args, **kwargs):
        if cmd == _SENTINEL_REBOOT_COMMAND:
            retries_during_reboot_command.append(connection.get_option('reconnection_retries'))
            raise AnsibleConnectionFailure('Fake connection drop')
        return {
            _SENTINEL_TEST_COMMAND: {
                'rc': 0,
                'stderr': '<test command stub-stderr>',
                'stdout': '<test command stub-stdout>',
            },
        }[cmd]

    monkeypatch.setattr(
        action_plugin,
        '_low_level_execute_command',
        _patched_low_level_execute_command,
    )

    monkeypatch.setattr(action_plugin, 'check_boot_time', lambda *_a, **_kw: 5)
    monkeypatch.setattr(action_plugin, 'get_distribution', mocker.MagicMock())
    monkeypatch.setattr(action_plugin, 'get_system_boot_time', lambda d: 0)

    low_level_cmd_spy = mocker.spy(action_plugin, '_low_level_execute_command')

    action_result = action_plugin.run()

    # B: reconnection_retries was 0 for the single (failed) attempt at sending the reboot command.
    assert retries_during_reboot_command == [0]

    # D: even though the reboot command raised, the original value is restored afterwards.
    assert connection.get_option('reconnection_retries') == original_retries

    # G: the reboot command was attempted only once - it was not retried by the reboot action itself.
    reboot_command_calls = [
        call for call in low_level_cmd_spy.call_args_list
        if call.args and call.args[0] == _SENTINEL_REBOOT_COMMAND
    ]
    assert len(reboot_command_calls) == 1

    # E: existing AnsibleConnectionFailure handling still treats this as a successful reboot.
    assert 'failed' not in action_result
    assert action_result == {'rebooted': True, 'changed': True, 'elapsed': 0}


@pytest.mark.parametrize(
    'task_args',
    (
        {
            'reboot_timeout': 5,
            'reboot_command': _SENTINEL_REBOOT_COMMAND,
            'test_command': _SENTINEL_TEST_COMMAND,
        },
    ),
    ids=('reboot command with spaces', ),
    indirect=('task_args', ),
)
def test_reboot_command_reconnection_retries_option_unsupported(action_plugin, mocker, monkeypatch, task_args):
    """Connection plugins without a reconnection_retries option (e.g. local) must not raise."""
    # `action_plugin` is backed by a real 'local' connection plugin instance, which does not
    # declare a 'reconnection_retries' option, so get_option() raises KeyError for it.
    monkeypatch.setattr(action_plugin, '_low_level_execute_command', lambda *_a, **_kw: {
        'rc': 0,
        'stderr': '',
        'stdout': '',
    })

    set_option_spy = mocker.spy(action_plugin._connection, 'set_option')

    result = action_plugin.perform_reboot(task_vars={}, distribution={})

    assert result['failed'] is False
    # No attempt is made to override an option the connection plugin doesn't declare.
    set_option_spy.assert_not_called()


def test_reboot_command_real_ssh_retry_prevents_duplicate_command(action_plugin, monkeypatch):
    """Regression test for the duplicate-reboot bug using a real ssh connection plugin instance.

    Unlike the mock-based tests above, this does NOT stub out _low_level_execute_command(), so
    the call travels through the real ssh Connection.exec_command() -> Connection._run() (the
    actual method decorated by ssh.py's @_ssh_retry) -> _handle_error(). Only
    Connection._bare_run() is mocked, since that is the point where an actual `ssh` subprocess
    would be spawned.
    """
    play_context = PlayContext()
    connection = connection_loader.get('ssh', play_context, os.devnull)

    # A user with ansible_ssh_retries/ANSIBLE_SSH_RETRIES > 0 is exactly the condition that
    # makes the original bug reachable (the ssh connection plugin's default is 0 retries).
    original_retries = 3
    connection.set_option('reconnection_retries', original_retries)
    action_plugin._connection = connection
    action_plugin._task.args = {'reboot_command': _SENTINEL_REBOOT_COMMAND}

    retries_observed_by_bare_run = []

    def _fake_bare_run(cmd, in_data, sudoable=True, checkrc=True):
        # Simulate the real failure mode: ssh exits 255 because the host severed the
        # connection as it began shutting down, not because ssh never reached the host.
        retries_observed_by_bare_run.append(connection.get_option('reconnection_retries'))
        return (255, b'', b'Shared connection to host closed.\r\n')

    monkeypatch.setattr(connection, '_bare_run', _fake_bare_run)

    result = action_plugin.perform_reboot(task_vars={}, distribution={})

    # The real ssh transport was invoked exactly once, with reconnection_retries forced to 0
    # at that moment - so ssh.py's real retry loop has no attempts left and cannot resend the
    # command, even though _bare_run keeps returning rc=255.
    assert retries_observed_by_bare_run == [0]

    # The original value is restored on the real connection object afterwards.
    assert connection.get_option('reconnection_retries') == original_retries

    # Existing behavior is unchanged: a dropped connection during reboot is still treated as a
    # successful reboot, not a task failure.
    assert result['failed'] is False


def test_reboot_connection_local(action_plugin, module_task):
    """Verify that using local connection doesn't let reboot happen."""
    expected_message = ' '.join(
        (
            'Running', module_task.action,
            'with local connection would reboot the control node.',
        ),
    )
    expected_action_result = {
        'changed': False,
        'elapsed': 0,
        'failed': True,
        'msg': expected_message,
        'rebooted': False,
    }

    action_result = action_plugin.run()

    assert action_result == expected_action_result
