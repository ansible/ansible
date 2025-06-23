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

import typing as t

from collections.abc import Mapping, MutableMapping
from enum import Enum
from itertools import chain

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars, validate_variable_name

from . import helpers  # this is left as a module import to facilitate easier unit test patching

display = Display()

if t.TYPE_CHECKING:
    from .host import Host


def to_safe_group_name(name, replacer="_", force=False, silent=False):
    # Converts 'bad' characters in a string to underscores (or provided replacer) so they can be used as Ansible hosts or groups

    warn = ''
    if name:  # when deserializing we might not have name yet
        invalid_chars = C.INVALID_VARIABLE_NAMES.findall(name)
        if invalid_chars:
            msg = 'invalid character(s) "%s" in group name (%s)' % (to_text(set(invalid_chars)), to_text(name))
            if C.TRANSFORM_INVALID_GROUP_CHARS not in ('never', 'ignore') or force:
                name = C.INVALID_VARIABLE_NAMES.sub(replacer, name)
                if not (silent or C.TRANSFORM_INVALID_GROUP_CHARS == 'silently'):
                    display.vvvv('Replacing ' + msg)
                    warn = 'Invalid characters were found in group names and automatically replaced, use -vvvv to see details'
            else:
                if C.TRANSFORM_INVALID_GROUP_CHARS == 'never':
                    display.vvvv('Not replacing %s' % msg)
                    warn = 'Invalid characters were found in group names but not replaced, use -vvvv to see details'

    if warn:
        display.warning(warn)

    return name


class InventoryObjectType(Enum):
    HOST = 0
    GROUP = 1


class Group:
    """A group of ansible hosts."""
    base_type = InventoryObjectType.GROUP

    # __slots__ = [ 'name', 'hosts', 'vars', 'child_groups', 'parent_groups', 'depth', '_hosts_cache' ]

    def __init__(self, name: str) -> None:
        name = helpers.remove_trust(name)

        self.depth: int = 0
        self.name: str = to_safe_group_name(name)
        self.hosts: list[Host] = []
        self._hosts: set[str] | None = None
        self.vars: dict[str, t.Any] = {}
        self.child_groups: list[Group] = []
        self.parent_groups: list[Group] = []
        self._hosts_cache: list[Host] | None = None
        self.priority: int = 1

    def __repr__(self):
        return self.get_name()

    def __str__(self):
        return self.get_name()

    def _walk_relationship(self, rel, include_self=False, preserve_ordering=False) -> set[Group] | list[Group]:
        """
        Given `rel` that is an iterable property of Group,
        consitituting a directed acyclic graph among all groups,
        Returns a set of all groups in full tree
        A   B    C
        |  / |  /
        | /  | /
        D -> E
        |  /    vertical connections
        | /     are directed upward
        F
        Called on F, returns set of (A, B, C, D, E)
        """
        seen: set[Group] = set([])
        unprocessed = set(getattr(self, rel))
        if include_self:
            unprocessed.add(self)
        if preserve_ordering:
            ordered: list[Group] = [self] if include_self else []
            ordered.extend(getattr(self, rel))

        while unprocessed:
            seen.update(unprocessed)
            new_unprocessed = set([])

            for new_item in chain.from_iterable(getattr(g, rel) for g in unprocessed):
                new_unprocessed.add(new_item)
                if preserve_ordering:
                    if new_item not in seen:
                        ordered.append(new_item)

            new_unprocessed.difference_update(seen)
            unprocessed = new_unprocessed

        if preserve_ordering:
            return ordered
        return seen

    def get_ancestors(self) -> set[Group]:
        return t.cast(set, self._walk_relationship('parent_groups'))

    def get_descendants(self, **kwargs) -> set[Group] | list[Group]:
        return self._walk_relationship('child_groups', **kwargs)

    @property
    def host_names(self) -> set[str]:
        if self._hosts is None:
            self._hosts = {h.name for h in self.hosts}
        return self._hosts

    def get_name(self) -> str:
        return self.name

    def add_child_group(self, group: Group) -> bool:
        added = False
        if self == group:
            raise Exception("can't add group to itself")

        # don't add if it's already there
        if group not in self.child_groups:

            # prepare list of group's new ancestors this edge creates
            start_ancestors = group.get_ancestors()
            new_ancestors = self.get_ancestors()
            if group in new_ancestors:
                raise AnsibleError("Adding group '%s' as child to '%s' creates a recursive dependency loop." % (to_native(group.name), to_native(self.name)))
            new_ancestors.add(self)
            new_ancestors.difference_update(start_ancestors)

            added = True
            self.child_groups.append(group)

            # update the depth of the child
            group.depth = max([self.depth + 1, group.depth])

            # update the depth of the grandchildren
            group._check_children_depth()

            # now add self to child's parent_groups list, but only if there
            # isn't already a group with the same name
            if self.name not in [g.name for g in group.parent_groups]:
                group.parent_groups.append(self)
                for h in group.get_hosts():
                    h.populate_ancestors(additions=new_ancestors)

            self.clear_hosts_cache()
        return added

    def _check_children_depth(self) -> None:

        depth = self.depth
        start_depth = self.depth  # self.depth could change over loop
        seen = set([])
        unprocessed = set(self.child_groups)

        while unprocessed:
            seen.update(unprocessed)
            depth += 1
            to_process = unprocessed.copy()
            unprocessed = set([])
            for g in to_process:
                if g.depth < depth:
                    g.depth = depth
                    unprocessed.update(g.child_groups)
            if depth - start_depth > len(seen):
                raise AnsibleError("The group named '%s' has a recursive dependency loop." % to_native(self.name))

    def add_host(self, host: Host) -> bool:
        added = False
        if host.name not in self.host_names:
            self.hosts.append(host)
            self._hosts.add(host.name)
            host.add_group(self)
            self.clear_hosts_cache()
            added = True
        return added

    def remove_host(self, host: Host) -> bool:
        removed = False
        if host.name in self.host_names:
            self.hosts.remove(host)
            self._hosts.remove(host.name)
            host.remove_group(self)
            self.clear_hosts_cache()
            removed = True
        return removed

    def set_variable(self, key: str, value: t.Any) -> None:
        key = helpers.remove_trust(key)

        try:
            validate_variable_name(key)
        except AnsibleError as ex:
            Display().deprecated(msg=f'Accepting inventory variable with invalid name {key!r}.', version='2.23', help_text=ex._help_text, obj=ex.obj)

        if key == 'ansible_group_priority':
            self.set_priority(int(value))
        else:
            if key in self.vars and isinstance(self.vars[key], MutableMapping) and isinstance(value, Mapping):
                self.vars = combine_vars(self.vars, {key: value})
            else:
                self.vars[key] = value

    def clear_hosts_cache(self) -> None:

        self._hosts_cache = None
        for g in self.get_ancestors():
            g._hosts_cache = None

    def get_hosts(self) -> list[Host]:

        if self._hosts_cache is None:
            self._hosts_cache = self._get_hosts()
        return self._hosts_cache

    def _get_hosts(self) -> list[Host]:

        hosts: list[Host] = []
        seen: set[Host] = set()
        for kid in self.get_descendants(include_self=True, preserve_ordering=True):
            kid_hosts = kid.hosts
            for kk in kid_hosts:
                if kk not in seen:
                    seen.add(kk)
                    if self.name == 'all' and kk.implicit:
                        continue
                    hosts.append(kk)
        return hosts

    def get_vars(self) -> dict[str, t.Any]:
        return self.vars.copy()

    def set_priority(self, priority: int | str) -> None:
        try:
            self.priority = int(priority)
        except TypeError:
            # FIXME: warn about invalid priority
            pass
