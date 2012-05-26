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

#############################################

#import ansible.inventory
#import ansible.runner
#import ansible.constants as C
#from ansible import utils
#from ansible import errors

class Task(object):

    __slots__ = [ 
        'name', 'action', 'only_if', 'async_seconds', 'async_poll_interval',
        'notify', 'module_name', 'module_args', 'module_vars', 'play', 'notified_by',
    ]

    def __init__(self, play, ds):

        self.play       = play

        # FIXME: error handling on invalid fields
        # action...

        self.name   = ds.get('name', None)
        self.action = ds.get('action', '')
        self.notified_by = []

        if self.name is None:
            self.name = self.action

        self.only_if = ds.get('only_if', 'True')
        self.async_seconds = int(ds.get('async', 0))  # not async by default
        self.async_poll_interval = int(ds.get('poll', 10))  # default poll = 10 seconds
        self.notify = ds.get('notify', [])
        if isinstance(self.notify, basestring):
            self.notify = [ self.notify ]

        tokens = self.action.split(None, 1)
        if len(tokens) < 1:
            # FIXME: better error handling
            raise Exception("invalid action in task: %s" % ds)

        self.module_name = tokens[0]
        self.module_args = ''
        if len(tokens) > 1:
            self.module_args = tokens[1]

        # include task specific vars
        self.module_vars = ds.get('vars', {})
        if 'first_available_file' in ds:
            self.module_vars['first_available_file'] = ds.get('first_available_file')


