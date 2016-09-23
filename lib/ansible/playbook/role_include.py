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

from os.path import basename

from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.task import Task
from ansible.playbook.role import Role
from ansible.playbook.role.include import RoleInclude

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

    # private as this is a 'module options' vs a task property
    _static = FieldAttribute(isa='bool', default=None, private=True)
    _private = FieldAttribute(isa='bool', default=None, private=True)

    def __init__(self, block=None, role=None, task_include=None):

        super(IncludeRole, self).__init__(block=block, role=role, task_include=task_include)

        self.statically_loaded = False
        self._from_files = {}
        self._parent_role = role


    def get_block_list(self, play=None, variable_manager=None, loader=None):

        # only need play passed in when dynamic
        if play is None:
            myplay =  self._parent._play
        else:
            myplay = play

        ri = RoleInclude.load(self.name, play=myplay, variable_manager=variable_manager, loader=loader)
        ri.vars.update(self.vars)
        #ri._role_params.update(self.args) # jimi-c cant we avoid this?

        #build role
        actual_role = Role.load(ri, myplay, parent_role=self._parent_role, from_files=self._from_files)

        # compile role
        blocks = actual_role.compile(play=myplay)

        # set parent to ensure proper inheritance
        for b in blocks:
            b._parent = self._parent

        # updated available handlers in play
        myplay.handlers = myplay.handlers + actual_role.get_handler_blocks(play=myplay)

        return blocks

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):

        ir = IncludeRole(block, role, task_include=task_include).load_data(data, variable_manager=variable_manager, loader=loader)

        # set built in's
        attributes = frozenset(self._valid_attrs.keys())
        for builtin in attributes:
            if ir.args.get(builtin):
                setattr(ir, builtin, ir.args.get(builtin))

        # build options for role includes
        for key in ['tasks', 'vars', 'defaults']:
            from_key = key + '_from'
            if  ir.args.get(from_key):
                ir._from_files[key] = basename(ir.args.get(from_key))

        return ir.load_data(data, variable_manager=variable_manager, loader=loader)

    def copy(self, exclude_parent=False, exclude_tasks=False):

        new_me = super(IncludeRole, self).copy(exclude_parent=exclude_parent, exclude_tasks=exclude_tasks)
        new_me.statically_loaded = self.statically_loaded
        new_me.name = self.name
        new_me._from_files = self._from_files.copy()
        new_me._parent_role = self._parent_role

        return new_me
