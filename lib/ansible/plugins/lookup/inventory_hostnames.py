# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Steven Dossett <sdossett@panath.com>
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

from ansible.plugins.lookup import LookupBase
from ansible.inventory import Inventory

class LookupModule(LookupBase):

    def get_hosts(self, variables, pattern):
        hosts = []
        if pattern[0] in ('!','&'):
            obj = pattern[1:]
        else:
            obj = pattern

        if obj in variables['groups']:
            hosts = variables['groups'][obj]
        elif obj in variables['groups']['all']:
            hosts = [obj]
        return hosts

    def run(self, terms, variables=None, **kwargs):

        host_list = []

        for term in terms:
            patterns = Inventory.order_patterns(Inventory.split_host_pattern(term))

            for p in patterns:
                that = self.get_hosts(variables, p)
                if p.startswith("!"):
                    host_list = [ h for h in host_list if h not in that]
                elif p.startswith("&"):
                    host_list = [ h for h in host_list if h in that ]
                else:
                    host_list.extend(that)

        # return unique list
        return list(set(host_list))
