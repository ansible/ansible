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

from ansible.errors import AnsibleParserError
from ansible.playbook.attribute import Attribute, FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.become import Become
from ansible.playbook.conditional import Conditional
from ansible.playbook.helpers import load_list_of_tasks
from ansible.playbook.role import Role
from ansible.playbook.taggable import Taggable

class Block(Base, Become, Conditional, Taggable):

    _block  = FieldAttribute(isa='list', default=[])
    _rescue = FieldAttribute(isa='list', default=[])
    _always = FieldAttribute(isa='list', default=[])
    _delegate_to = FieldAttribute(isa='list')
    _delegate_facts = FieldAttribute(isa='bool', default=False)
    _any_errors_fatal = FieldAttribute(isa='bool')

    # for future consideration? this would be functionally
    # similar to the 'else' clause for exceptions
    #_otherwise = FieldAttribute(isa='list')

    def __init__(self, play=None, parent_block=None, role=None, task_include=None, use_handlers=False, implicit=False):
        self._play         = play
        self._role         = role
        self._task_include = None
        self._parent_block = None
        self._dep_chain    = None
        self._use_handlers = use_handlers
        self._implicit     = implicit

        if task_include:
            self._task_include = task_include
        elif parent_block:
            self._parent_block = parent_block

        super(Block, self).__init__()

    def get_vars(self):
        '''
        Blocks do not store variables directly, however they may be a member
        of a role or task include which does, so return those if present.
        '''

        all_vars = self.vars.copy()

        if self._role:
            all_vars.update(self._role.get_vars(self._dep_chain))
        if self._parent_block:
            all_vars.update(self._parent_block.get_vars())
        if self._task_include:
            all_vars.update(self._task_include.get_vars())

        return all_vars

    @staticmethod
    def load(data, play=None, parent_block=None, role=None, task_include=None, use_handlers=False, variable_manager=None, loader=None):
        implicit = not Block.is_block(data)
        b = Block(play=play, parent_block=parent_block, role=role, task_include=task_include, use_handlers=use_handlers, implicit=implicit)
        return b.load_data(data, variable_manager=variable_manager, loader=loader)

    @staticmethod
    def is_block(ds):
        is_block = False
        if isinstance(ds, dict):
            for attr in ('block', 'rescue', 'always'):
                if attr in ds:
                    is_block = True
                    break
        return is_block

    def preprocess_data(self, ds):
        '''
        If a simple task is given, an implicit block for that single task
        is created, which goes in the main portion of the block
        '''

        if not Block.is_block(ds):
            if isinstance(ds, list):
                return super(Block, self).preprocess_data(dict(block=ds))
            else:
                return super(Block, self).preprocess_data(dict(block=[ds]))

        return super(Block, self).preprocess_data(ds)

    def _load_block(self, attr, ds):
        try:
            return load_list_of_tasks(
                ds,
                play=self._play,
                block=self,
                role=self._role,
                task_include=self._task_include,
                variable_manager=self._variable_manager,
                loader=self._loader,
                use_handlers=self._use_handlers,
            )
        except AssertionError:
            raise AnsibleParserError("A malformed block was encountered.", obj=self._ds)

    def _load_rescue(self, attr, ds):
        try:
            return load_list_of_tasks(
                ds,
                play=self._play,
                block=self,
                role=self._role,
                task_include=self._task_include,
                variable_manager=self._variable_manager,
                loader=self._loader,
                use_handlers=self._use_handlers,
            )
        except AssertionError:
            raise AnsibleParserError("A malformed block was encountered.", obj=self._ds)

    def _load_always(self, attr, ds):
        try:
            return load_list_of_tasks(
                ds, 
                play=self._play,
                block=self, 
                role=self._role, 
                task_include=self._task_include,
                variable_manager=self._variable_manager, 
                loader=self._loader, 
                use_handlers=self._use_handlers,
            )
        except AssertionError:
            raise AnsibleParserError("A malformed block was encountered.", obj=self._ds)

    def get_dep_chain(self):
        if self._dep_chain is None:
            if self._parent_block:
                return self._parent_block.get_dep_chain()
            elif self._task_include:
                return self._task_include._block.get_dep_chain()
            else:
                return None
        else:
            return self._dep_chain[:]

    def copy(self, exclude_parent=False, exclude_tasks=False):
        def _dupe_task_list(task_list, new_block):
            new_task_list = []
            for task in task_list:
                if isinstance(task, Block):
                    new_task = task.copy(exclude_parent=True)
                    new_task._parent_block = new_block
                else:
                    new_task = task.copy(exclude_block=True)
                    new_task._block = new_block
                new_task_list.append(new_task)
            return new_task_list

        new_me = super(Block, self).copy()
        new_me._play         = self._play
        new_me._use_handlers = self._use_handlers

        if self._dep_chain:
            new_me._dep_chain = self._dep_chain[:]

        if not exclude_tasks:
            new_me.block  = _dupe_task_list(self.block or [], new_me)
            new_me.rescue = _dupe_task_list(self.rescue or [], new_me)
            new_me.always = _dupe_task_list(self.always or [], new_me)

        new_me._parent_block = None
        if self._parent_block and not exclude_parent:
            new_me._parent_block = self._parent_block.copy(exclude_tasks=exclude_tasks)

        new_me._role = None
        if self._role:
            new_me._role = self._role

        new_me._task_include = None
        if self._task_include:
            new_me._task_include = self._task_include.copy(exclude_block=True)
            new_me._task_include._block = self._task_include._block.copy(exclude_tasks=True)

        return new_me

    def serialize(self):
        '''
        Override of the default serialize method, since when we're serializing
        a task we don't want to include the attribute list of tasks.
        '''

        data = dict()
        for attr in self._get_base_attributes():
            if attr not in ('block', 'rescue', 'always'):
                data[attr] = getattr(self, attr)

        data['dep_chain'] = self.get_dep_chain()

        if self._role is not None:
            data['role'] = self._role.serialize()
        if self._task_include is not None:
            data['task_include'] = self._task_include.serialize()
        if self._parent_block is not None:
            data['parent_block'] = self._parent_block.copy(exclude_tasks=True).serialize()

        return data

    def deserialize(self, data):
        '''
        Override of the default deserialize method, to match the above overridden
        serialize method
        '''

        from ansible.playbook.task import Task

        # we don't want the full set of attributes (the task lists), as that
        # would lead to a serialize/deserialize loop
        for attr in self._get_base_attributes():
            if attr in data and attr not in ('block', 'rescue', 'always'):
                setattr(self, attr, data.get(attr))

        self._dep_chain = data.get('dep_chain', None)

        # if there was a serialized role, unpack it too
        role_data = data.get('role')
        if role_data:
            r = Role()
            r.deserialize(role_data)
            self._role = r

        # if there was a serialized task include, unpack it too
        ti_data = data.get('task_include')
        if ti_data:
            ti = Task()
            ti.deserialize(ti_data)
            self._task_include = ti

        pb_data = data.get('parent_block')
        if pb_data:
            pb = Block()
            pb.deserialize(pb_data)
            self._parent_block = pb
            self._dep_chain = self._parent_block.get_dep_chain()

    def evaluate_conditional(self, templar, all_vars):
        dep_chain = self.get_dep_chain()
        if dep_chain:
            for dep in dep_chain:
                if not dep.evaluate_conditional(templar, all_vars):
                    return False
        if self._task_include is not None:
            if not self._task_include.evaluate_conditional(templar, all_vars):
                return False
        if self._parent_block is not None:
            if not self._parent_block.evaluate_conditional(templar, all_vars):
                return False
        elif self._role is not None:
            if not self._role.evaluate_conditional(templar, all_vars):
                return False
        return super(Block, self).evaluate_conditional(templar, all_vars)

    def set_loader(self, loader):
        self._loader = loader
        if self._parent_block:
            self._parent_block.set_loader(loader)
        elif self._role:
            self._role.set_loader(loader)

        if self._task_include:
            self._task_include.set_loader(loader)

        dep_chain = self.get_dep_chain()
        if dep_chain:
            for dep in dep_chain:
                dep.set_loader(loader)

    def _get_parent_attribute(self, attr, extend=False):
        '''
        Generic logic to get the attribute or parent attribute for a block value.
        '''

        value = None
        try:
            value = self._attributes[attr]

            if self._parent_block and (value is None or extend):
                parent_value = getattr(self._parent_block, attr)
                if extend:
                    value = self._extend_value(value, parent_value)
                else:
                    value = parent_value
            if self._task_include and (value is None or extend):
                parent_value = getattr(self._task_include, attr)
                if extend:
                    value = self._extend_value(value, parent_value)
                else:
                    value = parent_value
            if self._role and (value is None or extend) and hasattr(self._role, attr):
                parent_value = getattr(self._role, attr, None)
                if extend:
                    value = self._extend_value(value, parent_value)
                else:
                    value = parent_value

                dep_chain = self.get_dep_chain()
                if dep_chain and (value is None or extend):
                    dep_chain.reverse()
                    for dep in dep_chain:
                        dep_value = getattr(dep, attr, None)
                        if extend:
                            value = self._extend_value(value, dep_value)
                        else:
                            value = dep_value

                        if value is not None and not extend:
                            break
            if self._play and (value is None or extend) and hasattr(self._play, attr):
                parent_value = getattr(self._play, attr, None)
                if extend:
                    value = self._extend_value(value, parent_value)
                else:
                    value = parent_value
        except KeyError as e:
            pass

        return value

    def _get_attr_environment(self):
        '''
        Override for the 'tags' getattr fetcher, used from Base.
        '''
        environment = self._attributes['environment']
        parent_environment = self._get_parent_attribute('environment', extend=True)
        if parent_environment is not None:
            environment = self._extend_value(environment, parent_environment)

        return environment

    def _get_attr_any_errors_fatal(self):
        '''
        Override for the 'tags' getattr fetcher, used from Base.
        '''
        return self._get_parent_attribute('any_errors_fatal')

    def filter_tagged_tasks(self, play_context, all_vars):
        '''
        Creates a new block, with task lists filtered based on the tags contained
        within the play_context object.
        '''

        def evaluate_and_append_task(target):
            tmp_list = []
            for task in target:
                if isinstance(task, Block):
                    tmp_list.append(evaluate_block(task))
                elif task.action == 'meta' \
                or (task.action == 'include' and task.evaluate_tags([], play_context.skip_tags, all_vars=all_vars)) \
                or task.evaluate_tags(play_context.only_tags, play_context.skip_tags, all_vars=all_vars):
                    tmp_list.append(task)
            return tmp_list

        def evaluate_block(block):
            new_block = self.copy(exclude_tasks=True)
            new_block.block  = evaluate_and_append_task(block.block)
            new_block.rescue = evaluate_and_append_task(block.rescue)
            new_block.always = evaluate_and_append_task(block.always)
            return new_block

        return evaluate_block(self)

    def has_tasks(self):
        return len(self.block) > 0 or len(self.rescue) > 0 or len(self.always) > 0

