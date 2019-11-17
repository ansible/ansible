# -*- coding: utf-8 -*-
# (c) 2018, Jordan Borean <jborean@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pytest

from units.compat.mock import patch, MagicMock
from ansible.plugins.action.win_updates import ActionModule
from ansible.plugins.become.runas import BecomeModule
from ansible.playbook.task import Task


@pytest.fixture()
def test_win_updates():
    task = MagicMock(Task)
    task.args = {}

    connection = MagicMock()
    connection.module_implementation_preferences = ('.ps1', '.exe', '')

    play_context = MagicMock()
    play_context.check_mode = False

    plugin = ActionModule(task, connection, play_context, loader=None, templar=None, shared_loader_obj=None)
    return plugin


class TestWinUpdatesActionPlugin(object):

    INVALID_OPTIONS = (
        (
            {"state": "invalid"},
            False,
            "state must be either installed, searched or downloaded"
        ),
        (
            {"reboot": "nonsense"},
            False,
            "cannot parse reboot as a boolean: The value 'nonsense' is not a "
            "valid boolean."
        ),
        (
            {"reboot_timeout": "string"},
            False,
            "reboot_timeout must be an integer"
        ),
        (
            {"reboot": True},
            True,
            "async is not supported for this task when reboot=yes"
        )
    )

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    # pylint: disable=undefined-variable
    @pytest.mark.parametrize('task_args, async_val, expected',
                             ((t, a, e) for t, a, e in INVALID_OPTIONS))
    def test_invalid_options(self, task_args, async_val, expected):
        task = MagicMock(Task)
        task.args = task_args
        task.async_val = async_val

        connection = MagicMock()
        play_context = MagicMock()
        play_context.check_mode = False

        plugin = ActionModule(task, connection, play_context, loader=None,
                              templar=None, shared_loader_obj=None)
        res = plugin.run()
        assert res['failed']
        assert expected in res['msg']

    def test_exec_with_become(self, test_win_updates):
        test_become = os.urandom(8)

        set_become_mock = MagicMock()
        test_win_updates._connection.become = test_become
        test_win_updates._connection.set_become_plugin = set_become_mock

        with patch('ansible.plugins.action.ActionBase._execute_module', new=MagicMock()):
            test_win_updates._execute_module_with_become('win_updates', {}, {}, True, False)

        # Asserts we don't override the become plugin.
        assert set_become_mock.call_count == 1
        assert set_become_mock.mock_calls[0][1][0] == test_become

    def test_exec_with_become_no_plugin_set(self, test_win_updates):
        set_become_mock = MagicMock()
        test_win_updates._connection.become = None
        test_win_updates._connection.set_become_plugin = set_become_mock

        with patch('ansible.plugins.action.ActionBase._execute_module', new=MagicMock()):
            test_win_updates._execute_module_with_become('win_updates', {}, {}, True, False)

        assert set_become_mock.call_count == 2
        assert isinstance(set_become_mock.mock_calls[0][1][0], BecomeModule)
        assert set_become_mock.mock_calls[0][1][0].name == 'runas'
        assert set_become_mock.mock_calls[0][1][0].get_option('become_user') == 'SYSTEM'
        assert set_become_mock.mock_calls[0][1][0].get_option('become_flags') == ''
        assert set_become_mock.mock_calls[0][1][0].get_option('become_pass') is None
        assert set_become_mock.mock_calls[1][1] == (None,)

    def test_exec_with_become_no_plugin_set_use_task(self, test_win_updates):
        set_become_mock = MagicMock()
        test_win_updates._connection.become = None
        test_win_updates._connection.set_become_plugin = set_become_mock

        with patch('ansible.plugins.action.ActionBase._execute_module', new=MagicMock()):
            test_win_updates._execute_module_with_become('win_updates', {}, {}, True, True)

        assert set_become_mock.call_count == 1
        assert set_become_mock.mock_calls[0][1][0] is None

    def test_module_exec_async_result(self, monkeypatch):
        return_val = {
            "ansible_async_watchdog_pid": 7584,
            "ansible_job_id": "545519115287.9620",
            "changed": True,
            "finished": 0,
            "results_file": r"C:\.ansible_async\545519115287.9620",
            "started": 1
        }
        mock_execute = MagicMock(return_value=return_val)
        monkeypatch.setattr(ActionModule, '_execute_module', mock_execute)

        task = MagicMock(Task)
        task.args = {}
        task.async_val = 10

        connection = MagicMock()
        connection.module_implementation_preferences = ('.ps1', '.exe', '')

        play_context = MagicMock()
        play_context.check_mode = False
        play_context.become = True
        play_context.become_method = 'runas'
        play_context.become_user = 'SYSTEM'

        plugin = ActionModule(task, connection, play_context, loader=None,
                              templar=None, shared_loader_obj=None)
        actual = plugin.run(None, {})

        assert actual.get('failed') is None
        assert actual['ansible_async_watchdog_pid'] == 7584
        assert actual['ansible_job_id'] == "545519115287.9620"
        assert actual['changed'] is True
        assert actual['finished'] == 0
        assert actual['results_file'] == r"C:\.ansible_async\545519115287.9620"
        assert actual['started'] == 1
