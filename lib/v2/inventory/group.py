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
    def __init__(self, name, hosts=[]):
        self.name     = name
        self.hosts    = hosts
        self.parents  = []
        self.children = []

    def get_vars(self):
        return dict()

    def get_hosts(self):
        return self.hosts

    def get_direct_subgroups(self):
        direct_children = []
        for child in self.children:
            direct_children.append(child.name)
        return direct_children

    def get_all_subgroups(self):
        all_children = []
        for child in self.children:
            all_children.extend(child.get_all_subgroups())
        return all_children

    def get_parent_groups(self):
        return self.parents
