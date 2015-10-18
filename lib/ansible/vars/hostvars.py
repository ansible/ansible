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

import collections
import sys

from jinja2 import Undefined as j2undefined

from ansible import constants as C
from ansible.inventory.host import Host
from ansible.template import Templar

__all__ = ['HostVars']

# Note -- this is a Mapping, not a MutableMapping
class HostVars(collections.Mapping):
    ''' A special view of vars_cache that adds values from the inventory when needed. '''

    def __init__(self, play, inventory, variable_manager, loader):
        self._lookup = dict()
        self._loader = loader
        self._play = play
        self._variable_manager = variable_manager

        hosts = inventory.get_hosts(ignore_limits_and_restrictions=True)

        # check to see if localhost is in the hosts list, as we
        # may have it referenced via hostvars but if created implicitly
        # it doesn't sow up in the hosts list
        has_localhost = False
        for host in hosts:
            if host.name in C.LOCALHOST:
                has_localhost = True
                break

        if not has_localhost:
            new_host =  Host(name='localhost')
            new_host.set_variable("ansible_python_interpreter", sys.executable)
            new_host.set_variable("ansible_connection", "local")
            new_host.address = '127.0.0.1'
            hosts.append(new_host)

        for host in hosts:
            self._lookup[host.name] = host

    def __getitem__(self, host_name):

        if host_name not in self._lookup:
            return j2undefined

        host = self._lookup.get(host_name)
        data = self._variable_manager.get_vars(loader=self._loader, host=host, play=self._play, include_hostvars=False)
        templar = Templar(variables=data, loader=self._loader)
        return templar.template(data, fail_on_undefined=False)

    def __contains__(self, host_name):
        item = self.get(host_name)
        if item and item is not j2undefined:
            return True
        return False

    def __iter__(self):
        for host in self._lookup:
            yield host

    def __len__(self):
        return len(self._lookup)

    def __getstate__(self):
        return dict(loader=self._loader, lookup=self._lookup, play=self._play, var_manager=self._variable_manager)

    def __setstate__(self, data):
        self._play = data.get('play')
        self._loader = data.get('loader')
        self._lookup = data.get('lookup')
        self._variable_manager = data.get('var_manager')
