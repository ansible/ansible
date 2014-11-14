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


import os

from types import NoneType

from ansible.errors import AnsibleParserError
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject


def load_list_of_blocks(ds, parent_block=None, role=None, task_include=None, use_handlers=False, variable_manager=None, loader=None):
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
            b = Block.load(
                block,
                parent_block=parent_block,
                role=role,
                task_include=task_include,
                use_handlers=use_handlers,
                variable_manager=variable_manager,
                loader=loader
            )
            block_list.append(b)

    return block_list


def load_list_of_tasks(ds, block=None, role=None, task_include=None, use_handlers=False, variable_manager=None, loader=None):
    '''
    Given a list of task datastructures (parsed from YAML),
    return a list of Task() or TaskInclude() objects.
    '''

    # we import here to prevent a circular dependency with imports
    from ansible.playbook.handler import Handler
    from ansible.playbook.task import Task
    from ansible.playbook.task_include import TaskInclude

    assert type(ds) == list

    task_list = []
    for task in ds:
        if not isinstance(task, dict):
            raise AnsibleParserError("task/handler entries must be dictionaries (got a %s)" % type(task), obj=ds)

        if 'include' in task:
            cur_basedir = None
            if isinstance(task, AnsibleBaseYAMLObject) and loader:
                pos_info = task.get_position_info()
                new_basedir = os.path.dirname(pos_info[0])
                cur_basedir = loader.get_basedir()
                loader.set_basedir(new_basedir)

            t = TaskInclude.load(
                task,
                block=block,
                role=role,
                task_include=task_include,
                use_handlers=use_handlers,
                loader=loader
            )

            if cur_basedir and loader:
                loader.set_basedir(cur_basedir)
        else:
            if use_handlers:
                t = Handler.load(task, block=block, role=role, task_include=task_include, variable_manager=variable_manager, loader=loader)
            else:
                t = Task.load(task, block=block, role=role, task_include=task_include, variable_manager=variable_manager, loader=loader)

        task_list.append(t)

    return task_list


def load_list_of_roles(ds, variable_manager=None, loader=None):
    '''
    Loads and returns a list of RoleInclude objects from the datastructure
    list of role definitions
    '''

    # we import here to prevent a circular dependency with imports
    from ansible.playbook.role.include import RoleInclude

    assert isinstance(ds, list)

    roles = []
    for role_def in ds:
        i = RoleInclude.load(role_def, variable_manager=variable_manager, loader=loader)
        roles.append(i)

    return roles

def compile_block_list(block_list):
    '''
    Given a list of blocks, compile them into a flat list of tasks
    '''

    task_list = []

    for block in block_list:
        task_list.extend(block.compile())

    return task_list

