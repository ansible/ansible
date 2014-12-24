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

from ansible.playbook.attribute import Attribute, FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.helpers import load_list_of_tasks
from ansible.playbook.task_include import TaskInclude

class Block(Base):

    _block     = FieldAttribute(isa='list')
    _rescue    = FieldAttribute(isa='list')
    _always    = FieldAttribute(isa='list')
    _tags      = FieldAttribute(isa='list', default=[])
    _when      = FieldAttribute(isa='list', default=[])

    # for future consideration? this would be functionally
    # similar to the 'else' clause for exceptions
    #_otherwise = FieldAttribute(isa='list')

    def __init__(self, parent_block=None, role=None, task_include=None):
        self._parent_block = parent_block
        self._role = role
        self._task_include = task_include
        super(Block, self).__init__()

    def get_variables(self):
        # blocks do not (currently) store any variables directly,
        # so we just return an empty dict here
        return dict()

    @staticmethod
    def load(data, parent_block=None, role=None, task_include=None, loader=None):
        b = Block(parent_block=parent_block, role=role, task_include=task_include)
        return b.load_data(data, loader=loader)

    def munge(self, ds):
        '''
        If a simple task is given, an implicit block for that single task
        is created, which goes in the main portion of the block
        '''
        is_block = False
        for attr in ('block', 'rescue', 'always'):
            if attr in ds:
                is_block = True
                break
        if not is_block:
            if isinstance(ds, list):
                return dict(block=ds)
            else:
                return dict(block=[ds])
        return ds

    def _load_block(self, attr, ds):
        return load_list_of_tasks(ds, block=self, loader=self._loader)

    def _load_rescue(self, attr, ds):
        return load_list_of_tasks(ds, block=self, loader=self._loader)

    def _load_always(self, attr, ds):
        return load_list_of_tasks(ds, block=self, loader=self._loader)

    # not currently used
    #def _load_otherwise(self, attr, ds):
    #    return self._load_list_of_tasks(ds, block=self, loader=self._loader)

    def compile(self):
        '''
        Returns the task list for this object
        '''

        task_list = []
        for task in self.block:
            # FIXME: evaulate task tags/conditionals here
            task_list.extend(task.compile())

        return task_list
