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

from ansible.errors import AnsibleError
from ansible.playbook.helpers import load_list_of_tasks
from ansible.playbook.task import Task

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class Handler(Task):

    def __init__(self, block=None, role=None, task_include=None):
        self._flagged_hosts = []

        super(Handler, self).__init__(block=block, role=role, task_include=task_include)

    def __repr__(self):
        ''' returns a human readable representation of the handler '''
        return "HANDLER: %s" % self.get_name()

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None, play=None):
        h = Handler(block=block, role=role, task_include=task_include)
        h.load_data(data, variable_manager=variable_manager, loader=loader)
        if h.action == 'include':
            filenames = h.args['_raw_params'].strip().split()
            retval = []
            for filename in filenames:
                display.debug('loading handlers from %s' % filename)
                ds = loader.load_from_file(filename)
                if ds is None:
                    continue
                elif not isinstance(ds, list):
                    raise AnsibleError("included task files must contain a list of tasks")
                handlers = load_list_of_tasks(ds, play=play, use_handlers=True, loader=loader)
                retval.extend(handlers)
            return retval

        return h

    def flag_for_host(self, host):
        #assert instanceof(host, Host)
        if host not in self._flagged_hosts:
            self._flagged_hosts.append(host)

    def has_triggered(self, host):
        return host in self._flagged_hosts

    def serialize(self):
        result = super(Handler, self).serialize()
        result['is_handler'] = True
        return result
