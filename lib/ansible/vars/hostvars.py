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

from ansible.template import Templar

__all__ = ['HostVars']

class HostVars(dict):
    ''' A special view of vars_cache that adds values from the inventory when needed. '''

    def __init__(self, vars_manager, inventory, loader):
        self._vars_manager = vars_manager
        self._inventory    = inventory
        self._loader       = loader
        self._lookup       = {}

        #self.update(vars_cache)

    def __getitem__(self, host_name):
        
        if host_name not in self._lookup:
            host = self._inventory.get_host(host_name)
            result = self._vars_manager.get_vars(loader=self._loader, host=host)
            #result.update(self._vars_cache.get(host, {}))
            #templar = Templar(variables=self._vars_cache, loader=self._loader)
            #self._lookup[host] = templar.template(result)
            self._lookup[host_name] = result
        return self._lookup[host_name]

