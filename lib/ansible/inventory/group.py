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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from itertools import chain

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native, to_text

from ansible.utils.display import Display

display = Display()


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
                    warn = True
                    warn = 'Invalid characters were found in group names but not replaced, use -vvvv to see details'

                # remove this message after 2.10 AND changing the default to 'always'
                display.deprecated('The TRANSFORM_INVALID_GROUP_CHARS settings is set to allow bad characters in group names by default,'
                                   ' this will change, but still be user configurable on deprecation', version='2.10')

    if warn:
        display.warning(warn)

    return name


class Group:
    ''' a group of ansible hosts '''

    # __slots__ = [ 'name', 'hosts', 'vars', 'child_groups', 'parent_groups', 'depth', '_hosts_cache' ]

    def __init__(self, name=None):

        self.depth = 0
        self.name = to_safe_group_name(name)
        self.hosts = []
        self._hosts = None
        self.vars = {}
        self.child_groups = []
        self.parent_groups = []
        self._hosts_cache = None
        self.priority = 1

    def __repr__(self):
        return self.get_name()

    def __str__(self):
        return self.get_name()

    def __getstate__(self):
        return self.serialize()

    def __setstate__(self, data):
        return self.deserialize(data)

    def serialize(self):
        parent_groups = []
        for parent in self.parent_groups:
            parent_groups.append(parent.serialize())

        self._hosts = None

        result = dict(
            name=self.name,
            vars=self.vars.copy(),
            parent_groups=parent_groups,
            depth=self.depth,
            hosts=self.hosts,
        )

        return result

    def deserialize(self, data):
        self.__init__()
        self.name = data.get('name')
        self.vars = data.get('vars', dict())
        self.depth = data.get('depth', 0)
        self.hosts = data.get('hosts', [])
        self._hosts = None

        parent_groups = data.get('parent_groups', [])
        for parent_data in parent_groups:
            g = Group()
            g.deserialize(parent_data)
            self.parent_groups.append(g)

    def _walk_relationship(self, rel, include_self=False, preserve_ordering=False):
        '''
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
        '''
        seen = set([])
        unprocessed = set(getattr(self, rel))
        if include_self:
            unprocessed.add(self)
        if preserve_ordering:
            ordered = [self] if include_self else []
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

    def get_ancestors(self):
        return self._walk_relationship('parent_groups')

    def get_descendants(self, **kwargs):
        return self._walk_relationship('child_groups', **kwargs)

    @property
    def host_names(self):
        if self._hosts is None:
            self._hosts = set(self.hosts)
        return self._hosts

    def get_name(self):
        return self.name

    def add_child_group(self, group):

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

    def _check_children_depth(self):

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

    def add_host(self, host):
        if host.name not in self.host_names:
            self.hosts.append(host)
            self._hosts.add(host.name)
            host.add_group(self)
            self.clear_hosts_cache()

    def remove_host(self, host):

        if host.name in self.host_names:
            self.hosts.remove(host)
            self._hosts.remove(host.name)
            host.remove_group(self)
            self.clear_hosts_cache()

    def set_variable(self, key, value):

        if key == 'ansible_group_priority':
            self.set_priority(int(value))
        else:
            self.vars[key] = value

    def clear_hosts_cache(self):

        self._hosts_cache = None
        for g in self.get_ancestors():
            g._hosts_cache = None

    def get_hosts(self):

        if self._hosts_cache is None:
            self._hosts_cache = self._get_hosts()
        return self._hosts_cache

    def _get_hosts(self):

        hosts = []
        seen = {}
        for kid in self.get_descendants(include_self=True, preserve_ordering=True):
            kid_hosts = kid.hosts
            for kk in kid_hosts:
                if kk not in seen:
                    seen[kk] = 1
                    if self.name == 'all' and kk.implicit:
                        continue
                    hosts.append(kk)
        return hosts

    def get_vars(self):
        return self.vars.copy()

    def set_priority(self, priority):
        try:
            self.priority = int(priority)
        except TypeError:
            # FIXME: warn about invalid priority
            pass
