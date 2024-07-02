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

from __future__ import annotations

from collections.abc import Mapping
from functools import cached_property

from ansible import constants as C
from ansible.template import Templar, AnsibleUndefined


__all__ = ['HostVars', 'HostVarsVars']


# Note -- this is a Mapping, not a MutableMapping
class HostVars(Mapping):
    ''' A special view of vars_cache that adds values from the inventory when needed. '''

    def __init__(self, inventory, variable_manager, loader):
        self._inventory = inventory
        self._loader = loader
        self._variable_manager = variable_manager
        variable_manager._hostvars = self

    def set_variable_manager(self, variable_manager):
        self._variable_manager = variable_manager
        variable_manager._hostvars = self

    def set_inventory(self, inventory):
        self._inventory = inventory

    def _find_host(self, host_name):
        # does not use inventory.hosts so it can create localhost on demand
        return self._inventory.get_host(host_name)

    def raw_get(self, host_name):
        '''
        Similar to __getitem__, however the returned data is not run through
        the templating engine to expand variables in the hostvars.
        '''
        host = self._find_host(host_name)
        if host is None:
            return AnsibleUndefined(name="hostvars['%s']" % host_name)

        return self._variable_manager.get_vars(host=host, include_hostvars=False)

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
        data = self.raw_get(host_name)
        if isinstance(data, AnsibleUndefined):
            return data
        return HostVarsVars(data, loader=self._loader)

    def set_host_variable(self, host, varname, value):
        self._variable_manager.set_host_variable(host, varname, value)

    def set_nonpersistent_facts(self, host, facts):
        self._variable_manager.set_nonpersistent_facts(host, facts)

    def set_host_facts(self, host, facts):
        self._variable_manager.set_host_facts(host, facts)

    def __contains__(self, host_name):
        # does not use inventory.hosts so it can create localhost on demand
        return self._find_host(host_name) is not None

    def __iter__(self):
        yield from self._inventory.hosts

    def __len__(self):
        return len(self._inventory.hosts)

    def __repr__(self):
        out = {}
        for host in self._inventory.hosts:
            out[host] = self.get(host)
        return repr(out)

    def __deepcopy__(self, memo):
        # We do not need to deepcopy because HostVars is immutable,
        # however we have to implement the method so we can deepcopy
        # variables' dicts that contain HostVars.
        return self


class HostVarsVars(Mapping):

    def __init__(self, variables, loader):
        self._vars = variables
        self._loader = loader

    @cached_property
    def _templar(self):
        # NOTE: this only has access to the host's own vars,
        # so templates that depend on vars in other scopes will not work.
        return Templar(variables=self._vars, loader=self._loader)

    def __getitem__(self, var):
        return self._templar.template(self._vars[var], fail_on_undefined=False, static_vars=C.INTERNAL_STATIC_VARS)

    def __contains__(self, var):
        return (var in self._vars)

    def __iter__(self):
        yield from self._vars.keys()

    def __len__(self):
        return len(self._vars.keys())

    def __repr__(self):
        return repr(self._templar.template(self._vars, fail_on_undefined=False, static_vars=C.INTERNAL_STATIC_VARS))

    def __getstate__(self):
        ''' override serialization here to avoid
            pickle issues with templar and Jinja native'''
        state = self.__dict__.copy()
        state.pop('_templar', None)
        return state
