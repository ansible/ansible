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

from ansible.playbook.base import Base
from ansible.playbook.task import Task
from ansible.playbook.attribute import Attribute, FieldAttribute

class Block(Base):

    # TODO: FIXME: block/rescue/always should be enough
    _begin     = FieldAttribute(isa='list')
    _rescue    = FieldAttribute(isa='list')
    _end       = FieldAttribute(isa='list')
    _otherwise = FieldAttribute(isa='list')

    def __init__(self, role=None):
        self.role = role
        super(Block, self).__init__()

    def get_variables(self):
        # blocks do not (currently) store any variables directly,
        # so we just return an empty dict here
        return dict()

    @staticmethod
    def load(data, role=None):
        b = Block(role=role)
        return b.load_data(data)

    def _load_list_of_tasks(self, ds):
        assert type(ds) == list
        task_list = []
        for task in ds:
            t = Task.load(task)
            task_list.append(t)
        return task_list

    def _load_begin(self, attr, ds):
        return self._load_list_of_tasks(ds)

    def _load_rescue(self, attr, ds):
        return self._load_list_of_tasks(ds)

    def _load_end(self, attr, ds):
        return self._load_list_of_tasks(ds)

    def _load_otherwise(self, attr, ds):
        return self._load_list_of_tasks(ds)

