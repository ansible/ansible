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

from ansible import constants as C
from ansible import context
from ansible.errors import AnsibleParserError, AnsibleAssertionError
from ansible.module_utils._text import to_native
from ansible.module_utils.common.collections import is_sequence
from ansible.module_utils.six import binary_type, string_types, text_type
from ansible.playbook.attribute import NonInheritableFieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.block import Block
from ansible.playbook.collectionsearch import CollectionSearch
from ansible.playbook.helpers import load_list_of_blocks, load_list_of_roles
from ansible.playbook.role import Role
from ansible.playbook.task import Task
from ansible.playbook.taggable import Taggable
from ansible.vars.manager import preprocess_vars
from ansible.utils.display import Display

display = Display()


__all__ = ['Play']


class Play(Base, Taggable, CollectionSearch):

    """
    A play is a language feature that represents a list of roles and/or
    task/handler blocks to execute on a given set of hosts.

    Usage:

       Play.load(datastructure) -> Play
       Play.something(...)
    """

    # =================================================================================
    hosts = NonInheritableFieldAttribute(isa='list', required=True, listof=string_types, always_post_validate=True, priority=-2)

    # Facts
    gather_facts = NonInheritableFieldAttribute(isa='bool', default=None, always_post_validate=True)

    # defaults to be deprecated, should be 'None' in future
    gather_subset = NonInheritableFieldAttribute(isa='list', default=(lambda: C.DEFAULT_GATHER_SUBSET), listof=string_types, always_post_validate=True)
    gather_timeout = NonInheritableFieldAttribute(isa='int', default=C.DEFAULT_GATHER_TIMEOUT, always_post_validate=True)
    fact_path = NonInheritableFieldAttribute(isa='string', default=C.DEFAULT_FACT_PATH)

    # Variable Attributes
    vars_files = NonInheritableFieldAttribute(isa='list', default=list, priority=99)
    vars_prompt = NonInheritableFieldAttribute(isa='list', default=list, always_post_validate=False)

    # Role Attributes
    roles = NonInheritableFieldAttribute(isa='list', default=list, priority=90)

    # Block (Task) Lists Attributes
    handlers = NonInheritableFieldAttribute(isa='list', default=list, priority=-1)
    pre_tasks = NonInheritableFieldAttribute(isa='list', default=list, priority=-1)
    post_tasks = NonInheritableFieldAttribute(isa='list', default=list, priority=-1)
    tasks = NonInheritableFieldAttribute(isa='list', default=list, priority=-1)

    # Flag/Setting Attributes
    force_handlers = NonInheritableFieldAttribute(isa='bool', default=context.cliargs_deferred_get('force_handlers'), always_post_validate=True)
    max_fail_percentage = NonInheritableFieldAttribute(isa='percent', always_post_validate=True)
    serial = NonInheritableFieldAttribute(isa='list', default=list, always_post_validate=True)
    strategy = NonInheritableFieldAttribute(isa='string', default=C.DEFAULT_STRATEGY, always_post_validate=True)
    order = NonInheritableFieldAttribute(isa='string', always_post_validate=True)

    # =================================================================================

    def __init__(self):
        super(Play, self).__init__()

        self._included_conditional = None
        self._included_path = None
        self._removed_hosts = []
        self.ROLE_CACHE = {}

        self.only_tags = set(context.CLIARGS.get('tags', [])) or frozenset(('all',))
        self.skip_tags = set(context.CLIARGS.get('skip_tags', []))

        self._action_groups = {}
        self._group_actions = {}

    def __repr__(self):
        return self.get_name()

    def _validate_hosts(self, attribute, name, value):
        # Only validate 'hosts' if a value was passed in to original data set.
        if 'hosts' in self._ds:
            if not value:
                raise AnsibleParserError("Hosts list cannot be empty. Please check your playbook")

            if is_sequence(value):
                # Make sure each item in the sequence is a valid string
                for entry in value:
                    if entry is None:
                        raise AnsibleParserError("Hosts list cannot contain values of 'None'. Please check your playbook")
                    elif not isinstance(entry, (binary_type, text_type)):
                        raise AnsibleParserError("Hosts list contains an invalid host value: '{host!s}'".format(host=entry))

            elif not isinstance(value, (binary_type, text_type)):
                raise AnsibleParserError("Hosts list must be a sequence or string. Please check your playbook.")

    def get_name(self):
        ''' return the name of the Play '''
        if self.name:
            return self.name

        if is_sequence(self.hosts):
            self.name = ','.join(self.hosts)
        else:
            self.name = self.hosts or ''

        return self.name

    @staticmethod
    def load(data, variable_manager=None, loader=None, vars=None):
        p = Play()
        if vars:
            p.vars = vars.copy()
        return p.load_data(data, variable_manager=variable_manager, loader=loader)

    def preprocess_data(self, ds):
        '''
        Adjusts play datastructure to cleanup old/legacy items
        '''

        if not isinstance(ds, dict):
            raise AnsibleAssertionError('while preprocessing data (%s), ds should be a dict but was a %s' % (ds, type(ds)))

        # The use of 'user' in the Play datastructure was deprecated to
        # line up with the same change for Tasks, due to the fact that
        # 'user' conflicted with the user module.
        if 'user' in ds:
            # this should never happen, but error out with a helpful message
            # to the user if it does...
            if 'remote_user' in ds:
                raise AnsibleParserError("both 'user' and 'remote_user' are set for this play. "
                                         "The use of 'user' is deprecated, and should be removed", obj=ds)

            ds['remote_user'] = ds['user']
            del ds['user']

        return super(Play, self).preprocess_data(ds)

    def _load_tasks(self, attr, ds):
        '''
        Loads a list of blocks from a list which may be mixed tasks/blocks.
        Bare tasks outside of a block are given an implicit block.
        '''
        try:
            return load_list_of_blocks(ds=ds, play=self, variable_manager=self._variable_manager, loader=self._loader)
        except AssertionError as e:
            raise AnsibleParserError("A malformed block was encountered while loading tasks: %s" % to_native(e), obj=self._ds, orig_exc=e)

    def _load_pre_tasks(self, attr, ds):
        '''
        Loads a list of blocks from a list which may be mixed tasks/blocks.
        Bare tasks outside of a block are given an implicit block.
        '''
        try:
            return load_list_of_blocks(ds=ds, play=self, variable_manager=self._variable_manager, loader=self._loader)
        except AssertionError as e:
            raise AnsibleParserError("A malformed block was encountered while loading pre_tasks", obj=self._ds, orig_exc=e)

    def _load_post_tasks(self, attr, ds):
        '''
        Loads a list of blocks from a list which may be mixed tasks/blocks.
        Bare tasks outside of a block are given an implicit block.
        '''
        try:
            return load_list_of_blocks(ds=ds, play=self, variable_manager=self._variable_manager, loader=self._loader)
        except AssertionError as e:
            raise AnsibleParserError("A malformed block was encountered while loading post_tasks", obj=self._ds, orig_exc=e)

    def _load_handlers(self, attr, ds):
        '''
        Loads a list of blocks from a list which may be mixed handlers/blocks.
        Bare handlers outside of a block are given an implicit block.
        '''
        try:
            return self._extend_value(
                self.handlers,
                load_list_of_blocks(ds=ds, play=self, use_handlers=True, variable_manager=self._variable_manager, loader=self._loader),
                prepend=True
            )
        except AssertionError as e:
            raise AnsibleParserError("A malformed block was encountered while loading handlers", obj=self._ds, orig_exc=e)

    def _load_roles(self, attr, ds):
        '''
        Loads and returns a list of RoleInclude objects from the datastructure
        list of role definitions and creates the Role from those objects
        '''

        if ds is None:
            ds = []

        try:
            role_includes = load_list_of_roles(ds, play=self, variable_manager=self._variable_manager,
                                               loader=self._loader, collection_search_list=self.collections)
        except AssertionError as e:
            raise AnsibleParserError("A malformed role declaration was encountered.", obj=self._ds, orig_exc=e)

        roles = []
        for ri in role_includes:
            roles.append(Role.load(ri, play=self))

        self.roles[:0] = roles

        return self.roles

    def _load_vars_prompt(self, attr, ds):
        new_ds = preprocess_vars(ds)
        vars_prompts = []
        if new_ds is not None:
            for prompt_data in new_ds:
                if 'name' not in prompt_data:
                    raise AnsibleParserError("Invalid vars_prompt data structure, missing 'name' key", obj=ds)
                for key in prompt_data:
                    if key not in ('name', 'prompt', 'default', 'private', 'confirm', 'encrypt', 'salt_size', 'salt', 'unsafe'):
                        raise AnsibleParserError("Invalid vars_prompt data structure, found unsupported key '%s'" % key, obj=ds)
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
                # Don't insert tasks from ``import/include_role``, preventing
                # duplicate execution at the wrong time
                if r.from_include:
                    continue
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
                if r.from_include:
                    continue
                block_list.extend(r.get_handler_blocks(play=self))

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

        for task in flush_block.block:
            task.implicit = True

        block_list = []
        if self.force_handlers:
            noop_task = Task()
            noop_task.action = 'meta'
            noop_task.args['_raw_params'] = 'noop'
            noop_task.implicit = True
            noop_task.set_loader(self._loader)

            b = Block(play=self)
            b.block = self.pre_tasks or [noop_task]
            b.always = [flush_block]
            block_list.append(b)

            tasks = self._compile_roles() + self.tasks
            b = Block(play=self)
            b.block = tasks or [noop_task]
            b.always = [flush_block]
            block_list.append(b)

            b = Block(play=self)
            b.block = self.post_tasks or [noop_task]
            b.always = [flush_block]
            block_list.append(b)

            return block_list

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
        if self.vars_files is None:
            return []
        elif not isinstance(self.vars_files, list):
            return [self.vars_files]
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
        data['action_groups'] = self._action_groups
        data['group_actions'] = self._group_actions

        return data

    def deserialize(self, data):
        super(Play, self).deserialize(data)

        self._included_path = data.get('included_path', None)
        self._action_groups = data.get('action_groups', {})
        self._group_actions = data.get('group_actions', {})
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
        new_me._included_conditional = self._included_conditional
        new_me._included_path = self._included_path
        new_me._action_groups = self._action_groups
        new_me._group_actions = self._group_actions
        return new_me
