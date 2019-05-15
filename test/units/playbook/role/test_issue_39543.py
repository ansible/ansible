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


class TestIssue39543(unittest.TestCase):

    def setUp(self):

        self.loader = DictDataLoader({
            '/etc/ansible/roles/role_a/tasks/main.yml': """
                - shell: echo start of role_a before including role_x

                - include_role:
                    name: "role_x"

                - shell: echo end of role_a after including role_x
            """,
            '/etc/ansible/roles/role_b/meta/main.yml': """
                dependencies:
                - { role: role_a }

            """,
            '/etc/ansible/roles/role_b/tasks/main.yml': """
                - shell: echo Not expecting to see this as role_b is conditionally excluded
            """,
            '/etc/ansible/roles/role_x/tasks/main.yml': """
                - shell: echo Should see this as it's included by role_a
            """,
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
            role = task._role
            if not role:
                continue

            yield (role.get_name(),
                   self.var_manager.get_vars(play=play, task=task))

    @patch('ansible.playbook.role.definition.unfrackpath',
           mock_unfrackpath_noop)
    def test_issue(self):

        """Test one-level include with default tasks and variables"""
        play = Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            roles=[
                {'role': 'role_a'},
                {'role': 'role_b', 'when': 'some_variable | default(false)'}
            ]
        ), loader=self.loader, variable_manager=self.var_manager)

        tasks = play.compile()
        print(tasks)
        import pudb; pu.db
