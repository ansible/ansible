# Copyright (c) 2012 Red Hat, Inc. All rights reserved.
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

from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.task import Task
from ansible.playbook.role import Role
from ansible.playbook.role.include import RoleInclude

from ansible.errors import AnsibleError

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

__all__ = ['IncludeRole']


class IncludeRole(Task):

    """
    A Role include is derived from a regular role to handle the special
    circumstances related to the `- include_role: ...`
    """

    # =================================================================================
    # ATTRIBUTES

    _name   = FieldAttribute(isa='string', default=None)
    _tasks_from = FieldAttribute(isa='string', default=None)
    _static = FieldAttribute(isa='bool', default=None)
#    _private = FieldAttribute(isa='bool', default=None)

    def __init__(self, block=None, role=None, task_include=None):
        super(IncludeRole, self).__init__(block=block, role=role, task_include=task_include)
        self._included_role = Role(block._play)
        self._role_meta = None
        self._role_name = task_include
        self._block = block
        self._parent_role = role

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):

        try:
            r = IncludeRole(block=block, role=data['include_role']['name'] , task_include=None)
        except TypeError:
            raise AnsibleError("Not a valid role to include: %s" % data)

        return r.load_data(data, variable_manager=variable_manager, loader=loader)

    def load_data(self, data, variable_manager=None, loader=None):

        super(IncludeRole, self).load_data(data, variable_manager=variable_manager, loader=loader)

        ri = RoleInclude.load(data['include_role'], play=self._block._play, variable_manager=variable_manager, loader=loader)

        myrole = self._included_role.load(ri, self._block._play, parent_role=self._parent_role)

        return myrole.compile(play=self._block._play) # returns list of blocks
