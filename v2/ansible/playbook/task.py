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
    _transport            = FieldAttribute(isa='string')
    _until                = FieldAttribute(isa='list') # ?

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
    def load(data, block=None, role=None):
        t = Task(block=block, role=role)
        return t.load_data(data)

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
            if k in ('action', 'local_action', 'args', 'delegate_to') or k == action:
                # we don't want to re-assign these values, which were
                # determined by the ModuleArgsParser() above
                continue
            elif "with_%s" % k in lookup_finder:
                self._munge_loop(ds, new_ds, k, v)
            else:
                new_ds[k] = v

        return new_ds


    # ==================================================================================
    # BELOW THIS LINE
    # info below this line is "old" and is before the attempt to build Attributes
    # use as reference but plan to replace and radically simplify
    # ==================================================================================

LEGACY = """

    def _load_action(self, ds, k, v):
        ''' validate/transmogrify/assign the module and parameters if used in 'action/local_action' format '''

        results = dict()
        module_name, params = v.strip().split(' ', 1)
        if module_name not in module_finder:
            raise AnsibleError("the specified module '%s' could not be found, check your module path" % module_name)
        results['_module_name'] = module_name
        results['_parameters'] = parse_kv(params)

        if k == 'local_action':
            if 'delegate_to' in ds:
                raise AnsibleError("delegate_to cannot be specified with local_action in task: %s" % ds.get('name', v))
            results['_delegate_to'] = '127.0.0.1'
            if not 'transport' in ds and not 'connection' in ds:
                results['_transport'] = 'local'
        return results

    def _load_module(self, ds, k, v):
        ''' validate/transmogrify/assign the module and parameters if used in 'module:' format '''

        results = dict()
        if self._module_name:
            raise AnsibleError("the module name (%s) was already specified, '%s' is a duplicate" % (self._module_name, k))
        elif 'action' in ds:
            raise AnsibleError("multiple actions specified in task: '%s' and '%s'" % (k, ds.get('name', ds['action'])))
        results['_module_name'] = k
        if isinstance(v, dict) and 'args' in ds:
            raise AnsibleError("can't combine args: and a dict for %s: in task %s" % (k, ds.get('name', "%s: %s" % (k, v))))
        results['_parameters'] = self._load_parameters(v)
        return results

    def _load_loop(self, ds, k, v):
        ''' validate/transmogrify/assign the module any loop directives that have valid action plugins as names '''

        results = dict()
        if isinstance(v, basestring):
             param = v.strip()
             if (param.startswith('{{') and param.find('}}') == len(ds[x]) - 2 and param.find('|') == -1):
                 utils.warning("It is unnecessary to use '{{' in loops, leave variables in loop expressions bare.")
        plugin_name = k.replace("with_","")
        if plugin_name in utils.plugins.lookup_loader:
            results['_lookup_plugin'] = plugin_name
            results['_lookup_terms']  = v
        else:
            raise errors.AnsibleError("cannot find lookup plugin named %s for usage in with_%s" % (plugin_name, plugin_name))
        return results

    def _load_legacy_when(self, ds, k, v):
        ''' yell about old when syntax being used still '''

        utils.deprecated("The 'when_' conditional has been removed. Switch to using the regular unified 'when' statements as described on docs.ansible.com.","1.5", removed=True)
        if self._when:
            raise errors.AnsibleError("multiple when_* statements specified in task %s" % (ds.get('name', ds.get('action'))))
        when_name = k.replace("when_","")
        return dict(_when = "%s %s" % (when_name, v))

    def _load_when(self, ds, k, v):
        ''' validate/transmogrify/assign a conditional '''

        conditionals = self._when.copy()
        conditionals.push(v)
        return dict(_when=conditionals)

    def _load_changed_when(self, ds, k, v):
        ''' validate/transmogrify/assign a changed_when conditional '''

        conditionals = self._changed_when.copy()
        conditionals.push(v)
        return dict(_changed_when=conditionals)

    def _load_failed_when(self, ds, k, v):
        ''' validate/transmogrify/assign a failed_when conditional '''

        conditionals = self._failed_when.copy()
        conditionals.push(v)
        return dict(_failed_when=conditionals)

    # FIXME: move to BaseObject
    def _load_tags(self, ds, k, v):
        ''' validate/transmogrify/assign any tags '''

        new_tags = self.tags.copy()
        tags = v
        if isinstance(v, basestring):
            tags = v.split(',')
        new_tags.push(v)
        return dict(_tags=v)

    def _load_invalid_key(self, ds, k, v):
        ''' handle any key we do not recognize '''

        raise AnsibleError("%s is not a legal parameter in an Ansible task or handler" % k)

    def _load_other_valid_key(self, ds, k, v):
        ''' handle any other attribute we DO recognize '''

        results = dict()
        k = "_%s" % k
        results[k] = v
        return results

    def _loader_for_key(self, k):
        ''' based on the name of a datastructure element, find the code to handle it '''

        if k in ('action', 'local_action'):
            return self._load_action
        elif k in utils.plugins.module_finder:
            return self._load_module
        elif k.startswith('with_'):
            return self._load_loop
        elif k == 'changed_when':
            return self._load_changed_when
        elif k == 'failed_when':
            return self._load_failed_when
        elif k == 'when':
            return self._load_when
        elif k == 'tags':
            return self._load_tags
        elif k not in self.VALID_KEYS:
            return self._load_invalid_key
        else:
            return self._load_other_valid_key

    # ==================================================================================
    # PRE-VALIDATION - expected to be uncommonly used, this checks for arguments that
    # are aliases of each other.  Most everything else should be in the LOAD block
    # or the POST-VALIDATE block.

    def _pre_validate(self, ds):
       ''' rarely used function to see if the datastructure has items that mean the same thing '''

       if 'action' in ds and 'local_action' in ds:
           raise AnsibleError("the 'action' and 'local_action' attributes can not be used together")

    # =================================================================================
    # POST-VALIDATION: checks for internal inconsistency between fields
    # validation can result in an error but also corrections

    def _post_validate(self):
        ''' is the loaded datastructure sane? '''

        if not self._name:
            self._name = self._post_validate_fixed_name()

        # incompatible items
        self._validate_conflicting_su_and_sudo()
        self._validate_conflicting_first_available_file_and_loookup()

    def _post_validate_fixed_name(self):
        '' construct a name for the task if no name was specified '''

        flat_params = " ".join(["%s=%s" % (k,v) for k,v in self._parameters.iteritems()])
        return = "%s %s" % (self._module_name, flat_params)

    def _post_validate_conflicting_su_and_sudo(self):
        ''' make sure su/sudo usage doesn't conflict '''

        conflicting = (self._sudo or self._sudo_user or self._sudo_pass) and (self._su or self._su_user or self._su_pass):
        if conflicting:
            raise AnsibleError('sudo params ("sudo", "sudo_user", "sudo_pass") and su params ("su", "su_user", "su_pass") cannot be used together')

    def _post_validate_conflicting_first_available_file_and_lookup(self):
         ''' first_available_file (deprecated) predates lookup plugins, and cannot be used with those kinds of loops '''

        if self._first_available_file and self._lookup_plugin:
            raise AnsibleError("with_(plugin), and first_available_file are mutually incompatible in a single task")

"""
