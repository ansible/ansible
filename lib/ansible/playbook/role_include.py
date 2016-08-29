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

    _name   = FieldAttribute(isa='string', default=None)
    _tasks_from = FieldAttribute(isa='string', default=None)

    # these should not be changeable?
    _static = FieldAttribute(isa='bool', default=False)
    _private = FieldAttribute(isa='bool', default=True)

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):

        r = IncludeRole().load_data(data, variable_manager=variable_manager, loader=loader)
        args = r.preprocess_data(data).get('args', dict())

        ri = RoleInclude.load(args.get('name'), play=block._play, variable_manager=variable_manager, loader=loader)
        ri.vars.update(r.vars)

        # build options for roles
        from_files = {}
        for key in ['tasks', 'vars', 'defaults']:
            from_key = key + '_from'
            if  args.get(from_key):
                from_files[key] = basename(args.get(from_key))

        #build role
        actual_role = Role.load(ri, block._play, parent_role=role, from_files=from_files)

        # compile role
        blocks = actual_role.compile(play=block._play)

        # set parent to ensure proper inheritance
        for b in blocks:
            b._parent = block

        # updated available handlers in play
        block._play.handlers = block._play.handlers + actual_role.get_handler_blocks(play=block._play)

        return blocks
