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

from ansible import errors
from ansible import utils
from ansible.module_utils.splitter import split_args
import os
import ansible.utils.template as template
import sys

class Task(object):

    __slots__ = [
        'name', 'meta', 'action', 'when', 'async_seconds', 'async_poll_interval',
        'notify', 'module_name', 'module_args', 'module_vars', 'play_vars', 'play_file_vars', 'role_vars', 'role_params', 'default_vars',
        'play', 'notified_by', 'tags', 'register', 'role_name',
        'delegate_to', 'first_available_file', 'ignore_errors',
        'local_action', 'transport', 'sudo', 'remote_user', 'sudo_user', 'sudo_pass',
        'items_lookup_plugin', 'items_lookup_terms', 'environment', 'args',
        'any_errors_fatal', 'changed_when', 'failed_when', 'always_run', 'delay', 'retries', 'until',
        'su', 'su_user', 'su_pass', 'no_log', 'run_once',
    ]

    # to prevent typos and such
    VALID_KEYS = [
         'name', 'meta', 'action', 'when', 'async', 'poll', 'notify',
         'first_available_file', 'include', 'tags', 'register', 'ignore_errors',
         'delegate_to', 'local_action', 'transport', 'remote_user', 'sudo', 'sudo_user',
         'sudo_pass', 'when', 'connection', 'environment', 'args',
         'any_errors_fatal', 'changed_when', 'failed_when', 'always_run', 'delay', 'retries', 'until',
         'su', 'su_user', 'su_pass', 'no_log', 'run_once',
    ]

    def __init__(self, play, ds, module_vars=None, play_vars=None, play_file_vars=None, role_vars=None, role_params=None, default_vars=None, additional_conditions=None, role_name=None):
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
                    raise errors.AnsibleError("multiple actions specified in task: '%s' and '%s'" % (x, ds.get('name', ds['action'])))
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
                if isinstance(ds[x], basestring):
                    param = ds[x].strip()
                    # Only a variable, no logic
                    if (param.startswith('{{') and
                        param.find('}}') == len(ds[x]) - 2 and
                        param.find('|') == -1):
                        utils.warning("It is unnecessary to use '{{' in loops, leave variables in loop expressions bare.")

                plugin_name = x.replace("with_","")
                if plugin_name in utils.plugins.lookup_loader:
                    ds['items_lookup_plugin'] = plugin_name
                    ds['items_lookup_terms'] = ds[x]
                    ds.pop(x)
                else:
                    raise errors.AnsibleError("cannot find lookup plugin named %s for usage in with_%s" % (plugin_name, plugin_name))

            elif x in [ 'changed_when', 'failed_when', 'when']:
                if isinstance(ds[x], basestring):
                    param = ds[x].strip()
                    # Only a variable, no logic
                    if (param.startswith('{{') and
                        param.find('}}') == len(ds[x]) - 2 and
                        param.find('|') == -1):
                        utils.warning("It is unnecessary to use '{{' in conditionals, leave variables in loop expressions bare.")
            elif x.startswith("when_"):
                utils.deprecated("The 'when_' conditional has been removed. Switch to using the regular unified 'when' statements as described on docs.ansible.com.","1.5", removed=True)

                if 'when' in ds:
                    raise errors.AnsibleError("multiple when_* statements specified in task %s" % (ds.get('name', ds['action'])))
                when_name = x.replace("when_","")
                ds['when'] = "%s %s" % (when_name, ds[x])
                ds.pop(x)
            elif not x in Task.VALID_KEYS:
                raise errors.AnsibleError("%s is not a legal parameter in an Ansible task or handler" % x)

        self.module_vars    = module_vars
        self.play_vars      = play_vars
        self.play_file_vars = play_file_vars
        self.role_vars      = role_vars
        self.role_params    = role_params
        self.default_vars   = default_vars
        self.play           = play

        # load various attributes
        self.name         = ds.get('name', None)
        self.tags         = [ 'all' ]
        self.register     = ds.get('register', None)
        self.sudo         = utils.boolean(ds.get('sudo', play.sudo))
        self.su           = utils.boolean(ds.get('su', play.su))
        self.environment  = ds.get('environment', {})
        self.role_name    = role_name
        self.no_log       = utils.boolean(ds.get('no_log', "false")) or self.play.no_log
        self.run_once     = utils.boolean(ds.get('run_once', 'false'))

        #Code to allow do until feature in a Task 
        if 'until' in ds:
            if not ds.get('register'):
                raise errors.AnsibleError("register keyword is mandatory when using do until feature")
            self.module_vars['delay']     = ds.get('delay', 5)
            self.module_vars['retries']   = ds.get('retries', 3)
            self.module_vars['register']  = ds.get('register', None)
            self.until                    = ds.get('until')
            self.module_vars['until']     = self.until

        # rather than simple key=value args on the options line, these represent structured data and the values
        # can be hashes and lists, not just scalars
        self.args         = ds.get('args', {})

        # get remote_user for task, then play, then playbook
        if ds.get('remote_user') is not None:
            self.remote_user      = ds.get('remote_user')
        elif ds.get('remote_user', play.remote_user) is not None:
            self.remote_user      = ds.get('remote_user', play.remote_user)
        else:
            self.remote_user      = ds.get('remote_user', play.playbook.remote_user)

        self.sudo_user    = None
        self.sudo_pass    = None
        self.su_user      = None
        self.su_pass      = None

        if self.sudo:
            self.sudo_user    = ds.get('sudo_user', play.sudo_user)
            self.sudo_pass    = ds.get('sudo_pass', play.playbook.sudo_pass)
        elif self.su:
            self.su_user      = ds.get('su_user', play.su_user)
            self.su_pass      = ds.get('su_pass', play.playbook.su_pass)

        # Fail out if user specifies a sudo param with a su param in a given play
        if (ds.get('sudo') or ds.get('sudo_user') or ds.get('sudo_pass')) and \
                (ds.get('su') or ds.get('su_user') or ds.get('su_pass')):
            raise errors.AnsibleError('sudo params ("sudo", "sudo_user", "sudo_pass") '
                                      'and su params "su", "su_user", "su_pass") '
                                      'cannot be used together')

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
        self.when    = ds.get('when', None)
        self.changed_when = ds.get('changed_when', None)
        self.failed_when = ds.get('failed_when', None)

        # combine the default and module vars here for use in templating
        all_vars = self.default_vars.copy()
        all_vars = utils.combine_vars(all_vars, self.play_vars)
        all_vars = utils.combine_vars(all_vars, self.play_file_vars)
        all_vars = utils.combine_vars(all_vars, self.role_vars)
        all_vars = utils.combine_vars(all_vars, self.module_vars)
        all_vars = utils.combine_vars(all_vars, self.role_params)

        self.async_seconds = ds.get('async', 0)  # not async by default
        self.async_seconds = template.template_from_string(play.basedir, self.async_seconds, all_vars)
        self.async_seconds = int(self.async_seconds)
        self.async_poll_interval = ds.get('poll', 10)  # default poll = 10 seconds
        self.async_poll_interval = template.template_from_string(play.basedir, self.async_poll_interval, all_vars)
        self.async_poll_interval = int(self.async_poll_interval)
        self.notify = ds.get('notify', [])
        self.first_available_file = ds.get('first_available_file', None)

        self.items_lookup_plugin = ds.get('items_lookup_plugin', None)
        self.items_lookup_terms  = ds.get('items_lookup_terms', None)
     

        self.ignore_errors = ds.get('ignore_errors', False)
        self.any_errors_fatal = ds.get('any_errors_fatal', play.any_errors_fatal)

        self.always_run = ds.get('always_run', False)

        # action should be a string
        if not isinstance(self.action, basestring):
            raise errors.AnsibleError("action is of type '%s' and not a string in task. name: %s" % (type(self.action).__name__, self.name))

        # notify can be a string or a list, store as a list
        if isinstance(self.notify, basestring):
            self.notify = [ self.notify ]

        # split the action line into a module name + arguments
        try:
            tokens = split_args(self.action)
        except Exception, e:
            if "unbalanced" in str(e):
                raise errors.AnsibleError("There was an error while parsing the task %s.\n" % repr(self.action) + \
                                          "Make sure quotes are matched or escaped properly")
            else:
                raise
        if len(tokens) < 1:
            raise errors.AnsibleError("invalid/missing action in task. name: %s" % self.name)
        self.module_name = tokens[0]
        self.module_args = ''
        if len(tokens) > 1:
            self.module_args = " ".join(tokens[1:])

        import_tags = self.module_vars.get('tags',[])
        if type(import_tags) in [int,float]:
            import_tags = str(import_tags)
        elif type(import_tags) in [str,unicode]:
            # allow the user to list comma delimited tags
            import_tags = import_tags.split(",")

        # handle mutually incompatible options
        incompatibles = [ x for x in [ self.first_available_file, self.items_lookup_plugin ] if x is not None ]
        if len(incompatibles) > 1:
            raise errors.AnsibleError("with_(plugin), and first_available_file are mutually incompatible in a single task")

        # make first_available_file accessible to Runner code
        if self.first_available_file:
            self.module_vars['first_available_file'] = self.first_available_file
            # make sure that the 'item' variable is set when using
            # first_available_file (issue #8220)
            if 'item' not in self.module_vars:
                self.module_vars['item'] = ''

        if self.items_lookup_plugin is not None:
            self.module_vars['items_lookup_plugin'] = self.items_lookup_plugin
            self.module_vars['items_lookup_terms'] = self.items_lookup_terms

        # allow runner to see delegate_to option
        self.module_vars['delegate_to'] = self.delegate_to

        # make some task attributes accessible to Runner code
        self.module_vars['ignore_errors'] = self.ignore_errors
        self.module_vars['register'] = self.register
        self.module_vars['changed_when'] = self.changed_when
        self.module_vars['failed_when'] = self.failed_when
        self.module_vars['always_run'] = self.always_run

        # tags allow certain parts of a playbook to be run without running the whole playbook
        apply_tags = ds.get('tags', None)
        if apply_tags is not None:
            if type(apply_tags) in [ str, unicode ]:
                self.tags.append(apply_tags)
            elif type(apply_tags) in [ int, float ]:
                self.tags.append(str(apply_tags))
            elif type(apply_tags) == list:
                self.tags.extend(apply_tags)
        self.tags.extend(import_tags)

        if additional_conditions:
            new_conditions = additional_conditions[:]
            if self.when:
                new_conditions.append(self.when)
            self.when = new_conditions
