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

from playbook.base import Base
from playbook.conditional import Conditional
from errors import AnsibleError
from ansible import utils

# TODO: it would be fantastic (if possible) if a task new where in the YAML it was defined for describing
# it in error conditions

class Task(Base):

    """
    A task is a language feature that represents a call to a module, with given arguments and other parameters. 
    A handler is a subclass of a task.

    Usage:

       Task.load(datastructure) -> Task
       Task.something(...)
    """

    # =================================================================================
    # KEYS AND SLOTS:  defines what variables in are valid in the data structure and 
    # the object itself

    VALID_KEYS = [
        'always_run', 'any_errors_fatal', 'async', 'connection', 'delay', 'delegate_to', 'environment',
        'first_available_file', 'ignore_errors', 'include', 'local_action', 'meta', 'name', 'no_log',
        'notify', 'poll', 'register', 'remote_user', 'retries', 'run_once', 'su', 'su_pass', 'su_user',
        'sudo', 'sudo_pass', 'sudo_user', 'transport', 'until'
    ]

    __slots__ = [
        '_always_run', '_any_errors_fatal', '_async', '_connection', '_delay', '_delegate_to', '_environment',
        '_first_available_file', '_ignore_errors', '_include', '_local_action', '_meta', '_name', '_no_log',
        '_notify', '_poll', '_register', '_remote_user', '_retries', '_run_once', '_su', '_su_pass', '_su_user',
        '_sudo', '_sudo_pass', '_sudo_user', '_transport', '_until'
    ]

    # ==================================================================================

    def __init__(self, block=None, role=None):
        ''' constructors a task, without the Task.load classmethod, it will be pretty blank '''
        self._block = block
        self._role  = role
        self._reset()
        super(Task, self).__init__()

    # TODO: move to BaseObject
    def _reset(self):
        ''' clear out the object '''

        for x in __slots__:
            setattr(x, None)

    # ==================================================================================
    # BASIC ACCESSORS
       
    def get_name(self):
       ''' return the name of the task '''
       if self._role:
            return "%s : %s" % (self._role.get_name(), self._name)
        else:
            return self._name

    def __repr__(self):
        ''' returns a human readable representation of the task '''
        return "TASK: %s" % self.get_name()

    # FIXME: does a task have variables?
    def get_vars(self):
        ''' return the variables associated with the task '''
        raise exception.NotImplementedError()

    def get_role(self):
        '' return the role associated with the task '''
        return self._role

    def get_block(self):
        ''' return the block the task is in '''
        return self._block


    # ==================================================================================
    # LOAD: functions related to walking the datastructure and storing data

    def _load_parameters(data):
        ''' validate/transmogrify/assign any module parameters for this task '''
 
       if isinstance(data, dict):
            return dict(_parameters=data)
        elif isinstance(data, basestring):
            return dict(_parameters=utils.parse_kv(data))
        elif isinstance(data, None):
            return dict(_parameters='')
        else:
            raise AnsibleError("invalid arguments specified, got '%s' (type=%s')" % (data, type(data)))

    def _load_action(self, ds, k, v):
        ''' validate/transmogrify/assign the module and parameters if used in 'action/local_action' format '''

        results = dict()
        module_name, params = v.strip().split(' ', 1)
        if module_name not in utils.plugins.module_finder:
            raise AnsibleError("the specified module '%s' could not be found, check your module path" % module_name)
        results['_module_name'] = module_name
        results['_parameters'] = utils.parse_kv(params)

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
 
    @classmethod
    def load(self, ds, block=None, role=None):
        ''' walk the datastructure and store/validate parameters '''

        self = Task(block=block, role=role)
        return self._load_from_datastructure(ds)

    # TODO: move to BaseObject
    def _load_from_datastructure(ds)
        
        self._pre_validate(ds)

        # load the keys from the datastructure
        for k,v in ds.iteritems():
            mods = self._loader_for_key(k)(k,v)
            if (k,v) in mods.iteritems():
                setattr(self,k,v)

        self._post_validate()
        return self 
 
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

