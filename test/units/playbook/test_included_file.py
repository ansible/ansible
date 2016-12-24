# (c) 2016, Adrian Likins <alikins@redhat.com>
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

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import MagicMock
from units.mock.loader import DictDataLoader

from ansible.playbook.task import Task
from ansible.playbook.task_include import TaskInclude
from ansible.executor import task_result

from ansible.playbook.included_file import IncludedFile


class TestIncludedFile(unittest.TestCase):
    def test(self):
        filename = 'somefile.yml'

        inc_file = IncludedFile(filename=filename, args=[], task=None)

        self.assertIsInstance(inc_file, IncludedFile)
        self.assertEquals(inc_file._filename, filename)
        self.assertEquals(inc_file._args, [])
        self.assertEquals(inc_file._task, None)

    def test_process_include_results(self):
        hostname = "testhost1"
        hostname2 = "testhost2"

        parent_task_ds = {'debug': 'msg=foo'}
        parent_task = Task()
        parent_task.load(parent_task_ds)

        task_ds = {'include': 'include_test.yml'}
        task_include = TaskInclude()
        loaded_task = task_include.load(task_ds, task_include=parent_task)

        child_task_ds = {'include': 'other_include_test.yml'}
        child_task_include = TaskInclude()
        loaded_child_task = child_task_include.load(child_task_ds, task_include=loaded_task)

        return_data = {'include': 'include_test.yml'}
        # The task in the TaskResult has to be a TaskInclude so it has a .static attr
        result1 = task_result.TaskResult(host=hostname, task=loaded_task, return_data=return_data)

        return_data = {'include': 'other_include_test.yml'}
        result2 = task_result.TaskResult(host=hostname2, task=loaded_child_task, return_data=return_data)
        results = [result1, result2]

        fake_loader = DictDataLoader({'include_test.yml': "",
                                      'other_include_test.yml': ""})

        mock_tqm = MagicMock(name='MockTaskQueueManager')

        mock_play = MagicMock(name='MockPlay')

        mock_iterator = MagicMock(name='MockIterator')
        mock_iterator._play = mock_play

        mock_inventory = MagicMock(name='MockInventory')
        mock_inventory._hosts_cache = dict()

        def _get_host(host_name):
            return None

        mock_inventory.get_host.side_effect = _get_host

        # TODO: can we use a real VariableManager?
        mock_variable_manager = MagicMock(name='MockVariableManager')
        mock_variable_manager.get_vars.return_value = dict()

        res = IncludedFile.process_include_results(results, mock_tqm, mock_iterator,
                                                   mock_inventory, fake_loader,
                                                   mock_variable_manager)
        self.assertIsInstance(res, list)
        self.assertEquals(res[0]._filename, os.path.join(os.getcwd(), 'include_test.yml'))
        self.assertEquals(res[1]._filename, os.path.join(os.getcwd(), 'other_include_test.yml'))

        self.assertEquals(res[0]._hosts, ['testhost1'])
        self.assertEquals(res[1]._hosts, ['testhost2'])

        self.assertEquals(res[0]._args, {})
        self.assertEquals(res[1]._args, {})
