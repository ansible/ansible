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

from sys import version_info
if version_info[0] == 2:
    import __builtin__ as builtins
else:
    import builtins

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

    def test_sudo_only_if_user_differs(self):
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
