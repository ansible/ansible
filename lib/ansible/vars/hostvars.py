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

STATIC_VARS = [
  'inventory_hostname', 'inventory_hostname_short',
  'inventory_file', 'inventory_dir', 'playbook_dir',
  'ansible_play_hosts', 'play_hosts', 'groups', 'ungrouped', 'group_names',
  'ansible_version', 'omit', 'role_names'
]

try:
    from hashlib import sha1
except ImportError:
    from sha import sha as sha1

__all__ = ['HostVars']

# Note -- this is a Mapping, not a MutableMapping
class HostVars(collections.Mapping):
    ''' A special view of vars_cache that adds values from the inventory when needed. '''

    def __init__(self, inventory, variable_manager, loader):
        self._lookup = dict()
        self._inventory = inventory
        self._loader = loader
        self._variable_manager = variable_manager
        self._cached_result = dict()

    def set_variable_manager(self, variable_manager):
        self._variable_manager = variable_manager

    def set_inventory(self, inventory):
        self._inventory = inventory

    def _find_host(self, host_name):
        return self._inventory.get_host(host_name)

    def __getitem__(self, host_name):
        host = self._find_host(host_name)
        if host is None:
            raise j2undefined

        data = self._variable_manager.get_vars(loader=self._loader, host=host, include_hostvars=False)

        sha1_hash = sha1(str(data).encode('utf-8')).hexdigest()
        if sha1_hash in self._cached_result:
            result = self._cached_result[sha1_hash]
        else:
            templar = Templar(variables=data, loader=self._loader)
            result = templar.template(data, fail_on_undefined=False, static_vars=STATIC_VARS)
            self._cached_result[sha1_hash] = result
        return result

    def set_host_variable(self, host, varname, value):
        self._variable_manager.set_host_variable(host, varname, value)

    def set_nonpersistent_facts(self, host, facts):
        self._variable_manager.set_nonpersistent_facts(host, facts)

    def set_host_facts(self, host, facts):
        self._variable_manager.set_host_facts(host, facts)

    def __contains__(self, host_name):
        return self._find_host(host_name) is not None

    def __iter__(self):
        for host in self._inventory.get_hosts(ignore_limits_and_restrictions=True):
            yield host

    def __len__(self):
        return len(self._inventory.get_hosts(ignore_limits_and_restrictions=True))

