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

import collections.abc as c
import typing as t

from ansible.module_utils import datatag

if t.TYPE_CHECKING:
    from ansible.inventory.manager import InventoryManager
    from ansible.parsing.dataloader import DataLoader
    from ansible._internal._templating._jinja_common import Marker
    from ansible.vars.manager import VariableManager


__all__ = ['HostVars', 'HostVarsVars']


class HostVars(c.Mapping):
    """A read-only wrapper to enable on-demand templating of a specific host's variables under that host's variable context."""
    # DTFIX-MERGE: why isn't this dict-ish enough to render eg `debug: var=hostvars`?

    def __init__(self, inventory: InventoryManager, variable_manager: VariableManager, loader: DataLoader) -> None:
        self._inventory = inventory
        self._loader = loader
        self._variable_manager = variable_manager

        variable_manager._hostvars = self

    def __getitem__(self, key: str) -> HostVarsVars | Marker:
        # does not use inventory.hosts, so it can create localhost on demand
        host = self._inventory.get_host(key)

        if host is None:
            # DTFIX-MERGE: untangle HostVars/HostVarsVars setup so we don't need to defer this import
            from ansible._internal._templating._jinja_bits import _undef

            return _undef(f"hostvars['{key}']")

        # DTFIX-FUTURE: this should be able to fetch play/task from a context so that vars defined at those layers are available within hostvarsvars
        data = self._variable_manager.get_vars(host=host, include_hostvars=False)

        return HostVarsVars(data, loader=self._loader, host=key)

    def __contains__(self, item: object) -> bool:
        # does not use inventory.hosts, so it can create localhost on demand
        return self._inventory.get_host(item) is not None

    def __iter__(self) -> t.Iterator[str]:
        yield from self._inventory.hosts

    def __len__(self) -> int:
        return len(self._inventory.hosts)

    def __deepcopy__(self, memo: t.Any) -> HostVars:
        # this object may be stored in a var dict that is itself deep copied, but since the underlying data
        # is supposed to be immutable, we don't need to actually copy the data
        return self


class HostVarsVars(c.Mapping):
    """A read-only view of a specific host's vars that will template on access under that host's variable context."""

    def __init__(self, variables: dict[str, t.Any], loader: DataLoader | None, host: str) -> None:
        # DTFIX-MERGE: can we eliminate this deferred import?
        from ansible._internal._templating._engine import TemplateEngine

        self._vars = variables
        self._templar = TemplateEngine(variables=variables, loader=loader)
        self._host = host

    def __getitem__(self, key: str) -> t.Any:
        return self._templar.template(self._vars[key])

    def __contains__(self, item: object) -> bool:
        return item in self._vars

    def __iter__(self) -> t.Iterator[str]:
        yield from self._vars

    def __len__(self) -> int:
        return len(self._vars)

    def __repr__(self) -> str:
        return f'HostVarsVars({self._host=!r}, ...)'

    def __deepcopy__(self, memo: t.Any) -> HostVarsVars:
        # this may be stored in a var dict that is itself deep copied, but since the underlying data
        # is supposed to be immutable, we don't need to actually copy the data
        return self


# DTFIX-MERGE: is there a better way to add this to the ignorable types in the module_utils code
datatag._untaggable_types.update({HostVars, HostVarsVars})
