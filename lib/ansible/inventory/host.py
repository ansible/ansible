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

import os
import ansible.constants as C
from ansible import utils
from ansible import errors

class Host(object):
    ''' a single ansible host '''

    __slots__ = [ 'name', 'vars', 'groups', 'inventory' ]

    def __init__(self, name=None, port=None, inventory=None):

        self.name = name
        self.vars = {}
        self.groups = []
        self.inventory = inventory
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
        for group in self.groups:
            results.update(group.get_variables())
        results.update(self.vars)
        results['inventory_hostname'] = self.name
        results['inventory_hostname_short'] = self.name.split('.')[0]
        groups = self.get_groups()
        results['group_names'] = sorted([ g.name for g in groups if g.name != 'all'])
        path = os.path.join(self.inventory.basedir(), "host_vars", self.name)
        if os.path.exists(path):
            data = utils.parse_yaml_from_file(path)
            if type(data) != dict:
                raise errors.AnsibleError("%s must be stored as a dictionary/hash" % path)
            results.update(data)
        return results
