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


class FactNamespace:
    def __init__(self, namespace_name):
        self.namespace_name = namespace_name

    def transform(self, name):
        '''Take a text name, and transforms it as needed (add a namespace prefix, etc)'''
        return name

    def _underscore(self, name):
        return name.replace('-', '_')


class PrefixFactNamespace(FactNamespace):
    def __init__(self, namespace_name, prefix=None):
        super(PrefixFactNamespace, self).__init__(namespace_name)
        self.prefix = prefix

    def transform(self, name):
        new_name = self._underscore(name)
        return '%s%s' % (self.prefix, new_name)
