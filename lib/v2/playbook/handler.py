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

from v2.errors import AnsibleError
from v2.inventory import Host
from v2.playbook import Task

class Handler(Task):
    def __init__(self):
        self.triggered    = False
        self.triggered_by = []

    def flag_for_host(self, host):
        if not isinstance(host, Host):
            raise AnsibleError('handlers expected to be triggered by a Host(), instead got %s' % type(host))
        if host.name not in self.triggered_by:
            triggered_by.append(host.name)

    def get_has_triggered(self):
        return self.triggered

    def set_has_triggered(self, triggered):
        if not isinstance(triggered, bool):
            raise AnsibleError('a handlers triggered property should be a boolean, instead got %s' % type(triggered))
        self.triggered = triggered
