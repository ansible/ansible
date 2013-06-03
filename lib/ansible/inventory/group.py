# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

    __slots__ = [ 'name', 'hosts', 'vars', 'child_groups', 'parent_groups', 'depth' ]

    def __init__(self, name=None):

        self.depth = 0
        self.name = name
        self.hosts = []
        self.vars = {}
        self.child_groups = []
        self.parent_groups = []
        if self.name is None:
            raise Exception("group name is required")

    def add_child_group(self, group):

        if self == group:
            raise Exception("can't add group to itself")

        # don't add if it's already there
        if not group in self.child_groups:
            self.child_groups.append(group)
            group.depth = max([self.depth+1, group.depth])
            group.parent_groups.append(self)

    def add_host(self, host):

        self.hosts.append(host)
        host.add_group(self)

    def set_variable(self, key, value):

        self.vars[key] = value

    def get_hosts(self):

        hosts = set()
        for kid in self.child_groups:
            hosts.update(kid.get_hosts())
        hosts.update(self.hosts)
        return list(hosts)

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

