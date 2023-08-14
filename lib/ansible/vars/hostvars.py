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

from collections.abc import Mapping

from ansible.template import Templar, AnsibleUndefined

__all__ = ['HostVars', 'HostVarsVars']


class HostVars(Mapping):
    """A special (read-only) view of vars_cache that adds values from the inventory when needed."""

    def __init__(self, inventory, variable_manager, loader):
        self._inventory = inventory
        self._loader = loader
        self._variable_manager = variable_manager

    def __setstate__(self, state):
        self.__dict__.update(state)

        # Methods __getstate__ and __setstate__ of VariableManager do not
        # preserve _loader and _hostvars attributes to improve pickle
        # performance and memory utilization. Since HostVars holds values
        # of those attributes already, assign them if needed.
        if self._variable_manager._loader is None:
            self._variable_manager._loader = self._loader

        if self._variable_manager._hostvars is None:
            self._variable_manager._hostvars = self

    def __getitem__(self, host_name):
        # does not use inventory.hosts so it can create localhost on demand
        host = self._inventory.get_host(host_name)
        if host is None:
            return AnsibleUndefined(name="hostvars['%s']" % host_name)

        return HostVarsVars(
            self._variable_manager.get_vars(host=host, include_hostvars=False),
            loader=self._loader
        )

    def __contains__(self, host_name):
        # does not use inventory.hosts so it can create localhost on demand
        return self._inventory.get_host(host_name) is not None

    def __iter__(self):
        for host in self._inventory.hosts:
            yield host

    def __len__(self):
        return len(self._inventory.hosts)

    def __repr__(self):
        return repr({h: self.get(h) for h in self._inventory.hosts})

    def __deepcopy__(self, memo):
        # We do not need to deepcopy because HostVars is immutable,
        # however we have to implement the method so we can deepcopy
        # variables' dicts that contain HostVars.
        return self


class HostVarsVars(Mapping):

    def __init__(self, variables, loader):
        self._vars = variables
        self._loader = loader

    def __getitem__(self, var):
        templar = Templar(variables=self._vars, loader=self._loader)
        return templar.template(self._vars[var], fail_on_undefined=False)

    def __contains__(self, var):
        return var in self._vars

    def __iter__(self):
        for var in self._vars.keys():
            yield var

    def __len__(self):
        return len(self._vars.keys())

    def __repr__(self):
        templar = Templar(variables=self._vars, loader=self._loader)
        return repr(templar.template(self._vars, fail_on_undefined=False))
