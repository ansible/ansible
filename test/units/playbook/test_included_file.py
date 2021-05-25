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

import pytest

from units.compat.mock import MagicMock
from units.mock.loader import DictDataLoader

from ansible.playbook.block import Block
from ansible.playbook.task import Task
from ansible.playbook.task_include import TaskInclude
from ansible.playbook.role_include import IncludeRole
from ansible.executor import task_result

from ansible.playbook.included_file import IncludedFile
from ansible.errors import AnsibleParserError


@pytest.fixture
def mock_iterator():
    mock_iterator = MagicMock(name='MockIterator')
    mock_iterator._play = MagicMock(name='MockPlay')
    return mock_iterator


@pytest.fixture
def mock_variable_manager():
    # TODO: can we use a real VariableManager?
    mock_variable_manager = MagicMock(name='MockVariableManager')
    mock_variable_manager.get_vars.return_value = dict()
    return mock_variable_manager


def test_equals_ok():
    uuid = '111-111'
    parent = MagicMock(name='MockParent')
    parent._uuid = uuid
    task = MagicMock(name='MockTask')
    task._uuid = uuid
    task._parent = parent
    inc_a = IncludedFile('a.yml', {}, {}, task)
    inc_b = IncludedFile('a.yml', {}, {}, task)
    assert inc_a == inc_b


def test_equals_different_tasks():
    parent = MagicMock(name='MockParent')
    parent._uuid = '111-111'
    task_a = MagicMock(name='MockTask')
    task_a._uuid = '11-11'
    task_a._parent = parent
    task_b = MagicMock(name='MockTask')
    task_b._uuid = '22-22'
    task_b._parent = parent
    inc_a = IncludedFile('a.yml', {}, {}, task_a)
    inc_b = IncludedFile('a.yml', {}, {}, task_b)
    assert inc_a != inc_b


def test_equals_different_parents():
    parent_a = MagicMock(name='MockParent')
    parent_a._uuid = '111-111'
    parent_b = MagicMock(name='MockParent')
    parent_b._uuid = '222-222'
    task_a = MagicMock(name='MockTask')
    task_a._uuid = '11-11'
    task_a._parent = parent_a
    task_b = MagicMock(name='MockTask')
    task_b._uuid = '11-11'
    task_b._parent = parent_b
    inc_a = IncludedFile('a.yml', {}, {}, task_a)
    inc_b = IncludedFile('a.yml', {}, {}, task_b)
    assert inc_a != inc_b


def test_included_file_instantiation():
    filename = 'somefile.yml'

    inc_file = IncludedFile(filename=filename, args={}, vars={}, task=None)

    assert isinstance(inc_file, IncludedFile)
    assert inc_file._filename == filename
    assert inc_file._args == {}
    assert inc_file._vars == {}
    assert inc_file._task is None


def test_process_include_results(mock_iterator, mock_variable_manager):
    hostname = "testhost1"
    hostname2 = "testhost2"

    parent_task_ds = {'debug': 'msg=foo'}
    parent_task = Task.load(parent_task_ds)
    parent_task._play = None

    task_ds = {'include': 'include_test.yml'}
    loaded_task = TaskInclude.load(task_ds, task_include=parent_task)

    return_data = {'include': 'include_test.yml'}
    # The task in the TaskResult has to be a TaskInclude so it has a .static attr
    result1 = task_result.TaskResult(host=hostname, task=loaded_task, return_data=return_data)
    result2 = task_result.TaskResult(host=hostname2, task=loaded_task, return_data=return_data)
    results = [result1, result2]

    fake_loader = DictDataLoader({'include_test.yml': ""})

    res = IncludedFile.process_include_results(results, mock_iterator, fake_loader, mock_variable_manager)
    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]._filename == os.path.join(os.getcwd(), 'include_test.yml')
    assert res[0]._hosts == ['testhost1', 'testhost2']
    assert res[0]._args == {}
    assert res[0]._vars == {}


def test_process_include_diff_files(mock_iterator, mock_variable_manager):
    hostname = "testhost1"
    hostname2 = "testhost2"

    parent_task_ds = {'debug': 'msg=foo'}
    parent_task = Task.load(parent_task_ds)
    parent_task._play = None

    task_ds = {'include': 'include_test.yml'}
    loaded_task = TaskInclude.load(task_ds, task_include=parent_task)
    loaded_task._play = None

    child_task_ds = {'include': 'other_include_test.yml'}
    loaded_child_task = TaskInclude.load(child_task_ds, task_include=loaded_task)
    loaded_child_task._play = None

    return_data = {'include': 'include_test.yml'}
    # The task in the TaskResult has to be a TaskInclude so it has a .static attr
    result1 = task_result.TaskResult(host=hostname, task=loaded_task, return_data=return_data)

    return_data = {'include': 'other_include_test.yml'}
    result2 = task_result.TaskResult(host=hostname2, task=loaded_child_task, return_data=return_data)
    results = [result1, result2]

    fake_loader = DictDataLoader({'include_test.yml': "",
                                  'other_include_test.yml': ""})

    res = IncludedFile.process_include_results(results, mock_iterator, fake_loader, mock_variable_manager)
    assert isinstance(res, list)
    assert res[0]._filename == os.path.join(os.getcwd(), 'include_test.yml')
    assert res[1]._filename == os.path.join(os.getcwd(), 'other_include_test.yml')

    assert res[0]._hosts == ['testhost1']
    assert res[1]._hosts == ['testhost2']

    assert res[0]._args == {}
    assert res[1]._args == {}

    assert res[0]._vars == {}
    assert res[1]._vars == {}


def test_process_include_simulate_free(mock_iterator, mock_variable_manager):
    hostname = "testhost1"
    hostname2 = "testhost2"

    parent_task_ds = {'debug': 'msg=foo'}
    parent_task1 = Task.load(parent_task_ds)
    parent_task2 = Task.load(parent_task_ds)

    parent_task1._play = None
    parent_task2._play = None

    task_ds = {'include': 'include_test.yml'}
    loaded_task1 = TaskInclude.load(task_ds, task_include=parent_task1)
    loaded_task2 = TaskInclude.load(task_ds, task_include=parent_task2)

    return_data = {'include': 'include_test.yml'}
    # The task in the TaskResult has to be a TaskInclude so it has a .static attr
    result1 = task_result.TaskResult(host=hostname, task=loaded_task1, return_data=return_data)
    result2 = task_result.TaskResult(host=hostname2, task=loaded_task2, return_data=return_data)
    results = [result1, result2]

    fake_loader = DictDataLoader({'include_test.yml': ""})

    res = IncludedFile.process_include_results(results, mock_iterator, fake_loader, mock_variable_manager)
    assert isinstance(res, list)
    assert len(res) == 2
    assert res[0]._filename == os.path.join(os.getcwd(), 'include_test.yml')
    assert res[1]._filename == os.path.join(os.getcwd(), 'include_test.yml')

    assert res[0]._hosts == ['testhost1']
    assert res[1]._hosts == ['testhost2']

    assert res[0]._args == {}
    assert res[1]._args == {}

    assert res[0]._vars == {}
    assert res[1]._vars == {}


def test_process_include_simulate_free_block_role_tasks(mock_iterator,
                                                        mock_variable_manager):
    """Test loading the same role returns different included files

    In the case of free, we may end up with included files from roles that
    have the same parent but are different tasks. Previously the comparison
    for equality did not check if the tasks were the same and only checked
    that the parents were the same. This lead to some tasks being run
    incorrectly and some tasks being silient dropped."""

    fake_loader = DictDataLoader({
        'include_test.yml': "",
        '/etc/ansible/roles/foo_role/tasks/task1.yml': """
            - debug: msg=task1
        """,
        '/etc/ansible/roles/foo_role/tasks/task2.yml': """
            - debug: msg=task2
        """,
    })

    hostname = "testhost1"
    hostname2 = "testhost2"

    role1_ds = {
        'name': 'task1 include',
        'include_role': {
            'name': 'foo_role',
            'tasks_from': 'task1.yml'
        }
    }
    role2_ds = {
        'name': 'task2 include',
        'include_role': {
            'name': 'foo_role',
            'tasks_from': 'task2.yml'
        }
    }
    parent_task_ds = {
        'block': [
            role1_ds,
            role2_ds
        ]
    }
    parent_block = Block.load(parent_task_ds, loader=fake_loader)

    parent_block._play = None

    include_role1_ds = {
        'include_args': {
            'name': 'foo_role',
            'tasks_from': 'task1.yml'
        }
    }
    include_role2_ds = {
        'include_args': {
            'name': 'foo_role',
            'tasks_from': 'task2.yml'
        }
    }

    include_role1 = IncludeRole.load(role1_ds,
                                     block=parent_block,
                                     loader=fake_loader)
    include_role2 = IncludeRole.load(role2_ds,
                                     block=parent_block,
                                     loader=fake_loader)

    result1 = task_result.TaskResult(host=hostname,
                                     task=include_role1,
                                     return_data=include_role1_ds)
    result2 = task_result.TaskResult(host=hostname2,
                                     task=include_role2,
                                     return_data=include_role2_ds)
    results = [result1, result2]

    res = IncludedFile.process_include_results(results,
                                               mock_iterator,
                                               fake_loader,
                                               mock_variable_manager)
    assert isinstance(res, list)
    # we should get two different includes
    assert len(res) == 2
    assert res[0]._filename == 'foo_role'
    assert res[1]._filename == 'foo_role'
    # with different tasks
    assert res[0]._task != res[1]._task

    assert res[0]._hosts == ['testhost1']
    assert res[1]._hosts == ['testhost2']

    assert res[0]._args == {}
    assert res[1]._args == {}

    assert res[0]._vars == {}
    assert res[1]._vars == {}


def test_empty_raw_params():
    parent_task_ds = {'debug': 'msg=foo'}
    parent_task = Task.load(parent_task_ds)
    parent_task._play = None

    task_ds_list = [
        {
            'include': ''
        },
        {
            'include_tasks': ''
        },
        {
            'import_tasks': ''
        }
    ]
    for task_ds in task_ds_list:
        with pytest.raises(AnsibleParserError):
            TaskInclude.load(task_ds, task_include=parent_task)
