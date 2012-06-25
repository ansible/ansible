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

#############################################

# from ansible import errors

class Group(object):
    """ 
    Group of ansible hosts
    """

    def __init__(self, name=None):
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
        self.child_groups.append(group)
        group.parent_groups.append(self)

    def add_host(self, host):
        self.hosts.append(host)
        host.add_group(self)

    def set_variable(self, key, value):
        self.vars[key] = value

    def get_hosts(self):
        hosts = []
        for kid in self.child_groups:
            hosts.extend(kid.get_hosts())
        hosts.extend(self.hosts)
        return hosts 

    def get_variables(self):
        vars = {}
        # FIXME: verify this variable override order is what we want
        for ancestor in self.get_ancestors():
           vars.update(ancestor.get_variables())
        vars.update(self.vars)
        return vars

    def _get_ancestors(self):
        results = {}
        for g in self.parent_groups:
            results[g.name] = g
            results.update(g._get_ancestors())
        return results

    def get_ancestors(self):
        return self._get_ancestors().values()

    def remove_host(self, host):
        if host in self.hosts:
            self.hosts.remove(host)
            host.remove_group(self)
        for kid in self.child_groups:
            if host in kid.get_hosts():
                kid.remove_host(host)

