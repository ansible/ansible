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

from ansible.compat.six import string_types

from ansible.errors import AnsibleParserError

from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.become import Become
from ansible.playbook.block import Block
from ansible.playbook.helpers import load_list_of_blocks, load_list_of_roles
from ansible.playbook.role import Role
from ansible.playbook.taggable import Taggable
from ansible.vars import preprocess_vars

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


__all__ = ['Play']


class Play(Base, Taggable, Become):

    """
    A play is a language feature that represents a list of roles and/or
    task/handler blocks to execute on a given set of hosts.

    Usage:

       Play.load(datastructure) -> Play
       Play.something(...)
    """

    # =================================================================================
    # Connection-Related Attributes

    # TODO: generalize connection
    _accelerate          = FieldAttribute(isa='bool', default=False, always_post_validate=True)
    _accelerate_ipv6     = FieldAttribute(isa='bool', default=False, always_post_validate=True)
    _accelerate_port     = FieldAttribute(isa='int', default=5099, always_post_validate=True)

    # Connection
    _gather_facts        = FieldAttribute(isa='bool', default=None, always_post_validate=True)
    _hosts               = FieldAttribute(isa='list', required=True, listof=string_types, always_post_validate=True)
    _name                = FieldAttribute(isa='string', default='', always_post_validate=True)

    # Variable Attributes
    _vars_files          = FieldAttribute(isa='list', default=[], priority=99)
    _vars_prompt         = FieldAttribute(isa='list', default=[], always_post_validate=True)
    _vault_password      = FieldAttribute(isa='string', always_post_validate=True)

    # Role Attributes
    _roles               = FieldAttribute(isa='list', default=[], priority=90)

    # Block (Task) Lists Attributes
    _handlers            = FieldAttribute(isa='list', default=[])
    _pre_tasks           = FieldAttribute(isa='list', default=[])
    _post_tasks          = FieldAttribute(isa='list', default=[])
    _tasks               = FieldAttribute(isa='list', default=[])

    # Flag/Setting Attributes
    _any_errors_fatal    = FieldAttribute(isa='bool', default=False, always_post_validate=True)
    _force_handlers      = FieldAttribute(isa='bool', always_post_validate=True)
    _max_fail_percentage = FieldAttribute(isa='percent', always_post_validate=True)
    _serial              = FieldAttribute(isa='string',  always_post_validate=True)
    _strategy            = FieldAttribute(isa='string', default='linear', always_post_validate=True)

    # =================================================================================

    def __init__(self):
        super(Play, self).__init__()

        self._included_path = None
        self.ROLE_CACHE = {}

    def __repr__(self):
        return self.get_name()

    def get_name(self):
        ''' return the name of the Play '''
        return self._attributes.get('name')

    @staticmethod
    def load(data, variable_manager=None, loader=None):
        if ('name' not in data or data['name'] is None) and 'hosts' in data:
            if isinstance(data['hosts'], list):
                data['name'] = ','.join(data['hosts'])
            else:
                 data['name'] = data['hosts']
        p = Play()
        return p.load_data(data, variable_manager=variable_manager, loader=loader)

    def preprocess_data(self, ds):
        '''
        Adjusts play datastructure to cleanup old/legacy items
        '''

        assert isinstance(ds, dict)

        # The use of 'user' in the Play datastructure was deprecated to
        # line up with the same change for Tasks, due to the fact that
        # 'user' conflicted with the user module.
        if 'user' in ds:
            # this should never happen, but error out with a helpful message
            # to the user if it does...
            if 'remote_user' in ds:
                raise AnsibleParserError("both 'user' and 'remote_user' are set for %s."
                        " The use of 'user' is deprecated, and should be removed" % self.get_name(), obj=ds)

            ds['remote_user'] = ds['user']
            del ds['user']

        return super(Play, self).preprocess_data(ds)

    def _load_hosts(self, attr, ds):
        '''
        Loads the hosts from the given datastructure, which might be a list
        or a simple string. We also switch integers in this list back to strings,
        as the YAML parser will turn things that look like numbers into numbers.
        '''

        if isinstance(ds, (string_types, int)):
            ds = [ ds ]

        if not isinstance(ds, list):
            raise AnsibleParserError("'hosts' must be specified as a list or a single pattern", obj=ds)

        # YAML parsing of things that look like numbers may have
        # resulted in integers showing up in the list, so convert
        # them back to strings to prevent problems
        for idx,item in enumerate(ds):
            if isinstance(item, int):
                ds[idx] = "%s" % item

        return ds

    def _load_tasks(self, attr, ds):
        '''
        Loads a list of blocks from a list which may be mixed tasks/blocks.
        Bare tasks outside of a block are given an implicit block.
        '''
        try:
            return load_list_of_blocks(ds=ds, play=self, variable_manager=self._variable_manager, loader=self._loader)
        except AssertionError:
            raise AnsibleParserError("A malformed block was encountered.", obj=self._ds)

    def _load_pre_tasks(self, attr, ds):
        '''
        Loads a list of blocks from a list which may be mixed tasks/blocks.
        Bare tasks outside of a block are given an implicit block.
        '''
        try:
            return load_list_of_blocks(ds=ds, play=self, variable_manager=self._variable_manager, loader=self._loader)
        except AssertionError:
            raise AnsibleParserError("A malformed block was encountered.", obj=self._ds)

    def _load_post_tasks(self, attr, ds):
        '''
        Loads a list of blocks from a list which may be mixed tasks/blocks.
        Bare tasks outside of a block are given an implicit block.
        '''
        try:
            return load_list_of_blocks(ds=ds, play=self, variable_manager=self._variable_manager, loader=self._loader)
        except AssertionError:
            raise AnsibleParserError("A malformed block was encountered.", obj=self._ds)

    def _load_handlers(self, attr, ds):
        '''
        Loads a list of blocks from a list which may be mixed handlers/blocks.
        Bare handlers outside of a block are given an implicit block.
        '''
        try:
            return load_list_of_blocks(ds=ds, play=self, use_handlers=True, variable_manager=self._variable_manager, loader=self._loader)
        except AssertionError:
            raise AnsibleParserError("A malformed block was encountered.", obj=self._ds)

    def _load_roles(self, attr, ds):
        '''
        Loads and returns a list of RoleInclude objects from the datastructure
        list of role definitions and creates the Role from those objects
        '''

        if ds is None:
            ds = []

        try:
            role_includes = load_list_of_roles(ds, play=self, variable_manager=self._variable_manager, loader=self._loader)
        except AssertionError:
            raise AnsibleParserError("A malformed role declaration was encountered.", obj=self._ds)

        roles = []
        for ri in role_includes:
            roles.append(Role.load(ri, play=self))
        return roles

    def _load_vars_prompt(self, attr, ds):
        new_ds = preprocess_vars(ds)
        vars_prompts = []
        for prompt_data in new_ds:
            if 'name' not in prompt_data:
                display.deprecated("Using the 'short form' for vars_prompt has been deprecated")
                for vname, prompt in prompt_data.iteritems():
                    vars_prompts.append(dict(
                        name      = vname,
                        prompt    = prompt,
                        default   = None,
                        private   = None,
                        confirm   = None,
                        encrypt   = None,
                        salt_size = None,
                        salt      = None,
                    ))
            else:
                vars_prompts.append(prompt_data)
        return vars_prompts

    def _compile_roles(self):
        '''
        Handles the role compilation step, returning a flat list of tasks
        with the lowest level dependencies first. For example, if a role R
        has a dependency D1, which also has a dependency D2, the tasks from
        D2 are merged first, followed by D1, and lastly by the tasks from
        the parent role R last. This is done for all roles in the Play.
        '''

        block_list = []

        if len(self.roles) > 0:
            for r in self.roles:
                block_list.extend(r.compile(play=self))

        return block_list

    def compile_roles_handlers(self):
        '''
        Handles the role handler compilation step, returning a flat list of Handlers
        This is done for all roles in the Play.
        '''

        block_list = []

        if len(self.roles) > 0:
            for r in self.roles:
                block_list.extend(r.get_handler_blocks())

        return block_list

    def compile(self):
        '''
        Compiles and returns the task list for this play, compiled from the
        roles (which are themselves compiled recursively) and/or the list of
        tasks specified in the play.
        '''

        # create a block containing a single flush handlers meta
        # task, so we can be sure to run handlers at certain points
        # of the playbook execution
        flush_block = Block.load(
            data={'meta': 'flush_handlers'},
            play=self,
            variable_manager=self._variable_manager,
            loader=self._loader
        )

        block_list = []

        block_list.extend(self.pre_tasks)
        block_list.append(flush_block)
        block_list.extend(self._compile_roles())
        block_list.extend(self.tasks)
        block_list.append(flush_block)
        block_list.extend(self.post_tasks)
        block_list.append(flush_block)

        return block_list

    def get_vars(self):
        return self.vars.copy()

    def get_vars_files(self):
        return self.vars_files

    def get_handlers(self):
        return self.handlers[:]

    def get_roles(self):
        return self.roles[:]

    def get_tasks(self):
        tasklist = []
        for task in self.pre_tasks + self.tasks + self.post_tasks:
            if isinstance(task, Block):
                tasklist.append(task.block + task.rescue + task.always)
            else:
                tasklist.append(task)
        return tasklist

    def serialize(self):
        data = super(Play, self).serialize()

        roles = []
        for role in self.get_roles():
            roles.append(role.serialize())
        data['roles'] = roles
        data['included_path'] = self._included_path

        return data

    def deserialize(self, data):
        super(Play, self).deserialize(data)

        self._included_path = data.get('included_path', None)
        if 'roles' in data:
            role_data = data.get('roles', [])
            roles = []
            for role in role_data:
                r = Role()
                r.deserialize(role)
                roles.append(r)

            setattr(self, 'roles', roles)
            del data['roles']

    def copy(self):
        new_me = super(Play, self).copy()
        new_me.ROLE_CACHE = self.ROLE_CACHE.copy()
        new_me._included_path = self._included_path
        return new_me
