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

from ansible.errors import AnsibleError


class Group:
    ''' a group of ansible hosts '''

    # __slots__ = [ 'name', 'hosts', 'vars', 'child_groups', 'parent_groups', 'depth', '_hosts_cache' ]

    def __init__(self, name=None):

        self.depth = 0
        self.name = name
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
                    h.populate_ancestors()

            self.clear_hosts_cache()

    def _check_children_depth(self, exclude=None):
        '''
        optimization:
        if 'exclude' set is provided, these groups will not be recursed into
        '''

        if exclude is None:
            exclude = set([])
        try:
            for group in self.child_groups:
                if group.name in exclude:
                    continue
                group.depth = max([self.depth + 1, group.depth])
                group._check_children_depth(exclude=exclude)
                exclude.add(group.name)
        except RuntimeError:
            raise AnsibleError("The group named '%s' has a recursive dependency loop." % self.name)

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

    def clear_hosts_cache(self, exclude=None):
        '''
        optimization:
        if 'exclude' set is provided, these groups will not be recursed into
        '''

        if exclude is None:
            exclude = set([])

        self._hosts_cache = None
        for g in self.parent_groups:
            if g.name in exclude:
                continue
            g.clear_hosts_cache(exclude=exclude)
            exclude.add(g.name)

    def get_hosts(self):

        if self._hosts_cache is None:
            self._hosts_cache = self._get_hosts()
        return self._hosts_cache

    def _get_hosts(self):

        hosts = []
        seen = {}
        for kid in self.child_groups:
            kid_hosts = kid.get_hosts()
            for kk in kid_hosts:
                if kk not in seen:
                    seen[kk] = 1
                    if self.name == 'all' and kk.implicit:
                        continue
                    hosts.append(kk)
        for mine in self.hosts:
            if mine not in seen:
                seen[mine] = 1
                if self.name == 'all' and mine.implicit:
                    continue
                hosts.append(mine)
        return hosts

    def get_vars(self):
        return self.vars.copy()

    def _get_ancestors(self, results=None):
        '''
        optimization:
        if `results` kwarg is supplied, this method adds its parentage
        onto a running dictionary of parents of a lower depth group
        '''

        if results is None:
            results = {}
        for g in self.parent_groups:
            if g.name not in results:
                results[g.name] = g
                results = g._get_ancestors(results=results)
        return results

    def get_ancestors(self):

        return self._get_ancestors().values()

    def set_priority(self, priority):
        try:
            self.priority = int(priority)
        except TypeError:
            # FIXME: warn about invalid priority
            pass
