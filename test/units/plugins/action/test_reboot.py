# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for the reboot action plugin."""
from __future__ import annotations

import os

import pytest

from ansible.errors import AnsibleConnectionFailure
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
    task.check_mode = False
    task.diff = False
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
