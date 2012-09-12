# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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


class Task(object):

    __slots__ = [
        'name', 'action', 'only_if', 'async_seconds', 'async_poll_interval',
        'notify', 'module_name', 'module_args', 'module_vars',
        'play', 'notified_by', 'tags', 'register', 'with_items',
        'delegate_to', 'first_available_file', 'ignore_errors',
        'local_action', 'pause', 'task_type'
    ]

    # to prevent typos and such
    VALID_KEYS = [
         'name', 'action', 'only_if', 'async', 'poll', 'notify', 'with_items',
         'first_available_file', 'include', 'tags', 'register', 'ignore_errors',
         'delegate_to', 'local_action', 'pause'
    ]

    # The specific keys which identify a task's true type
    TASK_TYPES = ['action', 'local_action', 'pause']

    def __init__(self, play, ds, module_vars=None):
        ''' constructor loads from a task or handler datastructure '''

        for x in ds.keys():
            if not x in Task.VALID_KEYS:
                raise errors.AnsibleError("%s is not a legal parameter in an Ansible task or handler" % x)

        self.module_vars = module_vars
        self.play        = play

        # load various attributes
        self.tags         = [ 'all' ]
        self.register     = ds.get('register', None)

        # Lets talk about mutual exclusion for a minute, I hope you
        # brushed up on your set operations! The following are sets of
        # some keys that have special grouping conditions:
        #
        # All of the keys present in the play, etc
        present_keys = set(ds.keys())
        empty = set([])
        valid_keys = set(Task.VALID_KEYS)
        # One and Only One of these must be present
        task_type_keys = set(Task.TASK_TYPES)
        # Everything you can modify a task with
        non_type_keys = valid_keys - task_type_keys
        # You can't mix action and local action
        task_action_keys = set(['action', 'local_action'])
        # You can't specify a delegate to a local_action
        local_action_keys = set(['local_action', 'delegate_to'])
        # I don't understand how this combination would make any sense
        pause_delegate = set(['pause', 'delegate_to'])
        # These don't work either
        with_files = set(['with_items', 'first_available_file'])

        # Now lets go through and check for problems
        #
        # You need to have One and Only One of these
        if len(task_type_keys & present_keys) > 1:
            raise errors.AnsibleError("only one of 'action', 'local_action', and 'pause' may be present in a task")

        if len(task_type_keys & present_keys) == empty:
            raise errors.AnsibleError("one of 'action', 'local_action', or 'pause' must be present in a task")

        # One or the other
        if len(task_action_keys & present_keys) > 1:
            raise errors.AnsibleError("only one of 'action' and 'local_action' may be present in a task")

        # Local actions are already delegated
        if len(local_action_keys & present_keys) > 1:
            raise errors.AnsibleError("using 'local_action' is not compatable with 'delegate_to'")

        # These don't mix well either
        if len(with_files & present_keys) > 1:
            raise errors.AnsibleError("'with_items' and 'first_available_file' are mutually incompatible in a single task")

        # Makes no sense
        if len(pause_delegate & present_keys) > 1:
            raise errors.AnsibleError("using 'pause' is not compatable with 'delegate_to'")

        # Last-stop for syntax checking and type identification

        # Consider all present keys, then take away all the modifier
        # types, your resultant set should be left with exactly 1
        # item: the task's type. Verify this result by intersecting it
        # with the task_type_keys set. If only one element remains
        # then you have identified the type of this task. Any other
        # result else means that this is a malformed task description.
        #
        # With all the condition checking before this block this
        # should work every time (famous last words) to identify the
        # task type as well as catch any lingering syntax errors.
        type_candidate = present_keys - non_type_keys
        if len(type_candidate & task_type_keys) == 1:
            self.task_type = type_candidate.pop()
            self.module_vars['task_type'] = self.task_type
        else:
            desc = []
            for k,v in ds.iteritems():
                desc.append("[%s:%s]" % (k, str(v)))
            raise errors.AnsibleError("syntax error while parsing task: %s" % " ".join(desc))

        # Handle actions and optional delegates
        if self.task_type ==  'local_action':
            self.action = ds['local_action']
            self.delegate_to = '127.0.0.1'
            self.module_vars['delegate_to'] = self.delegate_to
            # Override this manually, they're like aliases
            self.task_type = 'action'
            self.module_vars['task_type'] = self.task_type
        elif self.task_type == 'action' in present_keys:
            self.action = ds['action']
            self.delegate_to = ds.get('delegate_to', None)
            self.module_vars['delegate_to'] = self.delegate_to
        else:
            self.action = ds[self.task_type]
            self.delegate_to = ds.get('delegate_to', None)

        # Every task needs a name! If it doesn't have a name it must
        # have either an action or pause statement.
        if not 'name' in present_keys:
            self.name = ds['action']
        else:
            self.name = ds['name']

        # notified by is used by Playbook code to flag which hosts
        # need to run a notifier
        self.notified_by = []

        # load various attributes
        self.only_if = ds.get('only_if', 'True')
        self.async_seconds = int(ds.get('async', 0))  # not async by default
        self.async_poll_interval = int(ds.get('poll', 10))  # default poll = 10 seconds
        self.notify = ds.get('notify', [])
        self.first_available_file = ds.get('first_available_file', None)
        self.with_items = ds.get('with_items', None)

        self.ignore_errors = ds.get('ignore_errors', False)

        # notify can be a string or a list, store as a list
        if isinstance(self.notify, basestring):
            self.notify = [ self.notify ]

        # split the action line into: [module-name, 'string of arguments']
        tokens = self.action.split(None, 1)

        # non action-type tasks don't start with a module name, so
        # just pass it the action and let it handle it's own argument
        # validation
        if not self.task_type == 'action':
            self.module_name = self.task_type
            self.module_args = self.action
        else:
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

        self.name = utils.template(self.name, self.module_vars)
        self.action = utils.template(self.action, self.module_vars)


        # make first_available_file accessable to Runner code
        if self.first_available_file:
            self.module_vars['first_available_file'] = self.first_available_file

        # process with_items so it can be used by Runner code
        if self.with_items is None:
            self.with_items = [ ]
        self.module_vars['items'] = self.with_items

        # make ignore_errors accessable to Runner code
        self.module_vars['ignore_errors'] = self.ignore_errors

        # tags allow certain parts of a playbook to be run without running the whole playbook
        apply_tags = ds.get('tags', None)
        if apply_tags is not None:
            if type(apply_tags) in [ str, unicode ]:
                self.tags.append(apply_tags)
            elif type(apply_tags) == list:
                self.tags.extend(apply_tags)
        self.tags.extend(import_tags)
