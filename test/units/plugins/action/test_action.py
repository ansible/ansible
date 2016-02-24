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


from ansible import constants as C
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.playbook.play_context import PlayContext
from ansible.plugins.action import ActionBase


class TestActionBase(unittest.TestCase):

    class DerivedActionBase(ActionBase):
        def run(self, tmp=None, task_vars=None):
            # We're not testing the plugin run() method, just the helper
            # methods ActionBase defines
            return dict()

    def test_sudo_only_if_user_differs(self):
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
