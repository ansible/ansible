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
import re

from ansible import constants as C
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock, mock_open

from ansible.errors import AnsibleError
from ansible.module_utils.six import text_type
from ansible.module_utils.six.moves import shlex_quote, builtins
from ansible.module_utils._text import to_bytes
from ansible.playbook.play_context import PlayContext
from ansible.plugins.action import ActionBase
from ansible.template import Templar
from ansible.vars.clean import clean_facts

from units.mock.loader import DictDataLoader


python_module_replacers = br"""
#!/usr/bin/python

#ANSIBLE_VERSION = "<<ANSIBLE_VERSION>>"
#MODULE_COMPLEX_ARGS = "<<INCLUDE_ANSIBLE_MODULE_COMPLEX_ARGS>>"
#SELINUX_SPECIAL_FS="<<SELINUX_SPECIAL_FILESYSTEMS>>"

test = u'Toshio \u304f\u3089\u3068\u307f'
from ansible.module_utils.basic import *
"""

powershell_module_replacers = b"""
WINDOWS_ARGS = "<<INCLUDE_ANSIBLE_MODULE_JSON_ARGS>>"
# POWERSHELL_COMMON
"""


class DerivedActionBase(ActionBase):
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        # We're not testing the plugin run() method, just the helper
        # methods ActionBase defines
        return super(DerivedActionBase, self).run(tmp=tmp, task_vars=task_vars)


class TestActionBase(unittest.TestCase):

    def test_action_base_run(self):
        mock_task = MagicMock()
        mock_task.action = "foo"
        mock_task.args = dict(a=1, b=2, c=3)

        mock_connection = MagicMock()

        play_context = PlayContext()

        mock_task.async_val = None
        action_base = DerivedActionBase(mock_task, mock_connection, play_context, None, None, None)
        results = action_base.run()
        self.assertEqual(results, dict())

        mock_task.async_val = 0
        action_base = DerivedActionBase(mock_task, mock_connection, play_context, None, None, None)
        results = action_base.run()
        self.assertEqual(results, {})

    def test_action_base__configure_module(self):
        fake_loader = DictDataLoader({
        })

        # create our fake task
        mock_task = MagicMock()
        mock_task.action = "copy"
        mock_task.async_val = 0

        # create a mock connection, so we don't actually try and connect to things
        mock_connection = MagicMock()

        # create a mock shared loader object
        def mock_find_plugin(name, options):
            if name == 'badmodule':
                return None
            elif '.ps1' in options:
                return '/fake/path/to/%s.ps1' % name
            else:
                return '/fake/path/to/%s' % name

        mock_module_loader = MagicMock()
        mock_module_loader.find_plugin.side_effect = mock_find_plugin
        mock_shared_obj_loader = MagicMock()
        mock_shared_obj_loader.module_loader = mock_module_loader

        # we're using a real play context here
        play_context = PlayContext()

        # our test class
        action_base = DerivedActionBase(
            task=mock_task,
            connection=mock_connection,
            play_context=play_context,
            loader=fake_loader,
            templar=None,
            shared_loader_obj=mock_shared_obj_loader,
        )

        # test python module formatting
        with patch.object(builtins, 'open', mock_open(read_data=to_bytes(python_module_replacers.strip(), encoding='utf-8'))):
            with patch.object(os, 'rename'):
                mock_task.args = dict(a=1, foo='fö〩')
                mock_connection.module_implementation_preferences = ('',)
                (style, shebang, data, path) = action_base._configure_module(mock_task.action, mock_task.args)
                self.assertEqual(style, "new")
                self.assertEqual(shebang, u"#!/usr/bin/python")

                # test module not found
                self.assertRaises(AnsibleError, action_base._configure_module, 'badmodule', mock_task.args)

        # test powershell module formatting
        with patch.object(builtins, 'open', mock_open(read_data=to_bytes(powershell_module_replacers.strip(), encoding='utf-8'))):
            mock_task.action = 'win_copy'
            mock_task.args = dict(b=2)
            mock_connection.module_implementation_preferences = ('.ps1',)
            (style, shebang, data, path) = action_base._configure_module('stat', mock_task.args)
            self.assertEqual(style, "new")
            self.assertEqual(shebang, u'#!powershell')

            # test module not found
            self.assertRaises(AnsibleError, action_base._configure_module, 'badmodule', mock_task.args)

    def test_action_base__compute_environment_string(self):
        fake_loader = DictDataLoader({
        })

        # create our fake task
        mock_task = MagicMock()
        mock_task.action = "copy"
        mock_task.args = dict(a=1)

        # create a mock connection, so we don't actually try and connect to things
        def env_prefix(**args):
            return ' '.join(['%s=%s' % (k, shlex_quote(text_type(v))) for k, v in args.items()])
        mock_connection = MagicMock()
        mock_connection._shell.env_prefix.side_effect = env_prefix

        # we're using a real play context here
        play_context = PlayContext()

        # and we're using a real templar here too
        templar = Templar(loader=fake_loader)

        # our test class
        action_base = DerivedActionBase(
            task=mock_task,
            connection=mock_connection,
            play_context=play_context,
            loader=fake_loader,
            templar=templar,
            shared_loader_obj=None,
        )

        # test standard environment setup
        mock_task.environment = [dict(FOO='foo'), None]
        env_string = action_base._compute_environment_string()
        self.assertEqual(env_string, "FOO=foo")

        # test where environment is not a list
        mock_task.environment = dict(FOO='foo')
        env_string = action_base._compute_environment_string()
        self.assertEqual(env_string, "FOO=foo")

        # test environment with a variable in it
        templar.set_available_variables(variables=dict(the_var='bar'))
        mock_task.environment = [dict(FOO='{{the_var}}')]
        env_string = action_base._compute_environment_string()
        self.assertEqual(env_string, "FOO=bar")

        # test with a bad environment set
        mock_task.environment = dict(FOO='foo')
        mock_task.environment = ['hi there']
        self.assertRaises(AnsibleError, action_base._compute_environment_string)

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

    def test_action_base__make_tmp_path(self):
        # create our fake task
        mock_task = MagicMock()

        def get_shell_opt(opt):

            ret = None
            if opt == 'admin_users':
                ret = ['root', 'toor', 'Administrator']
            elif opt == 'remote_tmp':
                ret = '~/.ansible/tmp'

            return ret

        # create a mock connection, so we don't actually try and connect to things
        mock_connection = MagicMock()
        mock_connection.transport = 'ssh'
        mock_connection._shell.mkdtemp.return_value = 'mkdir command'
        mock_connection._shell.join_path.side_effect = os.path.join
        mock_connection._shell.get_option = get_shell_opt
        mock_connection._shell.HOMES_RE = re.compile(r'(\'|\")?(~|\$HOME)(.*)')

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
        self.assertEqual(action_base._make_tmp_path('root'), '/some/path/')

        # empty path fails
        action_base._low_level_execute_command.return_value = dict(rc=0, stdout='')
        self.assertRaises(AnsibleError, action_base._make_tmp_path, 'root')

        # authentication failure
        action_base._low_level_execute_command.return_value = dict(rc=5, stdout='')
        self.assertRaises(AnsibleError, action_base._make_tmp_path, 'root')

        # ssh error
        action_base._low_level_execute_command.return_value = dict(rc=255, stdout='', stderr='')
        self.assertRaises(AnsibleError, action_base._make_tmp_path, 'root')
        play_context.verbosity = 5
        self.assertRaises(AnsibleError, action_base._make_tmp_path, 'root')

        # general error
        action_base._low_level_execute_command.return_value = dict(rc=1, stdout='some stuff here', stderr='')
        self.assertRaises(AnsibleError, action_base._make_tmp_path, 'root')
        action_base._low_level_execute_command.return_value = dict(rc=1, stdout='some stuff here', stderr='No space left on device')
        self.assertRaises(AnsibleError, action_base._make_tmp_path, 'root')

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
        self.assertEqual(action_base._transfer_data('/path/to/remote/file', dict(some_key='some value')), '/path/to/remote/file')
        self.assertEqual(action_base._transfer_data('/path/to/remote/file', dict(some_key='fö〩')), '/path/to/remote/file')

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
        def build_module_command(env_string, shebang, cmd, arg_path=None):
            to_run = [env_string, cmd]
            if arg_path:
                to_run.append(arg_path)
            return " ".join(to_run)

        def get_option(option):
            return {}.get(option)

        mock_connection = MagicMock()
        mock_connection.build_module_command.side_effect = build_module_command
        mock_connection.socket_path = None
        mock_connection._shell.get_remote_filename.return_value = 'copy.py'
        mock_connection._shell.join_path.side_effect = os.path.join
        mock_connection._shell.tmpdir = '/var/tmp/mytempdir'
        mock_connection._shell.get_option = get_option

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
        action_base._is_pipelining_enabled = MagicMock()
        action_base._make_tmp_path = MagicMock()
        action_base._transfer_data = MagicMock()
        action_base._compute_environment_string = MagicMock()
        action_base._low_level_execute_command = MagicMock()
        action_base._fixup_perms2 = MagicMock()

        action_base._configure_module.return_value = ('new', '#!/usr/bin/python', 'this is the module data', 'path')
        action_base._is_pipelining_enabled.return_value = False
        action_base._compute_environment_string.return_value = ''
        action_base._connection.has_pipelining = False
        action_base._make_tmp_path.return_value = '/the/tmp/path'
        action_base._low_level_execute_command.return_value = dict(stdout='{"rc": 0, "stdout": "ok"}')
        self.assertEqual(action_base._execute_module(module_name=None, module_args=None), dict(_ansible_parsed=True, rc=0, stdout="ok", stdout_lines=['ok']))
        self.assertEqual(
            action_base._execute_module(
                module_name='foo',
                module_args=dict(z=9, y=8, x=7),
                task_vars=dict(a=1)
            ),
            dict(
                _ansible_parsed=True,
                rc=0,
                stdout="ok",
                stdout_lines=['ok'],
            )
        )

        # test with needing/removing a remote tmp path
        action_base._configure_module.return_value = ('old', '#!/usr/bin/python', 'this is the module data', 'path')
        action_base._is_pipelining_enabled.return_value = False
        action_base._make_tmp_path.return_value = '/the/tmp/path'
        self.assertEqual(action_base._execute_module(), dict(_ansible_parsed=True, rc=0, stdout="ok", stdout_lines=['ok']))

        action_base._configure_module.return_value = ('non_native_want_json', '#!/usr/bin/python', 'this is the module data', 'path')
        self.assertEqual(action_base._execute_module(), dict(_ansible_parsed=True, rc=0, stdout="ok", stdout_lines=['ok']))

        play_context.become = True
        play_context.become_user = 'foo'
        self.assertEqual(action_base._execute_module(), dict(_ansible_parsed=True, rc=0, stdout="ok", stdout_lines=['ok']))

        # test an invalid shebang return
        action_base._configure_module.return_value = ('new', '', 'this is the module data', 'path')
        action_base._is_pipelining_enabled.return_value = False
        action_base._make_tmp_path.return_value = '/the/tmp/path'
        self.assertRaises(AnsibleError, action_base._execute_module)

        # test with check mode enabled, once with support for check
        # mode and once with support disabled to raise an error
        play_context.check_mode = True
        action_base._configure_module.return_value = ('new', '#!/usr/bin/python', 'this is the module data', 'path')
        self.assertEqual(action_base._execute_module(), dict(_ansible_parsed=True, rc=0, stdout="ok", stdout_lines=['ok']))
        action_base._supports_check_mode = False
        self.assertRaises(AnsibleError, action_base._execute_module)

    def test_action_base_sudo_only_if_user_differs(self):
        fake_loader = MagicMock()
        fake_loader.get_basedir.return_value = os.getcwd()
        play_context = PlayContext()
        action_base = DerivedActionBase(None, None, play_context, fake_loader, None, None)
        action_base._connection = MagicMock(exec_command=MagicMock(return_value=(0, '', '')))
        action_base._connection._shell = MagicMock(append_command=MagicMock(return_value=('JOINED CMD')))

        play_context.become = True
        play_context.become_user = play_context.remote_user = 'root'
        play_context.make_become_cmd = MagicMock(return_value='CMD')

        action_base._low_level_execute_command('ECHO', sudoable=True)
        play_context.make_become_cmd.assert_not_called()

        play_context.remote_user = 'apo'
        action_base._low_level_execute_command('ECHO', sudoable=True, executable='/bin/csh')
        play_context.make_become_cmd.assert_called_once_with("ECHO", executable='/bin/csh')

        play_context.make_become_cmd.reset_mock()

        become_allow_same_user = C.BECOME_ALLOW_SAME_USER
        C.BECOME_ALLOW_SAME_USER = True
        try:
            play_context.remote_user = 'root'
            action_base._low_level_execute_command('ECHO SAME', sudoable=True)
            play_context.make_become_cmd.assert_called_once_with("ECHO SAME", executable=None)
        finally:
            C.BECOME_ALLOW_SAME_USER = become_allow_same_user


class TestActionBaseCleanReturnedData(unittest.TestCase):
    def test(self):

        fake_loader = DictDataLoader({
        })
        mock_module_loader = MagicMock()
        mock_shared_loader_obj = MagicMock()
        mock_shared_loader_obj.module_loader = mock_module_loader
        connection_loader_paths = ['/tmp/asdfadf', '/usr/lib64/whatever',
                                   'dfadfasf',
                                   'foo.py',
                                   '.*',
                                   # FIXME: a path with parans breaks the regex
                                   # '(.*)',
                                   '/path/to/ansible/lib/ansible/plugins/connection/custom_connection.py',
                                   '/path/to/ansible/lib/ansible/plugins/connection/ssh.py']

        def fake_all(path_only=None):
            for path in connection_loader_paths:
                yield path

        mock_connection_loader = MagicMock()
        mock_connection_loader.all = fake_all

        mock_shared_loader_obj.connection_loader = mock_connection_loader
        mock_connection = MagicMock()
        # mock_connection._shell.env_prefix.side_effect = env_prefix

        # action_base = DerivedActionBase(mock_task, mock_connection, play_context, None, None, None)
        action_base = DerivedActionBase(task=None,
                                        connection=mock_connection,
                                        play_context=None,
                                        loader=fake_loader,
                                        templar=None,
                                        shared_loader_obj=mock_shared_loader_obj)
        data = {'ansible_playbook_python': '/usr/bin/python',
                # 'ansible_rsync_path': '/usr/bin/rsync',
                'ansible_python_interpreter': '/usr/bin/python',
                'ansible_ssh_some_var': 'whatever',
                'ansible_ssh_host_key_somehost': 'some key here',
                'some_other_var': 'foo bar'}
        data = clean_facts(data)
        self.assertNotIn('ansible_playbook_python', data)
        self.assertNotIn('ansible_python_interpreter', data)
        self.assertIn('ansible_ssh_host_key_somehost', data)
        self.assertIn('some_other_var', data)


class TestActionBaseParseReturnedData(unittest.TestCase):

    def _action_base(self):
        fake_loader = DictDataLoader({
        })
        mock_module_loader = MagicMock()
        mock_shared_loader_obj = MagicMock()
        mock_shared_loader_obj.module_loader = mock_module_loader
        mock_connection_loader = MagicMock()

        mock_shared_loader_obj.connection_loader = mock_connection_loader
        mock_connection = MagicMock()

        action_base = DerivedActionBase(task=None,
                                        connection=mock_connection,
                                        play_context=None,
                                        loader=fake_loader,
                                        templar=None,
                                        shared_loader_obj=mock_shared_loader_obj)
        return action_base

    def test_fail_no_json(self):
        action_base = self._action_base()
        rc = 0
        stdout = 'foo\nbar\n'
        err = 'oopsy'
        returned_data = {'rc': rc,
                         'stdout': stdout,
                         'stdout_lines': stdout.splitlines(),
                         'stderr': err}
        res = action_base._parse_returned_data(returned_data)
        self.assertFalse(res['_ansible_parsed'])
        self.assertTrue(res['failed'])
        self.assertEqual(res['module_stderr'], err)

    def test_json_empty(self):
        action_base = self._action_base()
        rc = 0
        stdout = '{}\n'
        err = ''
        returned_data = {'rc': rc,
                         'stdout': stdout,
                         'stdout_lines': stdout.splitlines(),
                         'stderr': err}
        res = action_base._parse_returned_data(returned_data)
        del res['_ansible_parsed']  # we always have _ansible_parsed
        self.assertEqual(len(res), 0)
        self.assertFalse(res)

    def test_json_facts(self):
        action_base = self._action_base()
        rc = 0
        stdout = '{"ansible_facts": {"foo": "bar", "ansible_blip": "blip_value"}}\n'
        err = ''

        returned_data = {'rc': rc,
                         'stdout': stdout,
                         'stdout_lines': stdout.splitlines(),
                         'stderr': err}
        res = action_base._parse_returned_data(returned_data)
        self.assertTrue(res['ansible_facts'])
        self.assertIn('ansible_blip', res['ansible_facts'])
        # TODO: Should this be an AnsibleUnsafe?
        # self.assertIsInstance(res['ansible_facts'], AnsibleUnsafe)

    def test_json_facts_add_host(self):
        action_base = self._action_base()
        rc = 0
        stdout = '''{"ansible_facts": {"foo": "bar", "ansible_blip": "blip_value"},
        "add_host": {"host_vars": {"some_key": ["whatever the add_host object is"]}
        }
        }\n'''
        err = ''

        returned_data = {'rc': rc,
                         'stdout': stdout,
                         'stdout_lines': stdout.splitlines(),
                         'stderr': err}
        res = action_base._parse_returned_data(returned_data)
        self.assertTrue(res['ansible_facts'])
        self.assertIn('ansible_blip', res['ansible_facts'])
        self.assertIn('add_host', res)
        # TODO: Should this be an AnsibleUnsafe?
        # self.assertIsInstance(res['ansible_facts'], AnsibleUnsafe)
