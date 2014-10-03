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

class Task(Base):

    # the list of valid keys for tasks
    VALID_KEYS = [
        'always_run',
        'any_errors_fatal',
        'async',
        'connection',
        'delay',
        'delegate_to',
        'environment',
        'first_available_file',
        'ignore_errors',
        'include',
        'local_action',
        'meta',
        'name',
        'no_log',
        'notify',
        'poll',
        'register',
        'remote_user',
        'retries',
        'run_once',
        'su',
        'su_pass',
        'su_user',
        'sudo',
        'sudo_pass',
        'sudo_user',
        'transport',
        'until',
    ]

    def __init__(self, block=None, role=None):
        self._ds    = None
        self._block = block
        self._role  = role
        self._reset()
        super(Task, self).__init__()

    def __repr__(self):
        if self._role:
            return "%s : %s" % (self._role.get_name(), self._name)
        else:
            return self._name

    def _reset(self):
        ''' clears internal data structures '''

        for k in self.VALID_KEYS:
            setattr(self, '_%s' % k, None)

        # attributes not set via the ds
        self._action        = None
        self._module_name   = None
        self._parameters    = None
        self._lookup_plugin = None
        self._lookup_terms  = None

        # special conditionals
        self._changed_when = Conditional(self)
        self._failed_when  = Conditional(self)
        self._when         = Conditional(self)

    def _load_parameters(data):
        ''' sets the parameters for this task, based on the type of the data '''
        if isinstance(data, dict):
            self._parameters = data
        elif isinstance(data, basestring):
            self._parameters = utils.parse_kv(data)
        elif isinstance(data, None):
            self._parameters = ''
        else:
            raise AnsibleError("invalid arguments specified, got '%s' (type=%s')" % (data, type(data)))

    def load(self, ds):
        ''' parses and loads the task from the given datastructure '''

        # reset everything internally
        self._reset()

        # 'action' and 'local_action' are mutually-exclusive options
        if 'action' in ds and 'local_action' in ds:
            raise AnsibleError("the 'action' and 'local_action' attributes can not be used together")

        # iterate over each key/value in the datastructure to parse out its parameters.
        args = None
        for k,v in ds.iteritems():
            if k in ('action', 'local_action'):
                # task structure is:
                # action: module_name k=v ...
                # or
                # local_action: module_name k=v ...
                module_name, params = v.strip().split(' ', 1)
                if module_name not in utils.plugins.module_finder:
                    raise AnsibleError("the specified module '%s' could not be found, check your module path" % module_name)
                self._module_name = module_name
                self._parameters = utils.parse_kv(params)
                if k == 'local_action':
                    if 'delegate_to' in ds:
                        raise AnsibleError("delegate_to cannot be specified with local_action in task: %s" % ds.get('name', v))
                    self._delegate_to = '127.0.0.1'
                    if not 'transport' in ds and not 'connection' in ds:
                        self._transport = 'local'
            elif k in utils.plugins.module_finder:
                # task structure is:
                # - module_name: k=v ...
                if self._module_name:
                    raise AnsibleError("the module name (%s) was already specified, '%s' is a duplicate" % (self._module_name, k))
                elif 'action' in ds:
                    raise AnsibleError("multiple actions specified in task: '%s' and '%s'" % (k, ds.get('name', ds['action'])))
                self._module_name = k
                if isinstance(v, dict) and 'args' in ds:
                    raise AnsibleError("can't combine args: and a dict for %s: in task %s" % (k, ds.get('name', "%s: %s" % (k, v))))
                self._parameters = self._load_parameters(v)
            elif k == 'args':
                args = self._load_parameters(v)
            elif k.startswith('with_'):
                if isinstance(v, basestring):
                    param = v.strip()
                    if (param.startswith('{{') and param.find('}}') == len(ds[x]) - 2 and param.find('|') == -1):
                        utils.warning("It is unnecessary to use '{{' in loops, leave variables in loop expressions bare.")
                plugin_name = k.replace("with_","")
                if plugin_name in utils.plugins.lookup_loader:
                    self._lookup_plugin = plugin_name
                    self._lookup_terms  = v
                else:
                    raise errors.AnsibleError("cannot find lookup plugin named %s for usage in with_%s" % (plugin_name, plugin_name))
            elif k.startswith('when_'):
                utils.deprecated("The 'when_' conditional has been removed. Switch to using the regular unified 'when' statements as described on docs.ansible.com.","1.5", removed=True)
                if self._when:
                    raise errors.AnsibleError("multiple when_* statements specified in task %s" % (ds.get('name', ds.get('action'))))
                when_name = k.replace("when_","")
                self._when = "%s %s" % (when_name, v)
            elif k in ('changed_when', 'failed_when', 'when'):
                # these are conditional objects, so we push the new conditional value
                # into the object so that it can be evaluated later
                getattr(self, '_%s' % k).push(v)
            elif k == 'tags':
                # all taggable datastructures in Ansible (tasks, roles, etc.) are
                # based on the Base() class, which includes the _tags attribute
                # (which is a Tag() class)
                tags = v
                if isinstance(v, basestring):
                    tags = v.split(',')
                self._tags.push(tags)
            elif k not in self.VALID_KEYS:
                raise AnsibleError("%s is not a legal parameter in an Ansible task or handler" % k)
            else:
                setattr(self, '_%s' % k, v)

        # if args were specified along with parameters, merge them now
        # with the args taking lower precedence
        if args:
            self._parameters = utils.combine_vars(args, self._parameters)

        # run validation
        self._validate()

        # finally, store the ds for later use/reference
        self._ds = ds

    def _validate(self):
        '''
        Validates internal datastructures and verifies mutually-exclusive
        options are not in conflict.
        '''

        if not self._name:
            # if no name: was specified, flatten the parameters back 
            # into a string and combine them with with module name
            flat_params = " ".join(["%s=%s" % (k,v) for k,v in self._parameters.iteritems()])
            self._name = "%s %s" % (self._module_name, flat_params)

        # use builtin _ensure* methods to massage/set values on attributes
        # anything not listed here will be defaulted to None by _reset()
        self._ensure_int("_async", 0)
        self._ensure_int("_poll", 10)
        self._ensure_bool("_ignore_errors", False)
        self._ensure_bool("_always_run", False)
        self._ensure_list_of_strings("_notify", [])

        # handle mutually incompatible options
        if (self._sudo or self._sudo_user or self._sudo_pass) and (self._su or self._su_user or self._su_pass):
            raise AnsibleError('sudo params ("sudo", "sudo_user", "sudo_pass") and su params ("su", "su_user", "su_pass") cannot be used together')

        incompatibles = [ x for x in [ self._first_available_file, self._lookup_plugin ] if x is not None ]
        if len(incompatibles) > 1:
            raise AnsibleError("with_(plugin), and first_available_file are mutually incompatible in a single task")

    @property
    def name(self):
        return self.__repr__()

    def get_vars(self):
        return dict()

    def get_role(self):
        return self.role

    def get_block(self):
        return self.block

