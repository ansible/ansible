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
#
# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, Mock, patch
from ansible.module_utils.basic import AnsibleModuleFSM


class TestAnsibleModuleFSM(unittest.TestCase):

    @patch('ansible.module_utils.basic.AnsibleModule', autospec=True)
    def test_happy_path(self, ansible_mod_cls):
        ansible_mod = ansible_mod_cls.return_value

        state1 = 1
        state2 = 2
        state3 = 3

        event1 = 1
        event2 = 2
        event3 = 3

        action1 = Mock(return_value=(event1, {}))
        action2 = Mock(return_value=(event2, {}))
        action3 = Mock(return_value=(event3, {}))

        argument_spec = dict(
            arg1=dict(default='na', choices=['na', 'other']),
            arg2=dict(required=True, type='str')
        )

        AnsibleModuleFSM(
            state_machine=dict(
                starting_state=state1,
                starting_action=action1,
                exit_event=event3,
                transitions={
                    (state1, event1): (state2, action2),
                    (state2, event2): (state3, action3),
                }
            ),
            argument_spec=argument_spec
        )

        expected = set(['argument_spec'])
        actual = set(ansible_mod_cls.call_args[1].keys())
        self.assertTrue(expected.issubset(actual),
                        "%r is not a subjset of %r" % (expected, actual))

        self.assertEqual(action1.call_args, call(ansible_mod, {}))
        self.assertEqual(action2.call_args, call(ansible_mod, {}))
        self.assertEqual(action3.call_args, call(ansible_mod, {}))
