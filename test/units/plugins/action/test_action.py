#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2015, Florian Apolloner <florian@apolloner.eu>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock, Mock
from ansible.playbook.play_context import PlayContext
from ansible.plugins.action import ActionBase



class DerivedActionBase(ActionBase):
    TRANSFERS_FILES = False
    def run(self, tmp=None, task_vars=None):
        # We're not testing the plugin run() method, just the helper
        # methods ActionBase defines
        return super(DerivedActionBase, self).run(tmp=tmp, task_vars=task_vars)

class TestActionBase(unittest.TestCase):

    class DerivedActionBase(ActionBase):
        def run(self, tmp=None, task_vars=None):
            # We're not testing the plugin run() method, just the helper
            # methods ActionBase defines
            return dict()

    def test_action_base__early_needs_tmp_path(self):
        # create our fake task
        mock_task = MagicMock()

        # create a mock connection, so we don't actually try and connect to things
        mock_connection = MagicMock()

        # we're using a real play context here
        play_context = PlayContext()

        # our test class
        action_base = DerivedActionBase(
            task=mock_task,
            connection=mock_connection,
            play_context=play_context,
            loader=None,
            templar=None,
            shared_loader_obj=None,
        )

        self.assertFalse(action_base._early_needs_tmp_path())

        action_base.TRANSFERS_FILES = True
        self.assertTrue(action_base._early_needs_tmp_path())

    def test_action_base__late_needs_tmp_path(self):
        # create our fake task
        mock_task = MagicMock()

        # create a mock connection, so we don't actually try and connect to things
        mock_connection = MagicMock()

        # we're using a real play context here
        play_context = PlayContext()

        # our test class
        action_base = DerivedActionBase(
            task=mock_task,
            connection=mock_connection,
            play_context=play_context,
            loader=None,
            templar=None,
            shared_loader_obj=None,
        )

        # assert no temp path is required because tmp is set
        self.assertFalse(action_base._late_needs_tmp_path("/tmp/foo", "new"))

        # assert no temp path is required when using a new-style module
        # with pipelining supported and enabled with no become method
        mock_connection.has_pipelining = True
        play_context.pipelining = True
        play_context.become_method = None
        self.assertFalse(action_base._late_needs_tmp_path(None, "new"))

        # assert a temp path is required for each of the following:
        # the module style is not 'new'
        mock_connection.has_pipelining = True
        play_context.pipelining = True
        play_context.become_method = None
        self.assertTrue(action_base._late_needs_tmp_path(None, "old"))
        # connection plugin does not support pipelining
        mock_connection.has_pipelining = False
        play_context.pipelining = True
        play_context.become_method = None
        self.assertTrue(action_base._late_needs_tmp_path(None, "new"))
        # pipelining is disabled via the play context settings
        mock_connection.has_pipelining = True
        play_context.pipelining = False
        play_context.become_method = None
        self.assertTrue(action_base._late_needs_tmp_path(None, "new"))
        # keep remote files is enabled
        # FIXME: implement
        # the become method is 'su'
        mock_connection.has_pipelining = True
        play_context.pipelining = True
        play_context.become_method = 'su'
        self.assertTrue(action_base._late_needs_tmp_path(None, "new"))

    def test_action_base__make_tmp_path(self):
        # create our fake task
        mock_task = MagicMock()

        # create a mock connection, so we don't actually try and connect to things
        mock_connection = MagicMock()
        mock_connection.transport = 'ssh'
        mock_connection._shell.mkdtemp.return_value = 'mkdir command'
        mock_connection._shell.join_path.side_effect = os.path.join

        # we're using a real play context here
        play_context = PlayContext()
        play_context.become = True
        play_context.become_user = 'foo'

        # our test class
        action_base = DerivedActionBase(
            task=mock_task,
            connection=mock_connection,
            play_context=play_context,
            loader=None,
            templar=None,
            shared_loader_obj=None,
        )

        action_base._low_level_execute_command = MagicMock()
        action_base._low_level_execute_command.return_value = dict(rc=0, stdout='/some/path')
        self.assertEqual(action_base._make_tmp_path(), '/some/path/')

        # empty path fails
        action_base._low_level_execute_command.return_value = dict(rc=0, stdout='')
        self.assertRaises(AnsibleError, action_base._make_tmp_path)

        # authentication failure
        action_base._low_level_execute_command.return_value = dict(rc=5, stdout='')
        self.assertRaises(AnsibleError, action_base._make_tmp_path)

        # ssh error
        action_base._low_level_execute_command.return_value = dict(rc=255, stdout='', stderr='')
        self.assertRaises(AnsibleError, action_base._make_tmp_path)
        play_context.verbosity = 5
        self.assertRaises(AnsibleError, action_base._make_tmp_path)

        # general error
        action_base._low_level_execute_command.return_value = dict(rc=1, stdout='some stuff here', stderr='')
        self.assertRaises(AnsibleError, action_base._make_tmp_path)
        action_base._low_level_execute_command.return_value = dict(rc=1, stdout='some stuff here', stderr='No space left on device')
        self.assertRaises(AnsibleError, action_base._make_tmp_path)

    def test_action_base__remove_tmp_path(self):
        # create our fake task
        mock_task = MagicMock()

        # create a mock connection, so we don't actually try and connect to things
        mock_connection = MagicMock()
        mock_connection._shell.remove.return_value = 'rm some stuff'

        # we're using a real play context here
        play_context = PlayContext()

        # our test class
        action_base = DerivedActionBase(
            task=mock_task,
            connection=mock_connection,
            play_context=play_context,
            loader=None,
            templar=None,
            shared_loader_obj=None,
        )

        action_base._low_level_execute_command = MagicMock()
        # these don't really return anything or raise errors, so
        # we're pretty much calling these for coverage right now
        action_base._remove_tmp_path('/bad/path/dont/remove')
        action_base._remove_tmp_path('/good/path/to/ansible-tmp-thing')

    @patch('os.unlink')
    @patch('os.fdopen')
    @patch('tempfile.mkstemp')
    def test_action_base__transfer_data(self, mock_mkstemp, mock_fdopen, mock_unlink):
        # create our fake task
        mock_task = MagicMock()

        # create a mock connection, so we don't actually try and connect to things
        mock_connection = MagicMock()
        mock_connection.put_file.return_value = None

        # we're using a real play context here
        play_context = PlayContext()

        # our test class
        action_base = DerivedActionBase(
            task=mock_task,
            connection=mock_connection,
            play_context=play_context,
            loader=None,
            templar=None,
            shared_loader_obj=None,
        )

        mock_afd = MagicMock()
        mock_afile = MagicMock()
        mock_mkstemp.return_value = (mock_afd, mock_afile)

        mock_unlink.return_value = None

        mock_afo = MagicMock()
        mock_afo.write.return_value = None
        mock_afo.flush.return_value = None
        mock_afo.close.return_value = None
        mock_fdopen.return_value = mock_afo

        self.assertEqual(action_base._transfer_data('/path/to/remote/file', 'some data'), '/path/to/remote/file')
        self.assertEqual(action_base._transfer_data('/path/to/remote/file', 'some mixed data: fö〩'), '/path/to/remote/file')
        self.assertEqual(action_base._transfer_data('/path/to/remote/file', dict(some_key=u'some value')), '/path/to/remote/file')
        self.assertEqual(action_base._transfer_data('/path/to/remote/file', dict(some_key=u'fö〩')), '/path/to/remote/file')

        mock_afo.write.side_effect = Exception()
        self.assertRaises(AnsibleError, action_base._transfer_data, '/path/to/remote/file', '')

    def test_action_base__execute_remote_stat(self):
        # create our fake task
        mock_task = MagicMock()

        # create a mock connection, so we don't actually try and connect to things
        mock_connection = MagicMock()

        # we're using a real play context here
        play_context = PlayContext()

        # our test class
        action_base = DerivedActionBase(
            task=mock_task,
            connection=mock_connection,
            play_context=play_context,
            loader=None,
            templar=None,
            shared_loader_obj=None,
        )

        action_base._execute_module = MagicMock()

        # test normal case
        action_base._execute_module.return_value = dict(stat=dict(checksum='1111111111111111111111111111111111', exists=True))
        res = action_base._execute_remote_stat(path='/path/to/file', all_vars=dict(), follow=False)
        self.assertEqual(res['checksum'], '1111111111111111111111111111111111')

        # test does not exist
        action_base._execute_module.return_value = dict(stat=dict(exists=False))
        res = action_base._execute_remote_stat(path='/path/to/file', all_vars=dict(), follow=False)
        self.assertFalse(res['exists'])
        self.assertEqual(res['checksum'], '1')

        # test no checksum in result from _execute_module
        action_base._execute_module.return_value = dict(stat=dict(exists=True))
        res = action_base._execute_remote_stat(path='/path/to/file', all_vars=dict(), follow=False)
        self.assertTrue(res['exists'])
        self.assertEqual(res['checksum'], '')

        # test stat call failed
        action_base._execute_module.return_value = dict(failed=True, msg="because I said so")
        self.assertRaises(AnsibleError, action_base._execute_remote_stat, path='/path/to/file', all_vars=dict(), follow=False)

    def test_action_base__execute_module(self):
        # create our fake task
        mock_task = MagicMock()
        mock_task.action = 'copy'
        mock_task.args = dict(a=1, b=2, c=3)

        # create a mock connection, so we don't actually try and connect to things
        def build_module_command(env_string, shebang, cmd, arg_path=None, rm_tmp=None):
            to_run = [env_string, cmd]
            if arg_path:
                to_run.append(arg_path)
            if rm_tmp:
                to_run.append(rm_tmp)
            return " ".join(to_run)

        mock_connection = MagicMock()
        mock_connection.build_module_command.side_effect = build_module_command
        mock_connection._shell.join_path.side_effect = os.path.join

        # we're using a real play context here
        play_context = PlayContext()

        # our test class
        action_base = DerivedActionBase(
            task=mock_task,
            connection=mock_connection,
            play_context=play_context,
            loader=None,
            templar=None,
            shared_loader_obj=None,
        )

        # fake a lot of methods as we test those elsewhere
        action_base._configure_module = MagicMock()
        action_base._supports_check_mode = MagicMock()
        action_base._late_needs_tmp_path = MagicMock()
        action_base._make_tmp_path = MagicMock()
        action_base._transfer_data = MagicMock()
        action_base._compute_environment_string = MagicMock()
        action_base._remote_chmod = MagicMock()
        action_base._low_level_execute_command = MagicMock()

        action_base._configure_module.return_value = ('new', '#!/usr/bin/python', 'this is the module data')
        action_base._late_needs_tmp_path.return_value = False
        action_base._compute_environment_string.return_value = ''
        action_base._connection.has_pipelining = True
        action_base._low_level_execute_command.return_value = dict(stdout='{"rc": 0, "stdout": "ok"}')
        self.assertEqual(action_base._execute_module(module_name=None, module_args=None), dict(rc=0, stdout="ok", stdout_lines=['ok']))
        self.assertEqual(action_base._execute_module(module_name='foo', module_args=dict(z=9, y=8, x=7), task_vars=dict(a=1)), dict(rc=0, stdout="ok", stdout_lines=['ok']))

        # test with needing/removing a remote tmp path
        action_base._configure_module.return_value = ('old', '#!/usr/bin/python', 'this is the module data')
        action_base._late_needs_tmp_path.return_value = True
        action_base._make_tmp_path.return_value = '/the/tmp/path'
        self.assertEqual(action_base._execute_module(), dict(rc=0, stdout="ok", stdout_lines=['ok']))

        action_base._configure_module.return_value = ('non_native_want_json', '#!/usr/bin/python', 'this is the module data')
        self.assertEqual(action_base._execute_module(), dict(rc=0, stdout="ok", stdout_lines=['ok']))

        play_context.become = True
        play_context.become_user = 'foo'
        self.assertEqual(action_base._execute_module(), dict(rc=0, stdout="ok", stdout_lines=['ok']))

        # test an invalid shebang return
        action_base._configure_module.return_value = ('new', '', 'this is the module data')
        action_base._late_needs_tmp_path.return_value = False
        self.assertRaises(AnsibleError, action_base._execute_module)

        # test with check mode enabled, once with support for check
        # mode and once with support disabled to raise an error
        play_context.check_mode = True
        action_base._configure_module.return_value = ('new', '#!/usr/bin/python', 'this is the module data')
        self.assertEqual(action_base._execute_module(), dict(rc=0, stdout="ok", stdout_lines=['ok']))
        action_base._supports_check_mode = False
        self.assertRaises(AnsibleError, action_base._execute_module)

    def test_action_base_sudo_only_if_user_differs(self):
        play_context = PlayContext()
        action_base = self.DerivedActionBase(None, None, play_context, None, None, None)
        action_base._connection = Mock(exec_command=Mock(return_value=(0, '', '')))

        play_context.become = True
        play_context.become_user = play_context.remote_user = 'root'
        play_context.make_become_cmd = Mock(return_value='CMD')

        action_base._low_level_execute_command('ECHO', sudoable=True)
        play_context.make_become_cmd.assert_not_called()

        play_context.remote_user = 'apo'
        action_base._low_level_execute_command('ECHO', sudoable=True)
        play_context.make_become_cmd.assert_called_once_with("ECHO", executable='/bin/sh')

        play_context.make_become_cmd.reset_mock()

        become_allow_same_user = C.BECOME_ALLOW_SAME_USER
        C.BECOME_ALLOW_SAME_USER = True
        try:
            play_context.remote_user = 'root'
            action_base._low_level_execute_command('ECHO SAME', sudoable=True)
            play_context.make_become_cmd.assert_called_once_with("ECHO SAME", executable='/bin/sh')
        finally:
            C.BECOME_ALLOW_SAME_USER = become_allow_same_user
