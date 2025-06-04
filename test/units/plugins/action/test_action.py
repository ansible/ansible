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

from __future__ import annotations

import os
import re
from importlib import import_module


import builtins
import pytest
import shlex
import unittest

from unittest.mock import patch, MagicMock, mock_open

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleAuthenticationFailure
from ansible.executor.module_common import _BuiltModule
from ansible.module_utils.common.text.converters import to_bytes
from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible.playbook.play_context import PlayContext
from ansible.plugins.action import ActionBase
from ansible.plugins.shell import _ShellCommand
from ansible.vars.clean import clean_facts
from ansible.template import Templar
from ansible.plugins import loader

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


def _action_base():
    fake_loader = DictDataLoader({
    })
    mock_module_loader = MagicMock()
    mock_shared_loader_obj = MagicMock()
    mock_shared_loader_obj.module_loader = mock_module_loader
    mock_connection_loader = MagicMock()

    mock_shared_loader_obj.connection_loader = mock_connection_loader
    mock_connection = MagicMock()

    play_context = MagicMock()

    action_base = DerivedActionBase(task=None,
                                    connection=mock_connection,
                                    play_context=play_context,
                                    loader=fake_loader,
                                    templar=None,
                                    shared_loader_obj=mock_shared_loader_obj)
    return action_base


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
        self.assertEqual(results, {})

        mock_task.async_val = 0
        action_base = DerivedActionBase(mock_task, mock_connection, play_context, None, None, None)
        results = action_base.run()
        self.assertEqual(results, {})

    @pytest.mark.usefixtures('collection_loader')
    def test_action_base__configure_module(self):
        # Pre-populate the ansible.builtin collection
        # so reading the ansible_builtin_runtime.yml happens
        # before the mock_open below
        import_module('ansible_collections.ansible.builtin')
        fake_loader = DictDataLoader({
        })

        # create our fake task
        mock_task = MagicMock()
        mock_task.action = "copy"
        mock_task.async_val = 0
        mock_task.delegate_to = None

        # create a mock connection, so we don't actually try and connect to things
        mock_connection = MagicMock()
        mock_connection.become = None

        # create a mock shared loader object
        def mock_find_plugin_with_context(name, options, collection_list=None):
            mockctx = MagicMock()
            if name == 'badmodule':
                mockctx.resolved = False
                mockctx.plugin_resolved_path = None
            elif '.ps1' in options:
                mockctx.resolved = True
                mockctx.plugin_resolved_path = '/fake/path/to/%s.ps1' % name
            else:
                mockctx.resolved = True
                mockctx.plugin_resolved_path = '/fake/path/to/%s' % name
            mockctx.resolved_fqcn = name
            return mockctx

        mock_module_loader = MagicMock()
        mock_module_loader.find_plugin_with_context.side_effect = mock_find_plugin_with_context

        # we're using a real play context here
        play_context = PlayContext()

        # our test class
        action_base = DerivedActionBase(
            task=mock_task,
            connection=mock_connection,
            play_context=play_context,
            loader=fake_loader,
            templar=Templar(loader=fake_loader),
        )

        original_open = builtins.open

        def custom_open(file, *args, **kwargs):
            if file.endswith('.lock'):
                return original_open(file, *args, **kwargs)
            else:
                return mock_open(read_data=to_bytes(python_module_replacers.strip(), encoding='utf-8'))(file, *args, **kwargs)

        # test python module formatting
        with (
            patch.object(builtins, 'open', custom_open),
            patch.object(loader, 'module_loader', mock_module_loader)
        ):
            with patch.object(os, 'rename'):
                mock_task.args = dict(a=1, foo='fö〩')
                mock_connection.module_implementation_preferences = ('',)
                built_module, path = action_base._configure_module(mock_task.action, mock_task.args,
                                                                   task_vars=dict(ansible_python_interpreter='/usr/bin/python',
                                                                                  ansible_playbook_python='/usr/bin/python'))
                self.assertEqual(built_module.module_style, "new")
                self.assertEqual(built_module.shebang, u"#!/usr/bin/python")

                # test module not found
                self.assertRaises(AnsibleError, action_base._configure_module, 'badmodule', mock_task.args, {})

        # test powershell module formatting
        with (
            patch.object(builtins, 'open', mock_open(read_data=to_bytes(powershell_module_replacers.strip(), encoding='utf-8'))),
            patch.object(loader, 'module_loader', mock_module_loader),
        ):
            mock_task.action = 'win_copy'
            mock_task.args = dict(b=2)
            mock_connection.module_implementation_preferences = ('.ps1',)
            built_module, path = action_base._configure_module('stat', mock_task.args, {})
            self.assertEqual(built_module.module_style, "new")
            self.assertEqual(built_module.shebang, u'#!powershell')

            # test module not found
            self.assertRaises(AnsibleError, action_base._configure_module, 'badmodule', mock_task.args, {})

    def test_action_base__compute_environment_string(self):
        fake_loader = DictDataLoader({
        })

        # create our fake task
        mock_task = MagicMock()
        mock_task.action = "copy"
        mock_task.args = dict(a=1)

        # create a mock connection, so we don't actually try and connect to things
        def env_prefix(**args):
            return ' '.join(['%s=%s' % (k, shlex.quote(str(v))) for k, v in args.items()])
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
        templar.available_variables = dict(the_var='bar')
        mock_task.environment = [dict(FOO=TrustedAsTemplate().tag('{{the_var}}'))]
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

            assert opt == 'admin_users'
            ret = ['root', 'toor', 'Administrator']

            return ret

        # create a mock connection, so we don't actually try and connect to things
        mock_connection = MagicMock()
        mock_connection.transport = 'ssh'
        mock_connection._shell._mkdtemp2.return_value = _ShellCommand(command='mkdir command')
        mock_connection._shell.join_path.side_effect = os.path.join
        mock_connection._shell.get_option = get_shell_opt
        mock_connection._shell.HOMES_RE = re.compile(r'(\'|\")?(~|\$HOME)(.*)')

        # we're using a real play context here
        play_context = PlayContext()
        play_context.become = True
        play_context.become_user = 'foo'

        mock_task.become = True
        mock_task.become_user = True

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
        self.assertRaises(AnsibleError, action_base._make_tmp_path, 'root')

        # general error
        action_base._low_level_execute_command.return_value = dict(rc=1, stdout='some stuff here', stderr='')
        self.assertRaises(AnsibleError, action_base._make_tmp_path, 'root')
        action_base._low_level_execute_command.return_value = dict(rc=1, stdout='some stuff here', stderr='No space left on device')
        self.assertRaises(AnsibleError, action_base._make_tmp_path, 'root')

    def test_action_base__fixup_perms2(self):
        mock_task = MagicMock()
        mock_connection = MagicMock()
        play_context = PlayContext()
        action_base = DerivedActionBase(
            task=mock_task,
            connection=mock_connection,
            play_context=play_context,
            loader=None,
            templar=None,
            shared_loader_obj=None,
        )
        action_base._low_level_execute_command = MagicMock()
        remote_paths = ['/tmp/foo/bar.txt', '/tmp/baz.txt']
        remote_user = 'remoteuser1'

        # Used for skipping down to common group dir.
        CHMOD_ACL_FLAGS = ('+a', 'A+user:remoteuser2:r:allow')

        def runWithNoExpectation(execute=False):
            return action_base._fixup_perms2(
                remote_paths,
                remote_user=remote_user,
                execute=execute)

        def assertSuccess(execute=False):
            self.assertEqual(runWithNoExpectation(execute), remote_paths)

        def assertThrowRegex(regex, execute=False):
            self.assertRaisesRegex(
                AnsibleError,
                regex,
                action_base._fixup_perms2,
                remote_paths,
                remote_user=remote_user,
                execute=execute)

        def get_shell_option_for_arg(args_kv, default):
            """A helper for get_shell_option. Returns a function that, if
            called with ``option`` that exists in args_kv, will return the
            value, else will return ``default`` for every other given arg"""
            def _helper(option, *args, **kwargs):
                return args_kv.get(option, default)
            return _helper

        action_base.get_become_option = MagicMock()
        action_base.get_become_option.return_value = 'remoteuser2'

        # Step 1: On windows, we just return remote_paths
        action_base._connection._shell._IS_WINDOWS = True
        assertSuccess(execute=False)
        assertSuccess(execute=True)

        # But if we're not on windows....we have more work to do.
        action_base._connection._shell._IS_WINDOWS = False

        # Step 2: We're /not/ becoming an unprivileged user
        action_base._remote_chmod = MagicMock()
        action_base._is_become_unprivileged = MagicMock()
        action_base._is_become_unprivileged.return_value = False
        # Two subcases:
        #   - _remote_chmod rc is 0
        #   - _remote-chmod rc is not 0, something failed
        action_base._remote_chmod.return_value = {
            'rc': 0,
            'stdout': 'some stuff here',
            'stderr': '',
        }
        assertSuccess(execute=True)

        # When execute=False, we just get the list back. But add it here for
        # completion. chmod is never called.
        assertSuccess()

        action_base._remote_chmod.return_value = {
            'rc': 1,
            'stdout': 'some stuff here',
            'stderr': 'and here',
        }
        assertThrowRegex(
            'Failed to set permissions on remote files',
            execute=True)

        # Step 3: we are becoming unprivileged
        action_base._is_become_unprivileged.return_value = True

        # Step 3a: setfacl
        action_base._remote_set_user_facl = MagicMock()
        action_base._remote_set_user_facl.return_value = {
            'rc': 0,
            'stdout': '',
            'stderr': '',
        }
        assertSuccess()

        # Step 3b: chmod +rwx if we need to
        # To get here, setfacl failed, so mock it as such.
        action_base._remote_set_user_facl.return_value = {
            'rc': 1,
            'stdout': '',
            'stderr': '',
        }
        action_base._remote_chmod.return_value = {
            'rc': 1,
            'stdout': 'some stuff here',
            'stderr': '',
        }
        assertThrowRegex(
            'Failed to set file mode or acl on remote temporary files',
            execute=True)
        action_base._remote_chmod.return_value = {
            'rc': 0,
            'stdout': 'some stuff here',
            'stderr': '',
        }
        assertSuccess(execute=True)

        # Step 3c: chown
        action_base._remote_chown = MagicMock()
        action_base._remote_chown.return_value = {
            'rc': 0,
            'stdout': '',
            'stderr': '',
        }
        assertSuccess()
        action_base._remote_chown.return_value = {
            'rc': 1,
            'stdout': '',
            'stderr': '',
        }
        remote_user = 'root'
        action_base._get_admin_users = MagicMock()
        action_base._get_admin_users.return_value = ['root']
        assertThrowRegex('user would be unable to read the file.')
        remote_user = 'remoteuser1'

        # Step 3d: chmod +a on osx
        assertSuccess()
        action_base._remote_chmod.assert_called_with(
            ['remoteuser2 allow read'] + remote_paths,
            '+a')

        # This case can cause Solaris chmod to return 5 which the ssh plugin
        # treats as failure. To prevent a regression and ensure we still try the
        # rest of the cases below, we mock the thrown exception here.
        # This function ensures that only the macOS case (+a) throws this.
        def raise_if_plus_a(definitely_not_underscore, mode):
            if mode == '+a':
                raise AnsibleAuthenticationFailure()
            return {'rc': 0, 'stdout': '', 'stderr': ''}

        action_base._remote_chmod.side_effect = raise_if_plus_a
        assertSuccess()

        # Step 3e: chmod A+ on Solaris
        # We threw AnsibleAuthenticationFailure above, try Solaris fallback.
        # Based on our lambda above, it should be successful.
        action_base._remote_chmod.assert_called_with(
            remote_paths,
            'A+user:remoteuser2:r:allow')
        assertSuccess()

        # Step 3f: Common group
        def rc_1_if_chmod_acl(definitely_not_underscore, mode):
            rc = 0
            if mode in CHMOD_ACL_FLAGS:
                rc = 1
            return {'rc': rc, 'stdout': '', 'stderr': ''}

        action_base._remote_chmod = MagicMock()
        action_base._remote_chmod.side_effect = rc_1_if_chmod_acl

        get_shell_option = action_base.get_shell_option
        action_base.get_shell_option = MagicMock()
        action_base.get_shell_option.side_effect = get_shell_option_for_arg(
            {
                'common_remote_group': 'commongroup',
            },
            None)
        action_base._remote_chgrp = MagicMock()
        action_base._remote_chgrp.return_value = {
            'rc': 0,
            'stdout': '',
            'stderr': '',
        }
        # TODO: Add test to assert warning is shown if
        # world_readable_temp is set in this case.
        assertSuccess()
        action_base._remote_chgrp.assert_called_once_with(
            remote_paths,
            'commongroup')

        # Step 4: world-readable tmpdir
        action_base.get_shell_option.side_effect = get_shell_option_for_arg(
            {
                'world_readable_temp': True,
                'common_remote_group': None,
            },
            None)
        action_base._remote_chmod.return_value = {
            'rc': 0,
            'stdout': 'some stuff here',
            'stderr': '',
        }
        assertSuccess()
        action_base._remote_chmod = MagicMock()
        action_base._remote_chmod.return_value = {
            'rc': 1,
            'stdout': 'some stuff here',
            'stderr': '',
        }
        assertThrowRegex('Failed to set file mode on remote files')

        # Otherwise if we make it here in this state, we hit the catch-all
        action_base.get_shell_option.side_effect = get_shell_option_for_arg(
            {},
            None)
        assertThrowRegex('on the temporary files Ansible needs to create')

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
        self.assertEqual(action_base._transfer_data('/path/to/remote/file', 'some data'.encode()), '/path/to/remote/file')
        self.assertEqual(action_base._transfer_data('/path/to/remote/file', 'some mixed data: fö〩'.encode()), '/path/to/remote/file')

        mock_afo.write.side_effect = Exception()
        self.assertRaises(AnsibleError, action_base._transfer_data, '/path/to/remote/file', '')

        with pytest.raises(TypeError):
            action_base._transfer_data('/path/to/remote/file', dict())

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
        mock_task.diff = False
        mock_task.check_mode = False
        mock_task.no_log = False

        # create a mock connection, so we don't actually try and connect to things
        def get_option(option):
            return {'admin_users': ['root', 'toor']}.get(option)

        mock_connection = MagicMock()
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

        action_base._configure_module.return_value = (
            _BuiltModule(module_style='new', shebang='#!/usr/bin/python', b_module_data=b'this is the module data', serialization_profile='legacy'), 'path')
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
        action_base._configure_module.return_value = (
            _BuiltModule(module_style='old', shebang='#!/usr/bin/python', b_module_data=b'this is the module data', serialization_profile='legacy'), 'path')
        action_base._is_pipelining_enabled.return_value = False
        action_base._make_tmp_path.return_value = '/the/tmp/path'
        self.assertEqual(action_base._execute_module(), dict(_ansible_parsed=True, rc=0, stdout="ok", stdout_lines=['ok']))

        action_base._configure_module.return_value = (
            _BuiltModule(module_style='non_native_want_json', shebang='#!/usr/bin/python', b_module_data=b'this is the module data',
                         serialization_profile='legacy'), 'path')
        self.assertEqual(action_base._execute_module(), dict(_ansible_parsed=True, rc=0, stdout="ok", stdout_lines=['ok']))

        play_context.become = True
        play_context.become_user = 'foo'
        mock_task.become = True
        mock_task.become_user = True
        self.assertEqual(action_base._execute_module(), dict(_ansible_parsed=True, rc=0, stdout="ok", stdout_lines=['ok']))

        # test an invalid shebang return
        action_base._configure_module.return_value = (
            _BuiltModule(module_style='new', shebang='', b_module_data=b'this is the module data', serialization_profile='legacy'), 'path')
        action_base._is_pipelining_enabled.return_value = False
        action_base._make_tmp_path.return_value = '/the/tmp/path'
        self.assertRaises(AnsibleError, action_base._execute_module)

        # test with check mode enabled, once with support for check
        # mode and once with support disabled to raise an error
        play_context.check_mode = True
        mock_task.check_mode = True
        action_base._configure_module.return_value = (
            _BuiltModule(module_style='new', shebang='#!/usr/bin/python', b_module_data=b'this is the module data', serialization_profile='legacy'), 'path')
        self.assertEqual(action_base._execute_module(), dict(_ansible_parsed=True, rc=0, stdout="ok", stdout_lines=['ok']))
        action_base._supports_check_mode = False
        self.assertRaises(AnsibleError, action_base._execute_module)

    def test_action_base_sudo_only_if_user_differs(self):
        fake_loader = MagicMock()
        fake_loader.get_basedir.return_value = os.getcwd()
        play_context = PlayContext()

        action_base = DerivedActionBase(None, None, play_context, fake_loader, None, None)
        action_base.get_become_option = MagicMock(return_value='root')
        action_base._get_remote_user = MagicMock(return_value='root')

        action_base._connection = MagicMock(exec_command=MagicMock(return_value=(0, '', '')))

        action_base._connection._shell = shell = MagicMock(append_command=MagicMock(return_value=('JOINED CMD')))

        action_base._connection.become = become = MagicMock()
        action_base._connection.transport = ''
        become.build_become_command.return_value = 'foo'

        action_base._low_level_execute_command('ECHO', sudoable=True)
        become.build_become_command.assert_not_called()

        action_base._get_remote_user.return_value = 'apo'
        action_base._low_level_execute_command('ECHO', sudoable=True, executable='/bin/csh')
        become.build_become_command.assert_called_once_with("ECHO", shell)

        become.build_become_command.reset_mock()

        with patch.object(C, 'BECOME_ALLOW_SAME_USER', new=True):
            action_base._get_remote_user.return_value = 'root'
            action_base._low_level_execute_command('ECHO SAME', sudoable=True)
            become.build_become_command.assert_called_once_with("ECHO SAME", shell)

    def test__remote_expand_user_relative_pathing(self):
        action_base = _action_base()
        action_base._play_context.remote_addr = 'bar'
        action_base._connection.get_option.return_value = 'bar'
        action_base._low_level_execute_command = MagicMock(return_value={'stdout': b'../home/user'})
        action_base._connection._shell.join_path.return_value = '../home/user/foo'
        with self.assertRaises(AnsibleError) as cm:
            action_base._remote_expand_user('~/foo')
        self.assertEqual(
            cm.exception.message,
            "'bar' returned an invalid relative home directory path containing '..'"
        )


class TestActionBaseCleanReturnedData(unittest.TestCase):
    def test(self):
        data = {'ansible_playbook_python': '/usr/bin/python',
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

    def test_fail_no_json(self):
        action_base = _action_base()
        rc = 0
        stdout = 'foo\nbar\n'
        err = 'oopsy'
        returned_data = {'rc': rc,
                         'stdout': stdout,
                         'stdout_lines': stdout.splitlines(),
                         'stderr': err}
        res = action_base._parse_returned_data(returned_data, 'legacy')
        self.assertFalse(res['_ansible_parsed'])
        self.assertTrue(res['failed'])
        self.assertEqual(res['module_stderr'], err)

    def test_json_empty(self):
        action_base = _action_base()
        rc = 0
        stdout = '{}\n'
        err = ''
        returned_data = {'rc': rc,
                         'stdout': stdout,
                         'stdout_lines': stdout.splitlines(),
                         'stderr': err}
        res = action_base._parse_returned_data(returned_data, 'legacy')
        del res['_ansible_parsed']  # we always have _ansible_parsed
        self.assertEqual(len(res), 0)
        self.assertFalse(res)

    def test_json_facts(self):
        action_base = _action_base()
        rc = 0
        stdout = '{"ansible_facts": {"foo": "bar", "ansible_blip": "blip_value"}}\n'
        err = ''

        returned_data = {'rc': rc,
                         'stdout': stdout,
                         'stdout_lines': stdout.splitlines(),
                         'stderr': err}
        res = action_base._parse_returned_data(returned_data, 'legacy')
        self.assertTrue(res['ansible_facts'])
        self.assertIn('ansible_blip', res['ansible_facts'])

    def test_json_facts_add_host(self):
        action_base = _action_base()
        rc = 0
        stdout = """{"ansible_facts": {"foo": "bar", "ansible_blip": "blip_value"},
        "add_host": {"host_vars": {"some_key": ["whatever the add_host object is"]}
        }
        }\n"""
        err = ''

        returned_data = {'rc': rc,
                         'stdout': stdout,
                         'stdout_lines': stdout.splitlines(),
                         'stderr': err}
        res = action_base._parse_returned_data(returned_data, 'legacy')
        self.assertTrue(res['ansible_facts'])
        self.assertIn('ansible_blip', res['ansible_facts'])
        self.assertIn('add_host', res)
