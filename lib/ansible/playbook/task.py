# (c) 2012-2013, Michael DeHaan <michael.dehaan@gmail.com>
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

from ansible import errors
from ansible import utils
import os
import ansible.utils.template as template

class Task(object):

    __slots__ = [
        'name', 'meta', 'action', 'only_if', 'when', 'async_seconds', 'async_poll_interval',
        'notify', 'module_name', 'module_args', 'module_vars',
        'play', 'notified_by', 'tags', 'register',
        'delegate_to', 'first_available_file', 'ignore_errors',
        'local_action', 'transport', 'sudo', 'sudo_user', 'sudo_pass',
        'items_lookup_plugin', 'items_lookup_terms', 'environment', 'args',
        'any_errors_fatal', 'ignore_changed', 'always_run'
    ]

    # to prevent typos and such
    VALID_KEYS = [
         'name', 'meta', 'action', 'only_if', 'async', 'poll', 'notify',
         'first_available_file', 'include', 'tags', 'register', 'ignore_errors',
         'delegate_to', 'local_action', 'transport', 'sudo', 'sudo_user',
         'sudo_pass', 'when', 'connection', 'environment', 'args',
         'any_errors_fatal', 'ignore_changed', 'always_run'
    ]

    def __init__(self, play, ds, module_vars=None, additional_conditions=None):
        ''' constructor loads from a task or handler datastructure '''

        # meta directives are used to tell things like ansible/playbook to run
        # operations like handler execution.  Meta tasks are not executed
        # normally.
        if 'meta' in ds:
            self.meta = ds['meta']
            self.tags = []
            return
        else:
            self.meta = None


        library = os.path.join(play.basedir, 'library')
        if os.path.exists(library):
            utils.plugins.module_finder.add_directory(library)

        for x in ds.keys():

            # code to allow for saying "modulename: args" versus "action: modulename args"
            if x in utils.plugins.module_finder:

                if 'action' in ds:
                    raise errors.AnsibleError("multiple actions specified in task %s" % (ds.get('name', ds['action'])))
                if isinstance(ds[x], dict):
                    if 'args' in ds:
                        raise errors.AnsibleError("can't combine args: and a dict for %s: in task %s" % (x, ds.get('name', "%s: %s" % (x, ds[x]))))
                    ds['args'] = ds[x]
                    ds[x] = ''
                elif ds[x] is None:
                    ds[x] = ''
                if not isinstance(ds[x], basestring):
                    raise errors.AnsibleError("action specified for task %s has invalid type %s" % (ds.get('name', "%s: %s" % (x, ds[x])), type(ds[x])))
                ds['action'] = x + " " + ds[x]
                ds.pop(x)

            # code to allow "with_glob" and to reference a lookup plugin named glob
            elif x.startswith("with_"):
                plugin_name = x.replace("with_","")
                if plugin_name in utils.plugins.lookup_loader:
                    ds['items_lookup_plugin'] = plugin_name
                    ds['items_lookup_terms'] = ds[x]
                    ds.pop(x)
                else:
                    raise errors.AnsibleError("cannot find lookup plugin named %s for usage in with_%s" % (plugin_name, plugin_name))

            elif x == 'when':
                ds['when'] = "jinja2_compare %s" % (ds[x])
            elif x.startswith("when_"):
                if 'when' in ds:
                    raise errors.AnsibleError("multiple when_* statements specified in task %s" % (ds.get('name', ds['action'])))
                when_name = x.replace("when_","")
                ds['when'] = "%s %s" % (when_name, ds[x])
                ds.pop(x)

            elif not x in Task.VALID_KEYS:
                raise errors.AnsibleError("%s is not a legal parameter in an Ansible task or handler" % x)

        self.module_vars = module_vars
        self.play        = play

        # load various attributes
        self.name         = ds.get('name', None)
        self.tags         = [ 'all' ]
        self.register     = ds.get('register', None)
        self.sudo         = utils.boolean(ds.get('sudo', play.sudo))
        self.environment  = ds.get('environment', {})

        # rather than simple key=value args on the options line, these represent structured data and the values
        # can be hashes and lists, not just scalars
        self.args         = ds.get('args', {})

        if self.sudo:
            self.sudo_user    = ds.get('sudo_user', play.sudo_user)
            self.sudo_pass    = ds.get('sudo_pass', play.playbook.sudo_pass)
        else:
            self.sudo_user    = None
            self.sudo_pass    = None
        
        # Both are defined
        if ('action' in ds) and ('local_action' in ds):
            raise errors.AnsibleError("the 'action' and 'local_action' attributes can not be used together")
        # Both are NOT defined
        elif (not 'action' in ds) and (not 'local_action' in ds):
            raise errors.AnsibleError("'action' or 'local_action' attribute missing in task \"%s\"" % ds.get('name', '<Unnamed>'))
        # Only one of them is defined
        elif 'local_action' in ds:
            self.action      = ds.get('local_action', '')
            self.delegate_to = '127.0.0.1'
        else:
            self.action      = ds.get('action', '')
            self.delegate_to = ds.get('delegate_to', None)
            self.transport   = ds.get('connection', ds.get('transport', play.transport))

        if isinstance(self.action, dict):
            if 'module' not in self.action:
                raise errors.AnsibleError("'module' attribute missing from action in task \"%s\"" % ds.get('name', '%s' % self.action))
            if self.args:
                raise errors.AnsibleError("'args' cannot be combined with dict 'action' in task \"%s\"" % ds.get('name', '%s' % self.action))
            self.args = self.action
            self.action = self.args.pop('module')

        # delegate_to can use variables
        if not (self.delegate_to is None):
            # delegate_to: localhost should use local transport
            if self.delegate_to in ['127.0.0.1', 'localhost']:
                self.transport   = 'local'

        # notified by is used by Playbook code to flag which hosts
        # need to run a notifier
        self.notified_by = []

        # if no name is specified, use the action line as the name
        if self.name is None:
            self.name = self.action

        # load various attributes
        self.only_if = ds.get('only_if', 'True')
        self.when    = ds.get('when', None)

        self.async_seconds = int(ds.get('async', 0))  # not async by default
        self.async_poll_interval = int(ds.get('poll', 10))  # default poll = 10 seconds
        self.notify = ds.get('notify', [])
        self.first_available_file = ds.get('first_available_file', None)

        self.items_lookup_plugin = ds.get('items_lookup_plugin', None)
        self.items_lookup_terms  = ds.get('items_lookup_terms', None)
     

        self.ignore_errors = ds.get('ignore_errors', False)
        self.any_errors_fatal = ds.get('any_errors_fatal', play.any_errors_fatal)

        self.ignore_changed = ds.get('ignore_changed', False)
        self.always_run = ds.get('always_run', False)

        # action should be a string
        if not isinstance(self.action, basestring):
            raise errors.AnsibleError("action is of type '%s' and not a string in task. name: %s" % (type(self.action).__name__, self.name))

        # notify can be a string or a list, store as a list
        if isinstance(self.notify, basestring):
            self.notify = [ self.notify ]

        # split the action line into a module name + arguments
        tokens = self.action.split(None, 1)
        if len(tokens) < 1:
            raise errors.AnsibleError("invalid/missing action in task. name: %s" % self.name)
        self.module_name = tokens[0]
        self.module_args = ''
        if len(tokens) > 1:
            self.module_args = tokens[1]

        import_tags = self.module_vars.get('tags',[])
        if type(import_tags) in [str,unicode]:
            # allow the user to list comma delimited tags
            import_tags = import_tags.split(",")

        # handle mutually incompatible options
        incompatibles = [ x for x in [ self.first_available_file, self.items_lookup_plugin ] if x is not None ]
        if len(incompatibles) > 1:
            raise errors.AnsibleError("with_(plugin), and first_available_file are mutually incompatible in a single task")

        # make first_available_file accessable to Runner code
        if self.first_available_file:
            self.module_vars['first_available_file'] = self.first_available_file

        if self.items_lookup_plugin is not None:
            self.module_vars['items_lookup_plugin'] = self.items_lookup_plugin
            self.module_vars['items_lookup_terms'] = self.items_lookup_terms

        # allow runner to see delegate_to option
        self.module_vars['delegate_to'] = self.delegate_to

        # make some task attributes accessible to Runner code
        self.module_vars['ignore_errors'] = self.ignore_errors
        self.module_vars['ignore_changed'] = self.ignore_changed
        self.module_vars['always_run'] = self.always_run

        # tags allow certain parts of a playbook to be run without running the whole playbook
        apply_tags = ds.get('tags', None)
        if apply_tags is not None:
            if type(apply_tags) in [ str, unicode ]:
                self.tags.append(apply_tags)
            elif type(apply_tags) == list:
                self.tags.extend(apply_tags)
        self.tags.extend(import_tags)

        if self.when is not None:
            if self.only_if != 'True':
                raise errors.AnsibleError('when obsoletes only_if, only use one or the other')
            self.only_if = utils.compile_when_to_only_if(self.when)

        if additional_conditions:
            self.only_if = [ self.only_if ] 
            self.only_if.extend(additional_conditions)

