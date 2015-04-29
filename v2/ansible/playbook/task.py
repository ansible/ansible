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

from ansible.errors import AnsibleError

from ansible.parsing.mod_args import ModuleArgsParser
from ansible.parsing.splitter import parse_kv
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject, AnsibleMapping

from ansible.plugins import module_loader, lookup_loader

from ansible.playbook.attribute import Attribute, FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.become import Become
from ansible.playbook.block import Block
from ansible.playbook.conditional import Conditional
from ansible.playbook.role import Role
from ansible.playbook.taggable import Taggable

__all__ = ['Task']

class Task(Base, Conditional, Taggable, Become):

    """
    A task is a language feature that represents a call to a module, with given arguments and other parameters.
    A handler is a subclass of a task.

    Usage:

       Task.load(datastructure) -> Task
       Task.something(...)
    """

    # =================================================================================
    # ATTRIBUTES
    # load_<attribute_name> and
    # validate_<attribute_name>
    # will be used if defined
    # might be possible to define others

    _args                 = FieldAttribute(isa='dict', default=dict())
    _action               = FieldAttribute(isa='string')

    _always_run           = FieldAttribute(isa='bool')
    _any_errors_fatal     = FieldAttribute(isa='bool')
    _async                = FieldAttribute(isa='int', default=0)
    _changed_when         = FieldAttribute(isa='string')
    _delay                = FieldAttribute(isa='int', default=5)
    _delegate_to          = FieldAttribute(isa='string')
    _failed_when          = FieldAttribute(isa='string')
    _first_available_file = FieldAttribute(isa='list')
    _ignore_errors        = FieldAttribute(isa='bool')

    _loop                 = FieldAttribute(isa='string', private=True)
    _loop_args            = FieldAttribute(isa='list', private=True)
    _local_action         = FieldAttribute(isa='string')

    # FIXME: this should not be a Task
    _meta                 = FieldAttribute(isa='string')

    _name                 = FieldAttribute(isa='string', default='')

    _notify               = FieldAttribute(isa='list')
    _poll                 = FieldAttribute(isa='int')
    _register             = FieldAttribute(isa='string')
    _retries              = FieldAttribute(isa='int', default=1)
    _run_once             = FieldAttribute(isa='bool')
    _until                = FieldAttribute(isa='list') # ?

    def __init__(self, block=None, role=None, task_include=None):
        ''' constructors a task, without the Task.load classmethod, it will be pretty blank '''

        self._block        = block
        self._role         = role
        self._task_include = task_include

        super(Task, self).__init__()

    def get_name(self):
       ''' return the name of the task '''

       if self._role and self.name:
           return "%s : %s" % (self._role.get_name(), self.name)
       elif self.name:
           return self.name
       else:
           flattened_args = self._merge_kv(self.args)
           if self._role:
               return "%s : %s %s" % (self._role.get_name(), self.action, flattened_args)
           else:
               return "%s %s" % (self.action, flattened_args)

    def _merge_kv(self, ds):
        if ds is None:
            return ""
        elif isinstance(ds, basestring):
            return ds
        elif isinstance(ds, dict):
            buf = ""
            for (k,v) in ds.iteritems():
                if k.startswith('_'):
                    continue
                buf = buf + "%s=%s " % (k,v)
            buf = buf.strip()
            return buf

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):
        t = Task(block=block, role=role, task_include=task_include)
        return t.load_data(data, variable_manager=variable_manager, loader=loader)

    def __repr__(self):
        ''' returns a human readable representation of the task '''
        return "TASK: %s" % self.get_name()

    def _preprocess_loop(self, ds, new_ds, k, v):
        ''' take a lookup plugin name and store it correctly '''

        loop_name = k.replace("with_", "")
        if new_ds.get('loop') is not None:
            raise AnsibleError("duplicate loop in task: %s" % loop_name)
        new_ds['loop'] = loop_name
        new_ds['loop_args'] = v

    def preprocess_data(self, ds):
        '''
        tasks are especially complex arguments so need pre-processing.
        keep it short.
        '''

        assert isinstance(ds, dict)

        # the new, cleaned datastructure, which will have legacy
        # items reduced to a standard structure suitable for the
        # attributes of the task class
        new_ds = AnsibleMapping()
        if isinstance(ds, AnsibleBaseYAMLObject):
            new_ds.ansible_pos = ds.ansible_pos

        # use the args parsing class to determine the action, args,
        # and the delegate_to value from the various possible forms
        # supported as legacy
        args_parser = ModuleArgsParser(task_ds=ds)
        (action, args, delegate_to) = args_parser.parse()

        new_ds['action']      = action
        new_ds['args']        = args
        new_ds['delegate_to'] = delegate_to

        for (k,v) in ds.iteritems():
            if k in ('action', 'local_action', 'args', 'delegate_to') or k == action or k == 'shell':
                # we don't want to re-assign these values, which were
                # determined by the ModuleArgsParser() above
                continue
            elif k.replace("with_", "") in lookup_loader:
                self._preprocess_loop(ds, new_ds, k, v)
            else:
                new_ds[k] = v

        return super(Task, self).preprocess_data(new_ds)

    def post_validate(self, all_vars=dict(), fail_on_undefined=True):
        '''
        Override of base class post_validate, to also do final validation on
        the block and task include (if any) to which this task belongs.
        '''

        if self._block:
            self._block.post_validate(all_vars=all_vars, fail_on_undefined=fail_on_undefined)
        if self._task_include:
            self._task_include.post_validate(all_vars=all_vars, fail_on_undefined=fail_on_undefined)

        super(Task, self).post_validate(all_vars=all_vars, fail_on_undefined=fail_on_undefined)

    def get_vars(self):
        all_vars = self.vars.copy()
        if self._block:
            all_vars.update(self._block.get_vars())
        if self._task_include:
            all_vars.update(self._task_include.get_vars())

        all_vars.update(self.serialize())

        if 'tags' in all_vars:
            del all_vars['tags']
        if 'when' in all_vars:
            del all_vars['when']
        return all_vars

    # no longer used, as blocks are the lowest level of compilation now
    #def compile(self):
    #    '''
    #    For tasks, this is just a dummy method returning an array
    #    with 'self' in it, so we don't have to care about task types
    #    further up the chain.
    #    '''
    #
    #    return [self]

    def copy(self, exclude_block=False):
        new_me = super(Task, self).copy()

        new_me._block = None
        if self._block and not exclude_block:
            new_me._block = self._block.copy()

        new_me._role = None
        if self._role:
            new_me._role = self._role

        new_me._task_include = None
        if self._task_include:
            new_me._task_include = self._task_include.copy()

        return new_me

    def serialize(self):
        data = super(Task, self).serialize()

        if self._block:
            data['block'] = self._block.serialize()

        if self._role:
            data['role'] = self._role.serialize()

        if self._task_include:
            data['task_include'] = self._task_include.serialize()

        return data

    def deserialize(self, data):

        # import is here to avoid import loops
        #from ansible.playbook.task_include import TaskInclude

        block_data = data.get('block')

        if block_data:
            b = Block()
            b.deserialize(block_data)
            self._block = b
            del data['block']

        role_data = data.get('role')
        if role_data:
            r = Role()
            r.deserialize(role_data)
            self._role = r
            del data['role']

        ti_data = data.get('task_include')
        if ti_data:
            #ti = TaskInclude()
            ti = Task()
            ti.deserialize(ti_data)
            self._task_include = ti
            del data['task_include']

        super(Task, self).deserialize(data)

    def evaluate_conditional(self, all_vars):
        if self._block is not None:
            if not self._block.evaluate_conditional(all_vars):
                return False
        if self._task_include is not None:
            if not self._task_include.evaluate_conditional(all_vars):
                return False
        return super(Task, self).evaluate_conditional(all_vars)

    def set_loader(self, loader):
        '''
        Sets the loader on this object and recursively on parent, child objects.
        This is used primarily after the Task has been serialized/deserialized, which
        does not preserve the loader.
        '''

        self._loader = loader

        if self._block:
            self._block.set_loader(loader)
        if self._task_include:
            self._task_include.set_loader(loader)

    def _get_parent_attribute(self, attr):
        '''
        Generic logic to get the attribute or parent attribute for a task value.
        '''
        value = self._attributes[attr]
        if not value and self._block:
            value = getattr(self._block, attr)
        return value

