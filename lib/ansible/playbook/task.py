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
        'play', 'notified_by', 'tags', 'with_items', 'first_available_file', 'ignore_errors'
    ]

    # to prevent typos and such
    VALID_KEYS = [
         'name', 'action', 'only_if', 'async', 'poll', 'notify', 'with_items', 'first_available_file',
         'include', 'tags', 'ignore_errors'
    ]

    def __init__(self, play, ds, module_vars=None):
        ''' constructor loads from a task or handler datastructure '''

        for x in ds.keys():
            if not x in Task.VALID_KEYS:
                raise errors.AnsibleError("%s is not a legal parameter in an Ansible task or handler" % x)

        self.module_vars = module_vars
        self.play        = play

        # load various attributes
        self.name        = ds.get('name', None)
        self.action      = ds.get('action', '')
        self.tags        = [ 'all' ]

        # notified by is used by Playbook code to flag which hosts
        # need to run a notifier
        self.notified_by = []

        # if no name is specified, use the action line as the name
        if self.name is None:
            self.name = self.action

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

        self.name = utils.template(self.name, self.module_vars)
        self.action = utils.template(self.action, self.module_vars)

        # handle mutually incompatible options
        if self.with_items is not None and self.first_available_file is not None:
            raise errors.AnsibleError("with_items and first_available_file are mutually incompatible in a single task")

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
                
