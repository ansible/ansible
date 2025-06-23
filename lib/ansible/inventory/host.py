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

from collections.abc import Mapping, MutableMapping

from ansible.errors import AnsibleError
from ansible.inventory.group import Group, InventoryObjectType
from ansible.parsing.utils.addresses import patterns
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars, get_unique_id, validate_variable_name

from . import helpers  # this is left as a module import to facilitate easier unit test patching

__all__ = ['Host']


class Host:
    """A single ansible host."""
    base_type = InventoryObjectType.HOST

    # __slots__ = [ 'name', 'vars', 'groups' ]

    def __eq__(self, other):
        if not isinstance(other, Host):
            return False
        return self._uuid == other._uuid

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.get_name()

    def __repr__(self):
        return self.get_name()

    def __init__(self, name: str, port: int | str | None = None, gen_uuid: bool = True) -> None:
        name = helpers.remove_trust(name)

        self.vars: dict[str, t.Any] = {}
        self.groups: list[Group] = []
        self._uuid: str | None = None

        self.name: str = name
        self.address: str = name

        if port:
            self.set_variable('ansible_port', int(port))

        if gen_uuid:
            self._uuid = get_unique_id()

        self.implicit: bool = False

    def get_name(self) -> str:
        return self.name

    def populate_ancestors(self, additions: c.Iterable[Group] | None = None) -> None:
        # populate ancestors
        if additions is None:
            for group in self.groups:
                self.add_group(group)
        else:
            for group in additions:
                if group not in self.groups:
                    self.groups.append(group)

    def add_group(self, group: Group) -> bool:
        added = False
        # populate ancestors first
        for oldg in group.get_ancestors():
            if oldg not in self.groups:
                self.groups.append(oldg)

        # actually add group
        if group not in self.groups:
            self.groups.append(group)
            added = True
        return added

    def remove_group(self, group: Group) -> bool:
        removed = False
        if group in self.groups:
            self.groups.remove(group)
            removed = True

            # remove exclusive ancestors, xcept all!
            for oldg in group.get_ancestors():
                if oldg.name != 'all':
                    for childg in self.groups:
                        if oldg in childg.get_ancestors():
                            break
                    else:
                        self.remove_group(oldg)
        return removed

    def set_variable(self, key: str, value: t.Any) -> None:
        key = helpers.remove_trust(key)

        try:
            validate_variable_name(key)
        except AnsibleError as ex:
            Display().deprecated(msg=f'Accepting inventory variable with invalid name {key!r}.', version='2.23', help_text=ex._help_text, obj=ex.obj)

        if key in self.vars and isinstance(self.vars[key], MutableMapping) and isinstance(value, Mapping):
            self.vars = combine_vars(self.vars, {key: value})
        else:
            self.vars[key] = value

    def get_groups(self) -> list[Group]:
        return self.groups

    def get_magic_vars(self) -> dict[str, t.Any]:
        results: dict[str, t.Any] = dict(
            inventory_hostname=self.name,
        )

        # FUTURE: these values should be dynamically calculated on access ala the rest of magic vars
        if patterns['ipv4'].match(self.name) or patterns['ipv6'].match(self.name):
            results['inventory_hostname_short'] = self.name
        else:
            results['inventory_hostname_short'] = self.name.split('.')[0]

        results['group_names'] = sorted([g.name for g in self.get_groups() if g.name != 'all'])

        return results

    def get_vars(self) -> dict[str, t.Any]:
        return combine_vars(self.vars, self.get_magic_vars())
