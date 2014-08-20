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

import ansible.constants as C
from ansible import utils

class Host(object):
    ''' a single ansible host '''

    __slots__ = [ 'name', 'vars', 'groups' ]

    def __init__(self, name=None, port=None):

        self.name = name
        self.vars = {}
        self.groups = []
        if port and port != C.DEFAULT_REMOTE_PORT:
            self.set_variable('ansible_ssh_port', int(port))

        if self.name is None:
            raise Exception("host name is required")

    def add_group(self, group):

        self.groups.append(group)

    def set_variable(self, key, value):

        self.vars[key]=value

    def get_groups(self):

        groups = {}
        for g in self.groups:
            groups[g.name] = g
            ancestors = g.get_ancestors()
            for a in ancestors:
                groups[a.name] = a
        return groups.values()

    def get_variables(self):

        results = {}
        groups = self.get_groups()
        for group in sorted(groups, key=lambda g: g.depth):
            results = utils.combine_vars(results, group.get_variables())
        results = utils.combine_vars(results, self.vars)
        results['inventory_hostname'] = self.name
        results['inventory_hostname_short'] = self.name.split('.')[0]
        results['group_names'] = sorted([ g.name for g in groups if g.name != 'all'])
        return results


