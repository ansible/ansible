# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from ansible.playbook.task import Task
from ansible.compat.tests import unittest

basic_shell_task = dict(
    name  = 'Test Task',
    shell = 'echo hi'
)

kv_shell_task = dict(
    action = 'shell echo hi'
)

class TestTask(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_construct_empty_task(self):
        t = Task()

    def test_construct_task_with_role(self):
        pass

    def test_construct_task_with_block(self):
        pass

    def test_construct_task_with_role_and_block(self):
        pass

    def test_load_task_simple(self):
        t = Task.load(basic_shell_task)
        assert t is not None
        self.assertEqual(t.name, basic_shell_task['name'])
        self.assertEqual(t.action, 'command')
        self.assertEqual(t.args, dict(_raw_params='echo hi', _uses_shell=True))

    def test_load_task_kv_form(self):
        t = Task.load(kv_shell_task)
        self.assertEqual(t.action, 'command')
        self.assertEqual(t.args, dict(_raw_params='echo hi', _uses_shell=True))

    def test_task_auto_name(self):
        assert 'name' not in kv_shell_task
        t = Task.load(kv_shell_task)
        #self.assertEqual(t.name, 'shell echo hi')

    def test_task_auto_name_with_role(self):
        pass

    def test_load_task_complex_form(self):
        pass

    def test_can_load_module_complex_form(self):
        pass

    def test_local_action_implies_delegate(self):
        pass

    def test_local_action_conflicts_with_delegate(self):
        pass

    def test_delegate_to_parses(self):
        pass
