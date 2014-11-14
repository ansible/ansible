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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

class Host:
    def __init__(self, name):
        self._name         = name
        self._connection   = None
        self._ipv4_address = ''
        self._ipv6_address = ''
        self._port         = 22
        self._vars         = dict()

    def __repr__(self):
        return self.get_name()

    def get_name(self):
        return self._name

    def get_groups(self):
        return []

    def set_variable(self, name, value):
        ''' sets a variable for this host '''

        self._vars[name] = value

    def get_vars(self):
        ''' returns all variables for this host '''

        all_vars = self._vars.copy()
        all_vars.update(dict(inventory_hostname=self._name))
        return all_vars

