# (c) 2016, Daniel Miranda <danielkza2@gmail.com>
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

from units.compat import unittest
from units.compat.mock import patch

from ansible.playbook import Play
from ansible.playbook.role_include import IncludeRole
from ansible.playbook.task import Task
from ansible.vars.manager import VariableManager

from units.mock.loader import DictDataLoader
from units.mock.path import mock_unfrackpath_noop


class TestIncludeRole(unittest.TestCase):

    def setUp(self):

        self.loader = DictDataLoader({
            '/etc/ansible/roles/l1/tasks/main.yml': """
                - shell: echo 'hello world from l1'
                - include_role: name=l2
            """,
            '/etc/ansible/roles/l1/tasks/alt.yml': """
                - shell: echo 'hello world from l1 alt'
                - include_role: name=l2 tasks_from=alt defaults_from=alt
            """,
            '/etc/ansible/roles/l1/defaults/main.yml': """
                test_variable: l1-main
                l1_variable: l1-main
            """,
            '/etc/ansible/roles/l1/defaults/alt.yml': """
                test_variable: l1-alt
                l1_variable: l1-alt
            """,
            '/etc/ansible/roles/l2/tasks/main.yml': """
                - shell: echo 'hello world from l2'
                - include_role: name=l3
            """,
            '/etc/ansible/roles/l2/tasks/alt.yml': """
                - shell: echo 'hello world from l2 alt'
                - include_role: name=l3 tasks_from=alt defaults_from=alt
            """,
            '/etc/ansible/roles/l2/defaults/main.yml': """
                test_variable: l2-main
                l2_variable: l2-main
            """,
            '/etc/ansible/roles/l2/defaults/alt.yml': """
                test_variable: l2-alt
                l2_variable: l2-alt
            """,
            '/etc/ansible/roles/l3/tasks/main.yml': """
                - shell: echo 'hello world from l3'
            """,
            '/etc/ansible/roles/l3/tasks/alt.yml': """
                - shell: echo 'hello world from l3 alt'
            """,
            '/etc/ansible/roles/l3/defaults/main.yml': """
                test_variable: l3-main
                l3_variable: l3-main
            """,
            '/etc/ansible/roles/l3/defaults/alt.yml': """
                test_variable: l3-alt
                l3_variable: l3-alt
            """
        })

        self.var_manager = VariableManager(loader=self.loader)

    def tearDown(self):
        pass

    def flatten_tasks(self, tasks):
        for task in tasks:
            if isinstance(task, IncludeRole):
                blocks, handlers = task.get_block_list(loader=self.loader)
                for block in blocks:
                    for t in self.flatten_tasks(block.block):
                        yield t
            elif isinstance(task, Task):
                yield task
            else:
                for t in self.flatten_tasks(task.block):
                    yield t

    def get_tasks_vars(self, play, tasks):
        for task in self.flatten_tasks(tasks):
            if task.implicit:
                # skip meta: role_complete
                continue
            role = task._role
            if not role:
                continue

            yield (role.get_name(),
                   self.var_manager.get_vars(play=play, task=task))

    @patch('ansible.playbook.role.definition.unfrackpath',
           mock_unfrackpath_noop)
    def test_simple(self):

        """Test one-level include with default tasks and variables"""

        play = Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            tasks=[
                {'include_role': 'name=l3'}
            ]
        ), loader=self.loader, variable_manager=self.var_manager)

        tasks = play.compile()
        tested = False
        for role, task_vars in self.get_tasks_vars(play, tasks):
            tested = True
            self.assertEqual(task_vars.get('l3_variable'), 'l3-main')
            self.assertEqual(task_vars.get('test_variable'), 'l3-main')
        self.assertTrue(tested)

    @patch('ansible.playbook.role.definition.unfrackpath',
           mock_unfrackpath_noop)
    def test_simple_alt_files(self):

        """Test one-level include with alternative tasks and variables"""

        play = Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            tasks=[{'include_role': 'name=l3 tasks_from=alt defaults_from=alt'}]),
            loader=self.loader, variable_manager=self.var_manager)

        tasks = play.compile()
        tested = False
        for role, task_vars in self.get_tasks_vars(play, tasks):
            tested = True
            self.assertEqual(task_vars.get('l3_variable'), 'l3-alt')
            self.assertEqual(task_vars.get('test_variable'), 'l3-alt')
        self.assertTrue(tested)

    @patch('ansible.playbook.role.definition.unfrackpath',
           mock_unfrackpath_noop)
    def test_nested(self):

        """
        Test nested includes with default tasks and variables.

        Variables from outer roles should be inherited, but overridden in inner
        roles.
        """

        play = Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            tasks=[
                {'include_role': 'name=l1'}
            ]
        ), loader=self.loader, variable_manager=self.var_manager)

        tasks = play.compile()
        expected_roles = ['l1', 'l2', 'l3']
        for role, task_vars in self.get_tasks_vars(play, tasks):
            expected_roles.remove(role)
            # Outer-most role must not have variables from inner roles yet
            if role == 'l1':
                self.assertEqual(task_vars.get('l1_variable'), 'l1-main')
                self.assertEqual(task_vars.get('l2_variable'), None)
                self.assertEqual(task_vars.get('l3_variable'), None)
                self.assertEqual(task_vars.get('test_variable'), 'l1-main')
            # Middle role must have variables from outer role, but not inner
            elif role == 'l2':
                self.assertEqual(task_vars.get('l1_variable'), 'l1-main')
                self.assertEqual(task_vars.get('l2_variable'), 'l2-main')
                self.assertEqual(task_vars.get('l3_variable'), None)
                self.assertEqual(task_vars.get('test_variable'), 'l2-main')
            # Inner role must have variables from both outer roles
            elif role == 'l3':
                self.assertEqual(task_vars.get('l1_variable'), 'l1-main')
                self.assertEqual(task_vars.get('l2_variable'), 'l2-main')
                self.assertEqual(task_vars.get('l3_variable'), 'l3-main')
                self.assertEqual(task_vars.get('test_variable'), 'l3-main')
            else:
                self.fail()
        self.assertFalse(expected_roles)

    @patch('ansible.playbook.role.definition.unfrackpath',
           mock_unfrackpath_noop)
    def test_nested_alt_files(self):

        """
        Test nested includes with alternative tasks and variables.

        Variables from outer roles should be inherited, but overridden in inner
        roles.
        """

        play = Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            tasks=[
                {'include_role': 'name=l1 tasks_from=alt defaults_from=alt'}
            ]
        ), loader=self.loader, variable_manager=self.var_manager)

        tasks = play.compile()
        expected_roles = ['l1', 'l2', 'l3']
        for role, task_vars in self.get_tasks_vars(play, tasks):
            expected_roles.remove(role)
            # Outer-most role must not have variables from inner roles yet
            if role == 'l1':
                self.assertEqual(task_vars.get('l1_variable'), 'l1-alt')
                self.assertEqual(task_vars.get('l2_variable'), None)
                self.assertEqual(task_vars.get('l3_variable'), None)
                self.assertEqual(task_vars.get('test_variable'), 'l1-alt')
            # Middle role must have variables from outer role, but not inner
            elif role == 'l2':
                self.assertEqual(task_vars.get('l1_variable'), 'l1-alt')
                self.assertEqual(task_vars.get('l2_variable'), 'l2-alt')
                self.assertEqual(task_vars.get('l3_variable'), None)
                self.assertEqual(task_vars.get('test_variable'), 'l2-alt')
            # Inner role must have variables from both outer roles
            elif role == 'l3':
                self.assertEqual(task_vars.get('l1_variable'), 'l1-alt')
                self.assertEqual(task_vars.get('l2_variable'), 'l2-alt')
                self.assertEqual(task_vars.get('l3_variable'), 'l3-alt')
                self.assertEqual(task_vars.get('test_variable'), 'l3-alt')
            else:
                self.fail()
        self.assertFalse(expected_roles)
