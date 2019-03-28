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
from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.become import Become
from ansible.playbook.conditional import Conditional
from ansible.playbook.collectionsearch import CollectionSearch
from ansible.playbook.helpers import load_list_of_tasks
from ansible.playbook.role import Role
from ansible.playbook.taggable import Taggable
from ansible.utils.sentinel import Sentinel


class Block(Base, Become, Conditional, CollectionSearch, Taggable):

    # main block fields containing the task lists
    _block = FieldAttribute(isa='list', default=list, inherit=False)
    _rescue = FieldAttribute(isa='list', default=list, inherit=False)
    _always = FieldAttribute(isa='list', default=list, inherit=False)

    # other fields
    _delegate_to = FieldAttribute(isa='string')
    _delegate_facts = FieldAttribute(isa='bool')

    # for future consideration? this would be functionally
    # similar to the 'else' clause for exceptions
    # _otherwise = FieldAttribute(isa='list')

    def __init__(self, play=None, parent_block=None, role=None, task_include=None, use_handlers=False, implicit=False):
        self._play = play
        self._role = role
        self._parent = None
        self._dep_chain = None
        self._use_handlers = use_handlers
        self._implicit = implicit

        # end of role flag
        self._eor = False

        if task_include:
            self._parent = task_include
        elif parent_block:
            self._parent = parent_block

        super(Block, self).__init__()

    def __repr__(self):
        return "BLOCK(uuid=%s)(id=%s)(parent=%s)" % (self._uuid, id(self), self._parent)

    def __eq__(self, other):
        '''object comparison based on _uuid'''
        return self._uuid == other._uuid

    def __ne__(self, other):
        '''object comparison based on _uuid'''
        return self._uuid != other._uuid

    def get_vars(self):
        '''
        Blocks do not store variables directly, however they may be a member
        of a role or task include which does, so return those if present.
        '''

        all_vars = self.vars.copy()

        if self._parent:
            all_vars.update(self._parent.get_vars())

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
                task_include=None,
                variable_manager=self._variable_manager,
                loader=self._loader,
                use_handlers=self._use_handlers,
            )
        except AssertionError as e:
            raise AnsibleParserError("A malformed block was encountered while loading a block", obj=self._ds, orig_exc=e)

    def _load_rescue(self, attr, ds):
        try:
            return load_list_of_tasks(
                ds,
                play=self._play,
                block=self,
                role=self._role,
                task_include=None,
                variable_manager=self._variable_manager,
                loader=self._loader,
                use_handlers=self._use_handlers,
            )
        except AssertionError as e:
            raise AnsibleParserError("A malformed block was encountered while loading rescue.", obj=self._ds, orig_exc=e)

    def _load_always(self, attr, ds):
        try:
            return load_list_of_tasks(
                ds,
                play=self._play,
                block=self,
                role=self._role,
                task_include=None,
                variable_manager=self._variable_manager,
                loader=self._loader,
                use_handlers=self._use_handlers,
            )
        except AssertionError as e:
            raise AnsibleParserError("A malformed block was encountered while loading always", obj=self._ds, orig_exc=e)

    def _validate_always(self, attr, name, value):
        if value and not self.block:
            raise AnsibleParserError("'%s' keyword cannot be used without 'block'" % name, obj=self._ds)

    _validate_rescue = _validate_always

    def get_dep_chain(self):
        if self._dep_chain is None:
            if self._parent:
                return self._parent.get_dep_chain()
            else:
                return None
        else:
            return self._dep_chain[:]

    def copy(self, exclude_parent=False, exclude_tasks=False):
        def _dupe_task_list(task_list, new_block):
            new_task_list = []
            for task in task_list:
                new_task = task.copy(exclude_parent=True)
                if task._parent:
                    new_task._parent = task._parent.copy(exclude_tasks=True)
                    if task._parent == new_block:
                        # If task._parent is the same as new_block, just replace it
                        new_task._parent = new_block
                    else:
                        # task may not be a direct child of new_block, search for the correct place to insert new_block
                        cur_obj = new_task._parent
                        while cur_obj._parent and cur_obj._parent != new_block:
                            cur_obj = cur_obj._parent

                        cur_obj._parent = new_block
                else:
                    new_task._parent = new_block
                new_task_list.append(new_task)
            return new_task_list

        new_me = super(Block, self).copy()
        new_me._play = self._play
        new_me._use_handlers = self._use_handlers
        new_me._eor = self._eor

        if self._dep_chain is not None:
            new_me._dep_chain = self._dep_chain[:]

        new_me._parent = None
        if self._parent and not exclude_parent:
            new_me._parent = self._parent.copy(exclude_tasks=True)

        if not exclude_tasks:
            new_me.block = _dupe_task_list(self.block or [], new_me)
            new_me.rescue = _dupe_task_list(self.rescue or [], new_me)
            new_me.always = _dupe_task_list(self.always or [], new_me)

        new_me._role = None
        if self._role:
            new_me._role = self._role

        new_me.validate()
        return new_me

    def serialize(self):
        '''
        Override of the default serialize method, since when we're serializing
        a task we don't want to include the attribute list of tasks.
        '''

        data = dict()
        for attr in self._valid_attrs:
            if attr not in ('block', 'rescue', 'always'):
                data[attr] = getattr(self, attr)

        data['dep_chain'] = self.get_dep_chain()
        data['eor'] = self._eor

        if self._role is not None:
            data['role'] = self._role.serialize()
        if self._parent is not None:
            data['parent'] = self._parent.copy(exclude_tasks=True).serialize()
            data['parent_type'] = self._parent.__class__.__name__

        return data

    def deserialize(self, data):
        '''
        Override of the default deserialize method, to match the above overridden
        serialize method
        '''

        # import is here to avoid import loops
        from ansible.playbook.task_include import TaskInclude
        from ansible.playbook.handler_task_include import HandlerTaskInclude

        # we don't want the full set of attributes (the task lists), as that
        # would lead to a serialize/deserialize loop
        for attr in self._valid_attrs:
            if attr in data and attr not in ('block', 'rescue', 'always'):
                setattr(self, attr, data.get(attr))

        self._dep_chain = data.get('dep_chain', None)
        self._eor = data.get('eor', False)

        # if there was a serialized role, unpack it too
        role_data = data.get('role')
        if role_data:
            r = Role()
            r.deserialize(role_data)
            self._role = r

        parent_data = data.get('parent')
        if parent_data:
            parent_type = data.get('parent_type')
            if parent_type == 'Block':
                p = Block()
            elif parent_type == 'TaskInclude':
                p = TaskInclude()
            elif parent_type == 'HandlerTaskInclude':
                p = HandlerTaskInclude()
            p.deserialize(parent_data)
            self._parent = p
            self._dep_chain = self._parent.get_dep_chain()

    def set_loader(self, loader):
        self._loader = loader
        if self._parent:
            self._parent.set_loader(loader)
        elif self._role:
            self._role.set_loader(loader)

        dep_chain = self.get_dep_chain()
        if dep_chain:
            for dep in dep_chain:
                dep.set_loader(loader)

    def _get_parent_attribute(self, attr, extend=False, prepend=False):
        '''
        Generic logic to get the attribute or parent attribute for a block value.
        '''

        extend = self._valid_attrs[attr].extend
        prepend = self._valid_attrs[attr].prepend
        try:
            value = self._attributes[attr]
            # If parent is static, we can grab attrs from the parent
            # otherwise, defer to the grandparent
            if getattr(self._parent, 'statically_loaded', True):
                _parent = self._parent
            else:
                _parent = self._parent._parent

            if _parent and (value is Sentinel or extend):
                try:
                    if getattr(_parent, 'statically_loaded', True):
                        if hasattr(_parent, '_get_parent_attribute'):
                            parent_value = _parent._get_parent_attribute(attr)
                        else:
                            parent_value = _parent._attributes.get(attr, Sentinel)
                        if extend:
                            value = self._extend_value(value, parent_value, prepend)
                        else:
                            value = parent_value
                except AttributeError:
                    pass
            if self._role and (value is Sentinel or extend):
                try:
                    parent_value = self._role._attributes.get(attr, Sentinel)
                    if extend:
                        value = self._extend_value(value, parent_value, prepend)
                    else:
                        value = parent_value

                    dep_chain = self.get_dep_chain()
                    if dep_chain and (value is Sentinel or extend):
                        dep_chain.reverse()
                        for dep in dep_chain:
                            dep_value = dep._attributes.get(attr, Sentinel)
                            if extend:
                                value = self._extend_value(value, dep_value, prepend)
                            else:
                                value = dep_value

                            if value is not Sentinel and not extend:
                                break
                except AttributeError:
                    pass
            if self._play and (value is Sentinel or extend):
                try:
                    play_value = self._play._attributes.get(attr, Sentinel)
                    if play_value is not Sentinel:
                        if extend:
                            value = self._extend_value(value, play_value, prepend)
                        else:
                            value = play_value
                except AttributeError:
                    pass
        except KeyError:
            pass

        return value

    def filter_tagged_tasks(self, all_vars):
        '''
        Creates a new block, with task lists filtered based on the tags.
        '''

        def evaluate_and_append_task(target):
            tmp_list = []
            for task in target:
                if isinstance(task, Block):
                    tmp_list.append(evaluate_block(task))
                elif (task.action == 'meta' or
                        (task.action == 'include' and task.evaluate_tags([], self._play.skip_tags, all_vars=all_vars)) or
                        task.evaluate_tags(self._play.only_tags, self._play.skip_tags, all_vars=all_vars)):
                    tmp_list.append(task)
            return tmp_list

        def evaluate_block(block):
            new_block = self.copy(exclude_tasks=True)
            new_block.block = evaluate_and_append_task(block.block)
            new_block.rescue = evaluate_and_append_task(block.rescue)
            new_block.always = evaluate_and_append_task(block.always)
            return new_block

        return evaluate_block(self)

    def has_tasks(self):
        return len(self.block) > 0 or len(self.rescue) > 0 or len(self.always) > 0

    def get_include_params(self):
        if self._parent:
            return self._parent.get_include_params()
        else:
            return dict()

    def all_parents_static(self):
        '''
        Determine if all of the parents of this block were statically loaded
        or not. Since Task/TaskInclude objects may be in the chain, they simply
        call their parents all_parents_static() method. Only Block objects in
        the chain check the statically_loaded value of the parent.
        '''
        from ansible.playbook.task_include import TaskInclude
        if self._parent:
            if isinstance(self._parent, TaskInclude) and not self._parent.statically_loaded:
                return False
            return self._parent.all_parents_static()

        return True

    def get_first_parent_include(self):
        from ansible.playbook.task_include import TaskInclude
        if self._parent:
            if isinstance(self._parent, TaskInclude):
                return self._parent
            return self._parent.get_first_parent_include()
        return None
