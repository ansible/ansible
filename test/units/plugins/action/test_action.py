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
if version_info.major == 2:
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

from units.mock.loader import DictDataLoader

python_module_replacers = """
#!/usr/bin/python

#ANSIBLE_VERSION = "<<ANSIBLE_VERSION>>"
#MODULE_ARGS = "<<INCLUDE_ANSIBLE_MODULE_ARGS>>"
#MODULE_COMPLEX_ARGS = "<<INCLUDE_ANSIBLE_MODULE_COMPLEX_ARGS>>"
#SELINUX_SPECIAL_FS="<<SELINUX_SPECIAL_FILESYSTEMS>>"

from ansible.module_utils.basic import *
"""

powershell_module_replacers = """
WINDOWS_ARGS = "<<INCLUDE_ANSIBLE_MODULE_WINDOWS_ARGS>>"
# POWERSHELL_COMMON
"""

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
        with patch.object(builtins, 'open', mock_open(read_data=python_module_replacers.strip())) as m:
            mock_task.args = dict(a=1)
            mock_connection.module_implementation_preferences = ('',)
            (style, shebang, data) = action_base._configure_module(mock_task.action, mock_task.args)
            self.assertEqual(style, "new")
            self.assertEqual(shebang, "#!/usr/bin/python")

            # test module not found
            self.assertRaises(AnsibleError, action_base._configure_module, 'badmodule', mock_task.args)

        # test powershell module formatting
        with patch.object(builtins, 'open', mock_open(read_data=powershell_module_replacers.strip())) as m:
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
