
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

    BASE = ('name', 'role')  # directly assigned
    FROM_ARGS = ('tasks_from', 'vars_from', 'defaults_from')  # used to populate from dict in role
    OTHER_ARGS = ('private', 'allow_duplicates')  # assigned to matching property
    VALID_ARGS = tuple(frozenset(BASE + FROM_ARGS + OTHER_ARGS))  # all valid args

    # =================================================================================
    # ATTRIBUTES

    # private as this is a 'module options' vs a task property
    _allow_duplicates = FieldAttribute(isa='bool', default=True, private=True)
    _private = FieldAttribute(isa='bool', default=None, private=True)

    def __init__(self, block=None, role=None, task_include=None):

        super(IncludeRole, self).__init__(block=block, role=role, task_include=task_include)

        self._from_files = {}
        self._parent_role = role
        self._role_name = None
        self._role_path = None
        self._play = None
        self._role = None

    def get_block_list(self, play=None, variable_manager=None, loader=None):

        # only need play passed in when dynamic
        if play is None:
            myplay = self._parent._play
        else:
            myplay = play
        if variable_manager is None or loader is None:
            variable_manager = self.get_variable_manager()
        if loader is None:
            loader = variable_manager._loader

        ri = RoleInclude.load(self._role_name, play=myplay, variable_manager=variable_manager, loader=loader)
        ri.vars.update(self.vars)

        # build role
        if self.vars:
            v = self.vars.copy()
            # bypass vars from include_role itself
            for k in [
                'name', 'private', 'allow_duplicates',
                'defaults_from', 'tasks_from', 'vars_from'
            ]:
                v.pop(k, None)
            ri.vars.update(v)
        actual_role = Role.load(ri, myplay, parent_role=self._parent_role, from_files=self._from_files)
        actual_role._metadata.allow_duplicates = self.allow_duplicates

        # save this for later use
        self._role_path = actual_role._role_path
        self._role = actual_role
        if myplay is not None:
            self._play = myplay
            self._play.register_dynamic_role(self)

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

        # Validate options
        my_arg_names = frozenset(ir.args.keys())

        # name is needed, or use role as alias
        ir._role_name = ir.args.get('name', ir.args.get('role'))
        if ir._role_name is None:
            raise AnsibleParserError("'name' is a required field for %s." % ir.action)

        # validate bad args, otherwise we silently ignore
        bad_opts = my_arg_names.difference(IncludeRole.VALID_ARGS)
        if bad_opts:
            raise AnsibleParserError('Invalid options for %s: %s' % (ir.action, ','.join(list(bad_opts))))

        # build options for role includes
        for key in my_arg_names.intersection(IncludeRole.FROM_ARGS):
            from_key = key.replace('_from', '')
            ir._from_files[from_key] = basename(ir.args.get(key))

        # manual list as otherwise the options would set other task parameters we don't want.
        for option in my_arg_names.intersection(IncludeRole.OTHER_ARGS):
            setattr(ir, option, ir.args.get(option))

        return ir

    def copy(self, exclude_parent=False, exclude_tasks=False):

        # save our attrs
        role = self._role
        parentrole = self._parent_role
        parent = self._parent
        play = self._play

        # be smaller for parent methods to shallow copy
        self._role = None
        self._parent = None
        self._parent_role = None
        self._play = None

        new_me = super(IncludeRole, self).copy(exclude_parent=exclude_parent, exclude_tasks=exclude_tasks)

        # restore our state
        self._parent_role = parentrole
        self._parent = parent
        self._play = play
        self._role = role

        new_me.statically_loaded = self.statically_loaded
        new_me._from_files = self._from_files.copy()
        new_me._parent_role = self._parent_role
        new_me._role_name = self._role_name
        new_me._role_path = self._role_path
        new_me._role = self._role
        new_me.private = self.private
        new_me._play = self._play

        return new_me

    @property
    def is_loaded(self):
        return self._role is not None

    def get_include_params(self):
        v = super(IncludeRole, self).get_include_params()
        if self._parent_role:
            v.update(self._parent_role.get_role_params())
        return v

    def get_default_vars(self, dep_chain=None):
        if not self.is_loaded:
            return dict()
        if dep_chain is None:
            dep_chain = self.get_dep_chain()
        return self._role.get_default_vars(dep_chain=dep_chain)

    def get_vars(self, include_params=True):
        all_vars = TaskInclude.get_vars(self, include_params=include_params)
        if self.is_loaded:  # not yet loaded skip
            all_vars.update(
                self._role.get_vars(include_params=include_params)
            )
        return all_vars

    def serialize(self, no_play=False):
        data = super(IncludeRole, self).serialize()
        if not self._squashed and not self._finalized:
            data['_irole_name'] = self._role_name
            if self._parent_role:
                data['_irole_prole'] = self._parent_role.serialize()
            data['_irole_path'] = self._role_path
            if self._role:
                data['_irole_drole'] = self._role.serialize()
            if self._play and not no_play:
                # avoid deepcopy recurse errors
                self._play.unregister_dynamic_role(self)
                data['_irole_play'] = self._play.serialize(
                    skip_dynamic_roles=True)
                self._play.register_dynamic_role(self)
        return data

    def deserialize(self, data, play=None, include_deps=True):
        from ansible.playbook.play import Play
        from ansible.playbook.role import Role
        self._role_name = data.get('_irole_name', '')
        self._role_path = data.get('_irole_path', '')
        if play is None and '_irole_play' in data:
            play = Play()
            play.deserialize(data['_irole_play'])
            del data['_irole_play']
        if play is not None:
            setattr(self, '_play', play)
        if '_irole_drole' in data:
            r = Role()
            r.deserialize(data['_irole_drole'])
            setattr(self, '_role', r)
            del data['_irole_drole']
        if '_irole_prole' in data:
            r = Role()
            r.deserialize(data['_irole_prole'])
            setattr(self, '_parent_role', r)
            del data['_irole_prole']
        if play is not None:
            play.register_dynamic_role(self)
        super(IncludeRole, self).deserialize(data)

    def __setstate__(self, sr):
        self.__init__()
        self.deserialize(sr)

    def __getstate__(self):
        sr = self.serialize()
        return sr

    def __deepcopy__(self, memo):
        ret = self.deserialize(self.serialize())
        memo[id(self)] = ret
        return ret
