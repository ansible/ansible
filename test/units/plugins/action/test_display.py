# Copyright (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for the display action plugin."""
from __future__ import annotations

import os

import pytest

from ansible.errors import AnsibleActionFail
from ansible.playbook.task import Task
from ansible.plugins.action.display import ActionModule as DisplayAction
from ansible.plugins.loader import connection_loader


def _make_plugin(mocker, task_args):
    """Build display action plugin with mocked dependencies."""
    task = mocker.MagicMock(Task)
    task.action = 'display'
    task.args = task_args
    task.async_val = False
    task.check_mode = False
    task.diff = False
    task.get_name = mocker.MagicMock(return_value='Display task')
    play_context = mocker.MagicMock()
    play_context.check_mode = False
    play_context.shell = 'sh'
    import os
    connection = connection_loader.get('local', play_context, os.devnull)
    templar = mocker.MagicMock()
    templar.template = lambda x: x
    return DisplayAction(
        task,
        connection,
        play_context,
        None,
        templar,
        None,
    )


@pytest.mark.parametrize('task_args', [
    {'msg': 'Hello world', 'level': 'display'},
    {'msg': 'Warning message', 'level': 'warning'},
    {'msg': 'Deprecation notice', 'level': 'deprecated'},
    {'msg': 'Verbose v', 'level': 'v'},
    {'msg': 'Verbose vv', 'level': 'vv'},
    {'msg': 'Verbose vvv', 'level': 'vvv'},
    {'msg': 'Verbose vvvv', 'level': 'vvvv'},
    {'msg': 'Only msg (default level)'},
], ids=['display', 'warning', 'deprecated', 'v', 'vv', 'vvv', 'vvvv', 'default_level'])
def test_display_action_returns_result(mocker, task_args):
    """Run action and assert result structure; display methods are called via global Display."""
    level = task_args.get('level', 'display')
    plugin = _make_plugin(mocker, task_args)
    result = plugin.run(task_vars={})
    assert result['changed'] is False
    assert 'msg' in result
    assert result['level'] == level


def test_display_action_invalid_level_fails(mocker):
    """Invalid level raises AnsibleActionFail from validate_argument_spec."""
    plugin = _make_plugin(mocker, {'msg': 'Hi', 'level': 'invalid'})
    with pytest.raises(AnsibleActionFail):
        plugin.run(task_vars={})


def test_display_action_missing_msg_fails(mocker):
    """Missing required msg raises AnsibleActionFail."""
    plugin = _make_plugin(mocker, {'level': 'warning'})
    with pytest.raises(AnsibleActionFail):
        plugin.run(task_vars={})
