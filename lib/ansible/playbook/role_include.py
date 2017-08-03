
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

from ansible.errors import AnsibleParserError
from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.task_include import TaskInclude
from ansible.playbook.role import Role
from ansible.playbook.role.include import RoleInclude

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

__all__ = ['IncludeRole']


class IncludeRole(TaskInclude):

    """
    A Role include is derived from a regular role to handle the special
    circumstances related to the `- include_role: ...`
    """

    # =================================================================================
    # ATTRIBUTES

    # private as this is a 'module options' vs a task property
    _allow_duplicates = FieldAttribute(isa='bool', default=True, private=True)
    _private = FieldAttribute(isa='bool', default=None, private=True)
    _static = FieldAttribute(isa='bool', default=None)

    def __init__(self, block=None, role=None, task_include=None):

        super(IncludeRole, self).__init__(block=block, role=role, task_include=task_include)

        self._from_files = {}
        self._parent_role = role
        self._role_name = None
        self._role_path = None

    def get_block_list(self, play=None, variable_manager=None, loader=None):

        # only need play passed in when dynamic
        if play is None:
            myplay = self._parent._play
        else:
            myplay = play

        ri = RoleInclude.load(self._role_name, play=myplay, variable_manager=variable_manager, loader=loader)
        ri.vars.update(self.vars)

        # build role
        actual_role = Role.load(ri, myplay, parent_role=self._parent_role, from_files=self._from_files)
        actual_role._metadata.allow_duplicates = self.allow_duplicates

        # save this for later use
        self._role_path = actual_role._role_path

        # compile role with parent roles as dependencies to ensure they inherit
        # variables
        if not self._parent_role:
            dep_chain = []
        else:
            dep_chain = list(self._parent_role._parents)
            dep_chain.append(self._parent_role)

        blocks = actual_role.compile(play=myplay, dep_chain=dep_chain)
        for b in blocks:
            b._parent = self

        # updated available handlers in play
        handlers = actual_role.get_handler_blocks(play=myplay)
        myplay.handlers = myplay.handlers + handlers
        return blocks, handlers

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):

        ir = IncludeRole(block, role, task_include=task_include).load_data(data, variable_manager=variable_manager, loader=loader)

        # Process options
        # name is needed, or use role as alias
        ir._role_name = ir.args.get('name', ir.args.get('role'))
        if ir._role_name is None:
            raise AnsibleParserError("'name' is a required field for include_role.")

        # build options for role includes
        for key in ['tasks', 'vars', 'defaults']:
            from_key = '%s_from' % key
            if ir.args.get(from_key):
                ir._from_files[key] = basename(ir.args.get(from_key))

        # FIXME: find a way to make this list come from object ( attributes does not work as per below)
        # manual list as otherwise the options would set other task parameters we don't want.
        for option in ['private', 'allow_duplicates']:
            if option in ir.args:
                setattr(ir, option, ir.args.get(option))

        return ir

    def copy(self, exclude_parent=False, exclude_tasks=False):

        new_me = super(IncludeRole, self).copy(exclude_parent=exclude_parent, exclude_tasks=exclude_tasks)
        new_me.statically_loaded = self.statically_loaded
        new_me._from_files = self._from_files.copy()
        new_me._parent_role = self._parent_role
        new_me._role_name = self._role_name
        new_me._role_path = self._role_path

        return new_me

    def get_include_params(self):
        v = super(IncludeRole, self).get_include_params()
        if self._parent_role:
            v.update(self._parent_role.get_role_params())
        return v
