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

from ansible.playbook.task import Task
from ansible.playbook.task_include import TaskInclude
from ansible.executor import task_result

from ansible.playbook.included_file import IncludedFile


@pytest.fixture
def mock_inventory():
    mock_inventory = MagicMock(name='MockInventory')
    mock_host1 = MagicMock()
    mock_host1.name = "testhost1"
    mock_host2 = MagicMock()
    mock_host2.name = "testhost2"
    mock_inventory.get_host.side_effect = lambda x: {"testhost1": mock_host1, "testhost2": mock_host2}.get(x, None)
    return mock_inventory


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


def test_included_file_instantiation():
    filename = 'somefile.yml'

    inc_file = IncludedFile(filename=filename, args={}, vars={}, task=None)

    assert isinstance(inc_file, IncludedFile)
    assert inc_file._filename == filename
    assert inc_file._args == {}
    assert inc_file._vars == {}
    assert inc_file._task is None


def test_process_include_results(mock_inventory, mock_iterator, mock_variable_manager):
    hostname1 = "testhost1"
    hostname2 = "testhost2"

    parent_task_ds = {'debug': 'msg=foo'}
    parent_task = Task.load(parent_task_ds)
    parent_task._play = None

    task_ds = {'include': 'include_test.yml'}
    # The task in the TaskResult has to be a TaskInclude so it has a .static attr
    loaded_task = TaskInclude.load(task_ds, task_include=parent_task)

    mock_iterator.get_last_task_for_host.side_effect = lambda x: {hostname1: loaded_task, hostname2: loaded_task}.get(x.name)

    return_data = {'include': 'include_test.yml'}
    result1 = {
        'host_name': hostname1,
        'task_uuid': loaded_task._uuid,
        'status_type': 'ok',
        'status_msg': '',
        'original_result': return_data,
        'changed': True,
        'role_ran': False,
        'needs_debug': False,
    }
    result2 = {
        'host_name': hostname2,
        'task_uuid': loaded_task._uuid,
        'status_type': 'ok',
        'status_msg': '',
        'original_result': return_data,
        'changed': True,
        'role_ran': False,
        'needs_debug': False,
    }

    results = [result1, result2]

    fake_loader = DictDataLoader({'include_test.yml': ""})

    res = IncludedFile.process_include_results(results, mock_inventory, mock_iterator, fake_loader, mock_variable_manager)
    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]._filename == os.path.join(os.getcwd(), 'include_test.yml')
    assert res[0]._hosts == [mock_inventory.get_host(hostname1), mock_inventory.get_host(hostname2)]
    assert res[0]._args == {}
    assert res[0]._vars == {}


def test_process_include_diff_files(mock_inventory, mock_iterator, mock_variable_manager):
    hostname1 = "testhost1"
    hostname2 = "testhost2"

    parent_task_ds = {'debug': 'msg=foo'}
    parent_task = Task.load(parent_task_ds)
    parent_task._play = None

    task_ds = {'include': 'include_test.yml'}
    # The task in the TaskResult has to be a TaskInclude so it has a .static attr
    loaded_task = TaskInclude.load(task_ds, task_include=parent_task)
    loaded_task._play = None

    child_task_ds = {'include': 'other_include_test.yml'}
    loaded_child_task = TaskInclude.load(child_task_ds, task_include=loaded_task)
    loaded_child_task._play = None

    mock_iterator.get_last_task_for_host.side_effect = lambda x: {hostname1: loaded_task, hostname2: loaded_child_task}.get(x.name)

    return_data = {'include': 'include_test.yml'}
    result1 = {
        'host_name': hostname1,
        'task_uuid': loaded_task._uuid,
        'status_type': 'ok',
        'status_msg': '',
        'original_result': return_data,
        'changed': True,
        'role_ran': False,
        'needs_debug': False,
    }
    return_data = {'include': 'other_include_test.yml'}
    result2 = {
        'host_name': hostname2,
        'task_uuid': loaded_child_task._uuid,
        'status_type': 'ok',
        'status_msg': '',
        'original_result': return_data,
        'changed': True,
        'role_ran': False,
        'needs_debug': False,
    }

    results = [result1, result2]

    fake_loader = DictDataLoader({'include_test.yml': "",
                                  'other_include_test.yml': ""})

    res = IncludedFile.process_include_results(results, mock_inventory, mock_iterator, fake_loader, mock_variable_manager)
    assert isinstance(res, list)
    assert res[0]._filename == os.path.join(os.getcwd(), 'include_test.yml')
    assert res[1]._filename == os.path.join(os.getcwd(), 'other_include_test.yml')

    assert res[0]._hosts == [mock_inventory.get_host(hostname1)]
    assert res[1]._hosts == [mock_inventory.get_host(hostname2)]

    assert res[0]._args == {}
    assert res[1]._args == {}

    assert res[0]._vars == {}
    assert res[1]._vars == {}


def test_process_include_simulate_free(mock_inventory, mock_iterator, mock_variable_manager):
    hostname1 = "testhost1"
    hostname2 = "testhost2"

    parent_task_ds = {'debug': 'msg=foo'}
    parent_task1 = Task.load(parent_task_ds)
    parent_task2 = Task.load(parent_task_ds)

    parent_task1._play = None
    parent_task2._play = None

    task_ds = {'include': 'include_test.yml'}
    loaded_task1 = TaskInclude.load(task_ds, task_include=parent_task1)
    loaded_task2 = TaskInclude.load(task_ds, task_include=parent_task2)

    mock_iterator.get_last_task_for_host.side_effect = lambda x: {hostname1: loaded_task1, hostname2: loaded_task2}.get(x.name)

    return_data = {'include': 'include_test.yml'}
    # The task in the TaskResult has to be a TaskInclude so it has a .static attr
    result1 = {
        'host_name': hostname1,
        'task_uuid': loaded_task1._uuid,
        'status_type': 'ok',
        'status_msg': '',
        'original_result': return_data,
        'changed': True,
        'role_ran': False,
        'needs_debug': False,
    }
    result2 = {
        'host_name': hostname2,
        'task_uuid': loaded_task2._uuid,
        'status_type': 'ok',
        'status_msg': '',
        'original_result': return_data,
        'changed': True,
        'role_ran': False,
        'needs_debug': False,
    }
    results = [result1, result2]

    fake_loader = DictDataLoader({'include_test.yml': ""})

    res = IncludedFile.process_include_results(results, mock_inventory, mock_iterator, fake_loader, mock_variable_manager)
    assert isinstance(res, list)
    assert len(res) == 2
    assert res[0]._filename == os.path.join(os.getcwd(), 'include_test.yml')
    assert res[1]._filename == os.path.join(os.getcwd(), 'include_test.yml')

    assert res[0]._hosts == [mock_inventory.get_host(hostname1)]
    assert res[1]._hosts == [mock_inventory.get_host(hostname2)]

    assert res[0]._args == {}
    assert res[1]._args == {}

    assert res[0]._vars == {}
    assert res[1]._vars == {}
