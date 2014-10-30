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

from ansible.playbook.base import Base
from ansible.playbook.attribute import Attribute, FieldAttribute

from ansible.errors import AnsibleError

from ansible.parsing.splitter import parse_kv
from ansible.parsing.mod_args import ModuleArgsParser
from ansible.parsing.yaml import DataLoader
from ansible.plugins import module_finder, lookup_finder

class Task(Base):

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

    _args                 = FieldAttribute(isa='dict')
    _action               = FieldAttribute(isa='string')

    _always_run           = FieldAttribute(isa='bool')
    _any_errors_fatal     = FieldAttribute(isa='bool')
    _async                = FieldAttribute(isa='int')
    _connection           = FieldAttribute(isa='string')
    _delay                = FieldAttribute(isa='int')
    _delegate_to          = FieldAttribute(isa='string')
    _environment          = FieldAttribute(isa='dict')
    _first_available_file = FieldAttribute(isa='list')
    _ignore_errors        = FieldAttribute(isa='bool')

    _loop                 = FieldAttribute(isa='string', private=True)
    _loop_args            = FieldAttribute(isa='list', private=True)
    _local_action         = FieldAttribute(isa='string')

    # FIXME: this should not be a Task
    _meta                 = FieldAttribute(isa='string')

    _name                 = FieldAttribute(isa='string')

    _no_log               = FieldAttribute(isa='bool')
    _notify               = FieldAttribute(isa='list')
    _poll                 = FieldAttribute(isa='integer')
    _register             = FieldAttribute(isa='string')
    _remote_user          = FieldAttribute(isa='string')
    _retries              = FieldAttribute(isa='integer')
    _run_once             = FieldAttribute(isa='bool')
    _su                   = FieldAttribute(isa='bool')
    _su_pass              = FieldAttribute(isa='string')
    _su_user              = FieldAttribute(isa='string')
    _sudo                 = FieldAttribute(isa='bool')
    _sudo_user            = FieldAttribute(isa='string')
    _sudo_pass            = FieldAttribute(isa='string')
    _tags                 = FieldAttribute(isa='list', default=[])
    _transport            = FieldAttribute(isa='string')
    _until                = FieldAttribute(isa='list') # ?
    _when                 = FieldAttribute(isa='list', default=[])

    def __init__(self, block=None, role=None):
        ''' constructors a task, without the Task.load classmethod, it will be pretty blank '''
        self._block = block
        self._role  = role
        super(Task, self).__init__()

    def get_name(self):
       ''' return the name of the task '''

       if self._role and self.name:
           return "%s : %s" % (self._role.name, self.name)
       elif self.name:
           return self.name
       else:
           flattened_args = self._merge_kv(self.args)
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
    def load(data, block=None, role=None, loader=None):
        t = Task(block=block, role=role)
        return t.load_data(data, loader=loader)

    def __repr__(self):
        ''' returns a human readable representation of the task '''
        return "TASK: %s" % self.get_name()

    def _munge_loop(self, ds, new_ds, k, v):
        ''' take a lookup plugin name and store it correctly '''

        if self._loop.value is not None:
            raise AnsibleError("duplicate loop in task: %s" % k)
        new_ds['loop'] = k
        new_ds['loop_args'] = v

    def munge(self, ds):
        '''
        tasks are especially complex arguments so need pre-processing.
        keep it short.
        '''

        assert isinstance(ds, dict)

        # the new, cleaned datastructure, which will have legacy
        # items reduced to a standard structure suitable for the
        # attributes of the task class
        new_ds = dict()

        # use the args parsing class to determine the action, args,
        # and the delegate_to value from the various possible forms
        # supported as legacy
        args_parser = ModuleArgsParser()
        (action, args, delegate_to) = args_parser.parse(ds)

        new_ds['action']      = action
        new_ds['args']        = args
        new_ds['delegate_to'] = delegate_to

        for (k,v) in ds.iteritems():
            if k in ('action', 'local_action', 'args', 'delegate_to') or k == action or k == 'shell':
                # we don't want to re-assign these values, which were
                # determined by the ModuleArgsParser() above
                continue
            elif "with_%s" % k in lookup_finder:
                self._munge_loop(ds, new_ds, k, v)
            else:
                new_ds[k] = v

        return new_ds

