# -*- coding: utf-8 -*-
# (c) 2018, Jordan Borean <jborean@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.compat.tests.mock import patch, MagicMock, mock_open
from ansible.plugins.action.win_updates import ActionModule
from ansible.playbook.task import Task


class TestWinUpdatesActionPlugin(object):

    INVALID_OPTIONS = (
        (
            {"category_names": ["fake category"]},
            False,
            "Unknown category_name fake category, must be one of (Application,"
            "Connectors,CriticalUpdates,DefinitionUpdates,DeveloperKits,"
            "FeaturePacks,Guidance,SecurityUpdates,ServicePacks,Tools,"
            "UpdateRollups,Updates)"
        ),
        (
            {"state": "invalid"},
            False,
            "state must be either installed or searched"
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

    BECOME_OPTIONS = (
        (False, False, "sudo", "root", True, "runas", "SYSTEM"),
        (False, True, "sudo", "root", True, "runas", "SYSTEM"),
        (False, False, "runas", "root", True, "runas", "SYSTEM"),
        (False, False, "sudo", "user", True, "runas", "user"),
        (False, None, "sudo", None, True, "runas", "SYSTEM"),

        # use scheduled task, we shouldn't change anything
        (True, False, "sudo", None, False, "sudo", None),
        (True, True, "runas", "SYSTEM", True, "runas", "SYSTEM"),
    )

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    # pylint: disable=undefined-variable
    @pytest.mark.parametrize('use_task, o_b, o_bmethod, o_buser, e_b, e_bmethod, e_buser',
                             ((u, ob, obm, obu, eb, ebm, ebu)
                              for u, ob, obm, obu, eb, ebm, ebu in BECOME_OPTIONS))
    def test_module_exec_with_become(self, use_task, o_b, o_bmethod, o_buser,
                                     e_b, e_bmethod, e_buser):
        def mock_execute_module(self, **kwargs):
            pc = self._play_context
            return {"become": pc.become, "become_method": pc.become_method,
                    "become_user": pc.become_user}

        task = MagicMock(Task)
        task.args = {}

        connection = MagicMock()
        connection.module_implementation_preferences = ('.ps1', '.exe', '')

        play_context = MagicMock()
        play_context.check_mode = False
        play_context.become = o_b
        play_context.become_method = o_bmethod
        play_context.become_user = o_buser

        plugin = ActionModule(task, connection, play_context, loader=None,
                              templar=None, shared_loader_obj=None)
        with patch('ansible.plugins.action.ActionBase._execute_module',
                   new=mock_execute_module):
            actual = plugin._execute_module_with_become('win_updates', {}, {},
                                                        True, use_task)

        # always make sure we reset back to the defaults
        assert play_context.become == o_b
        assert play_context.become_method == o_bmethod
        assert play_context.become_user == o_buser

        # verify what was set when _execute_module was called
        assert actual['become'] == e_b
        assert actual['become_method'] == e_bmethod
        assert actual['become_user'] == e_buser

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
