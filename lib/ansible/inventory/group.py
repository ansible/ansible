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

class Group(object):
    ''' a group of ansible hosts '''

    __slots__ = [ 'name', 'hosts', 'vars', 'child_groups', 'parent_groups', 'depth', '_hosts_cache' ]

    def __init__(self, name=None):

        self.depth = 0
        self.name = name
        self.hosts = []
        self.vars = {}
        self.child_groups = []
        self.parent_groups = []
        self._hosts_cache = None
        #self.clear_hosts_cache()
        if self.name is None:
            raise Exception("group name is required")

    def add_child_group(self, group):

        if self == group:
            raise Exception("can't add group to itself")

        # don't add if it's already there
        if not group in self.child_groups:
            self.child_groups.append(group)

            # update the depth of the child
            group.depth = max([self.depth+1, group.depth])

            # update the depth of the grandchildren
            group._check_children_depth()

            # now add self to child's parent_groups list, but only if there
            # isn't already a group with the same name
            if not self.name in [g.name for g in group.parent_groups]:
                group.parent_groups.append(self)

            self.clear_hosts_cache()

    def _check_children_depth(self):

        for group in self.child_groups:
            group.depth = max([self.depth+1, group.depth])
            group._check_children_depth()

    def add_host(self, host):

        self.hosts.append(host)
        host.add_group(self)
        self.clear_hosts_cache()

    def set_variable(self, key, value):

        self.vars[key] = value

    def clear_hosts_cache(self):

        self._hosts_cache = None
        for g in self.parent_groups:
            g.clear_hosts_cache()

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
                    hosts.append(kk)
        for mine in self.hosts:
            if mine not in seen:
                seen[mine] = 1
                hosts.append(mine)
        return hosts

    def get_variables(self):
        return self.vars.copy()

    def _get_ancestors(self):

        results = {}
        for g in self.parent_groups:
            results[g.name] = g
            results.update(g._get_ancestors())
        return results

    def get_ancestors(self):

        return self._get_ancestors().values()

