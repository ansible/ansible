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

from types import NoneType


def load_list_of_blocks(ds, role=None, loader=None):
    '''
    Given a list of mixed task/block data (parsed from YAML),
    return a list of Block() objects, where implicit blocks
    are created for each bare Task.
    '''

    # we import here to prevent a circular dependency with imports
    from ansible.playbook.block import Block

    assert type(ds) in (list, NoneType)

    block_list = []
    if ds:
        for block in ds:
            b = Block.load(block, role=role, loader=loader)
            block_list.append(b)

    return block_list

def load_list_of_tasks(ds, block=None, role=None, loader=None):
    '''
    Given a list of task datastructures (parsed from YAML),
    return a list of Task() objects.
    '''

    # we import here to prevent a circular dependency with imports
    from ansible.playbook.task import Task

    assert type(ds) == list

    task_list = []
    for task in ds:
        t = Task.load(task, block=block, role=role, loader=loader)
        task_list.append(t)

    return task_list

def load_list_of_roles(ds, loader=None):
    '''
    Loads and returns a list of RoleInclude objects from the datastructure
    list of role definitions
    '''

    # we import here to prevent a circular dependency with imports
    from ansible.playbook.role.include import RoleInclude

    assert isinstance(ds, list)

    roles = []
    for role_def in ds:
        i = RoleInclude.load(role_def, loader=loader)
        roles.append(i)

    return roles

