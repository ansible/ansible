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

from __future__ import annotations

import itertools
import typing as t

from ansible.errors import AnsibleParserError
from ansible.module_utils.common.sentinel import Sentinel
from ansible.playbook.attribute import NonInheritableFieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.conditional import Conditional
from ansible.playbook.collectionsearch import CollectionSearch
from ansible.playbook.delegatable import Delegatable
from ansible.playbook.helpers import load_list_of_tasks
from ansible.playbook.notifiable import Notifiable
from ansible.playbook.taggable import Taggable

if t.TYPE_CHECKING:
    from ansible.playbook.task import Task


class Block(Base, Conditional, CollectionSearch, Taggable, Notifiable, Delegatable):

    # main block fields containing the task lists
    block = NonInheritableFieldAttribute(isa='list', default=list)
    rescue = NonInheritableFieldAttribute(isa='list', default=list)
    always = NonInheritableFieldAttribute(isa='list', default=list)

    # for future consideration? this would be functionally
    # similar to the 'else' clause for exceptions
    # otherwise = FieldAttribute(isa='list')

    def __init__(self, play=None, parent_block=None, role=None, task_include=None, use_handlers=False):
        self._play = play
        self._role = role
        self._parent = None
        self._dep_chain = None
        self._use_handlers = use_handlers

        if task_include:
            self._parent = task_include
        elif parent_block:
            self._parent = parent_block

        super(Block, self).__init__()

    def __repr__(self):
        return "BLOCK(uuid=%s)(id=%s)(parent=%s)" % (self._uuid, id(self), self._parent)

    def __eq__(self, other):
        """object comparison based on _uuid"""
        return self._uuid == other._uuid

    def __ne__(self, other):
        """object comparison based on _uuid"""
        return self._uuid != other._uuid

    def get_vars(self):
        """
        Blocks do not store variables directly, however they may be a member
        of a role or task include which does, so return those if present.
        """

        all_vars = {}

        if self._parent:
            all_vars |= self._parent.get_vars()

        all_vars |= self.vars.copy()

        return all_vars

    @staticmethod
    def load(data, play=None, parent_block=None, role=None, task_include=None, use_handlers=False, variable_manager=None, loader=None):
        b = Block(play=play, parent_block=parent_block, role=role, task_include=task_include, use_handlers=use_handlers)
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
        """
        If a simple task is given, an implicit block for that single task
        is created, which goes in the main portion of the block
        """

        if not Block.is_block(ds):
            if isinstance(ds, list):
                return super(Block, self).preprocess_data(dict(block=ds))
            else:
                return super(Block, self).preprocess_data(dict(block=[ds]))

        return super(Block, self).preprocess_data(ds)

    def _load(self, attr: str, ds: object) -> list:
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
        except AssertionError as ex:
            raise AnsibleParserError(f"A malformed block was encountered while loading {attr}.", obj=self._ds) from ex

    def _load_block(self, attr, ds):
        return self._load(attr, ds)

    def _load_rescue(self, attr, ds):
        return self._load(attr, ds)

    def _load_always(self, attr, ds):
        return self._load(attr, ds)

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

    def _copy_tasks(self, tasks: list[Block | Task]) -> list[Block | Task]:
        new_tasks = []
        for task in tasks:
            new_task = task.copy()
            if task._parent._uuid == self._uuid:
                new_task._parent = self
            else:
                if new_task._parent.statically_loaded:
                    new_task._parent = new_task._parent.copy()
                # parent is include/import, skip one level
                new_task._parent._parent = self
            new_tasks.append(new_task)
        return new_tasks

    def copy(self) -> t.Self:
        """Copy this block and return the new copy.

        The blocks and tasks within are recursively copied and re-parented.
        The new copy still points to its original parent. It is the responsibility
        of the caller to change the ``_parent`` attribute if needed.
        """
        new_me = super().copy()

        if self._dep_chain is not None:
            new_me._dep_chain = self._dep_chain[:]

        new_me.block = new_me._copy_tasks(self.block)
        new_me.rescue = new_me._copy_tasks(self.rescue)
        new_me.always = new_me._copy_tasks(self.always)

        return new_me

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

    def _get_parent_attribute(self, attr, omit=False):
        """
        Generic logic to get the attribute or parent attribute for a block value.
        """
        fattr = self.fattributes[attr]

        extend = fattr.extend
        prepend = fattr.prepend

        try:
            # omit self, and only get parent values
            if omit:
                value = Sentinel
            else:
                value = getattr(self, f'_{attr}', Sentinel)

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
                            parent_value = getattr(_parent, f'_{attr}', Sentinel)
                        if extend:
                            value = self._extend_value(value, parent_value, prepend)
                        else:
                            value = parent_value
                except AttributeError:
                    pass
            if self._role and (value is Sentinel or extend):
                try:
                    parent_value = getattr(self._role, f'_{attr}', Sentinel)
                    if extend:
                        value = self._extend_value(value, parent_value, prepend)
                    else:
                        value = parent_value

                    dep_chain = self.get_dep_chain()
                    if dep_chain and (value is Sentinel or extend):
                        dep_chain.reverse()
                        for dep in dep_chain:
                            dep_value = getattr(dep, f'_{attr}', Sentinel)
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
                    play_value = getattr(self._play, f'_{attr}', Sentinel)
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
        """
        Mutates the block, with task lists filtered based on the tags.
        """
        def evaluate_and_append_task(target):
            tmp_list = []
            for task in target:
                if isinstance(task, Block):
                    task.filter_tagged_tasks(all_vars)
                    if task.has_tasks():
                        tmp_list.append(task)
                elif task.evaluate_tags(self._play.only_tags, self._play.skip_tags, all_vars=all_vars):
                    tmp_list.append(task)
            return tmp_list

        self.block = evaluate_and_append_task(self.block)
        self.rescue = evaluate_and_append_task(self.rescue)
        self.always = evaluate_and_append_task(self.always)

    def get_tasks(self):
        task_list = []
        for task in itertools.chain(self.block, self.rescue, self.always):
            if isinstance(task, Block):
                task_list.extend(task.get_tasks())
            else:
                task_list.append(task)
        return task_list

    def has_tasks(self):
        return len(self.block) > 0 or len(self.rescue) > 0 or len(self.always) > 0

    def get_include_params(self):
        if self._parent:
            return self._parent.get_include_params()
        else:
            return dict()

    def all_parents_static(self):
        """
        Determine if all of the parents of this block were statically loaded
        or not. Since Task/TaskInclude objects may be in the chain, they simply
        call their parents all_parents_static() method. Only Block objects in
        the chain check the statically_loaded value of the parent.
        """
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
