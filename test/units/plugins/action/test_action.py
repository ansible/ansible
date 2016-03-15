#!/usr/bin/env python
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

import ast
import json
import pipes
import os

from sys import version_info

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

from ansible import __version__ as ansible_version
from ansible import constants as C
from ansible.compat.six import text_type
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock, mock_open

from ansible.errors import AnsibleError
from ansible.playbook.play_context import PlayContext
from ansible.plugins import PluginLoader
from ansible.plugins.action import ActionBase
from ansible.template import Templar
from ansible.utils.unicode import to_bytes

from units.mock.loader import DictDataLoader

python_module_replacers = b"""
#!/usr/bin/python

#ANSIBLE_VERSION = "<<ANSIBLE_VERSION>>"
#MODULE_ARGS = "<<INCLUDE_ANSIBLE_MODULE_ARGS>>"
#MODULE_COMPLEX_ARGS = "<<INCLUDE_ANSIBLE_MODULE_COMPLEX_ARGS>>"
#SELINUX_SPECIAL_FS="<<SELINUX_SPECIAL_FILESYSTEMS>>"

test = u'Toshio \u304f\u3089\u3068\u307f'
from ansible.module_utils.basic import *
"""

powershell_module_replacers = b"""
WINDOWS_ARGS = "<<INCLUDE_ANSIBLE_MODULE_WINDOWS_ARGS>>"
# POWERSHELL_COMMON
"""

# Prior to 3.4.4, mock_open cannot handle binary read_data
if version_info >= (3,) and version_info < (3, 4, 4):
    file_spec = None

    def _iterate_read_data(read_data):
        # Helper for mock_open:
        # Retrieve lines from read_data via a generator so that separate calls to
        # readline, read, and readlines are properly interleaved
        sep = b'\n' if isinstance(read_data, bytes) else '\n'
        data_as_list = [l + sep for l in read_data.split(sep)]

        if data_as_list[-1] == sep:
            # If the last line ended in a newline, the list comprehension will have an
            # extra entry that's just a newline.  Remove this.
            data_as_list = data_as_list[:-1]
        else:
            # If there wasn't an extra newline by itself, then the file being
            # emulated doesn't have a newline to end the last line  remove the
            # newline that our naive format() added
            data_as_list[-1] = data_as_list[-1][:-1]

        for line in data_as_list:
            yield line

    def mock_open(mock=None, read_data=''):
        """
        A helper function to create a mock to replace the use of `open`. It works
        for `open` called directly or used as a context manager.

        The `mock` argument is the mock object to configure. If `None` (the
        default) then a `MagicMock` will be created for you, with the API limited
        to methods or attributes available on standard file handles.

        `read_data` is a string for the `read` methoddline`, and `readlines` of the
        file handle to return.  This is an empty string by default.
        """
        def _readlines_side_effect(*args, **kwargs):
            if handle.readlines.return_value is not None:
                return handle.readlines.return_value
            return list(_data)

        def _read_side_effect(*args, **kwargs):
            if handle.read.return_value is not None:
                return handle.read.return_value
            return type(read_data)().join(_data)

        def _readline_side_effect():
            if handle.readline.return_value is not None:
                while True:
                    yield handle.readline.return_value
            for line in _data:
                yield line


        global file_spec
        if file_spec is None:
            import _io
            file_spec = list(set(dir(_io.TextIOWrapper)).union(set(dir(_io.BytesIO))))

        if mock is None:
            mock = MagicMock(name='open', spec=open)

        handle = MagicMock(spec=file_spec)
        handle.__enter__.return_value = handle

        _data = _iterate_read_data(read_data)

        handle.write.return_value = None
        handle.read.return_value = None
        handle.readline.return_value = None
        handle.readlines.return_value = None

        handle.read.side_effect = _read_side_effect
        handle.readline.side_effect = _readline_side_effect()
        handle.readlines.side_effect = _readlines_side_effect

        mock.return_value = handle
        return mock


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

        mock_task.async = None
        action_base = DerivedActionBase(mock_task, mock_connection, play_context, None, None, None)
        results = action_base.run()
        self.assertEqual(results, dict())

        mock_task.async = 0
        action_base = DerivedActionBase(mock_task, mock_connection, play_context, None, None, None)
        results = action_base.run()
        self.assertEqual(results, dict(invocation=dict(module_name='foo', module_args=dict(a=1, b=2, c=3))))

    def test_action_base__configure_module(self):
        fake_loader = DictDataLoader({
        })

        # create our fake task
        mock_task = MagicMock()
        mock_task.action = "copy"

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
        with patch.object(builtins, 'open', mock_open(read_data=to_bytes(python_module_replacers.strip(), encoding='utf-8'))) as m:
            mock_task.args = dict(a=1, foo='fö〩')
            mock_connection.module_implementation_preferences = ('',)
            (style, shebang, data) = action_base._configure_module(mock_task.action, mock_task.args)
            self.assertEqual(style, "new")
            self.assertEqual(shebang, b"#!/usr/bin/python")

            # test module not found
            self.assertRaises(AnsibleError, action_base._configure_module, 'badmodule', mock_task.args)

        # test powershell module formatting
        with patch.object(builtins, 'open', mock_open(read_data=to_bytes(powershell_module_replacers.strip(), encoding='utf-8'))) as m:
            mock_task.action = 'win_copy'
            mock_task.args = dict(b=2)
            mock_connection.module_implementation_preferences = ('.ps1',)
            (style, shebang, data) = action_base._configure_module('stat', mock_task.args)
            self.assertEqual(style, "new")
            self.assertEqual(shebang, None)

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
            return ' '.join(['%s=%s' % (k, pipes.quote(text_type(v))) for k,v in args.items()])
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
        action_base = DerivedActionBase(None, None, play_context, None, None, None)
        action_base._connection = MagicMock(exec_command=MagicMock(return_value=(0, '', '')))

        play_context.become = True
        play_context.become_user = play_context.remote_user = 'root'
        play_context.make_become_cmd = MagicMock(return_value='CMD')

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
