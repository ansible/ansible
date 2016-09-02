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

        self._role_name = None
        self.statically_loaded = False
        self._from_files = {}
        self._block = block
        self._parent_role = role
        #self.requires_templating = False


    def get_block_list(self, variable_manager=None, loader=None):

        ri = RoleInclude.load(self._role_name, play=self._block._play, variable_manager=variable_manager, loader=loader)
        ri.vars.update(self.vars)

        #build role
        actual_role = Role.load(ri, self._block._play, parent_role=self._parent_role, from_files=self._from_files)

        # compile role
        blocks = actual_role.compile(play=self._block._play)

        # set parent to ensure proper inheritance
        for b in blocks:
            b._parent = self._block

        # updated available handlers in play
        self._block._play.handlers = self._block._play.handlers + actual_role.get_handler_blocks(play=self._block._play)

        return blocks

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):

        r = IncludeRole(block, role, task_include=task_include).load_data(data, variable_manager=variable_manager, loader=loader)
        args = r.preprocess_data(data).get('args', dict())

        #TODO: use more automated list: for builtin in r.get_attributes():
        # set built in's
        r._role_name =  args.get('name')
        for builtin in ['static', 'private']:
            if args.get(builtin):
                setattr(r, builtin, args.get(builtin))

        # build options for roles
        for key in ['tasks', 'vars', 'defaults']:
            from_key = key + '_from'
            if  args.get(from_key):
                r._from_files[key] = basename(args.get(from_key))

        return r.load_data(data, variable_manager=variable_manager, loader=loader)
