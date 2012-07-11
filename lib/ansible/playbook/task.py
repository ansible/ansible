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

from ansible import errors
from ansible import utils

class Task(object):

    __slots__ = [ 
        'name', 'action', 'only_if', 'async_seconds', 'async_poll_interval',
        'notify', 'module_name', 'module_args', 'module_vars', 
        'play', 'notified_by', 'tags'
    ]

    def __init__(self, play, ds, module_vars=None):
        ''' constructor loads from a task or handler datastructure '''

        # TODO: more error handling
        # include task specific vars

        self.module_vars = module_vars

        self.play        = play
        self.name        = ds.get('name', None)
        self.action      = ds.get('action', '')
        self.tags        = [ 'all' ]

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
            raise errors.AnsibleError("invalid/missing action in task")

        self.module_name = tokens[0]
        self.module_args = ''
        if len(tokens) > 1:
            self.module_args = tokens[1]


        self.name = utils.template(self.name, self.module_vars)
        self.action = utils.template(self.name, self.module_vars)


        if 'first_available_file' in ds:
            self.module_vars['first_available_file'] = ds.get('first_available_file')

        # tags allow certain parts of a playbook to be run without
        # running the whole playbook
        apply_tags = ds.get('tags', None)
        if apply_tags is not None:
            if type(apply_tags) in [ str, unicode ]:
                self.tags.append(apply_tags)
            elif type(apply_tags) == list:
                self.tags.extend(apply_tags)

                


