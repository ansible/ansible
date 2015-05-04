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

from ansible.errors import *
from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):

    def run(self, terms, inject=None, **kwargs):
        if not isinstance(terms, list):
            raise AnsibleError("with_inventory_hostnames expects a list")

        # FIXME: the inventory is no longer available this way, so we may have
        #        to dump the host list into the list of variables and read it back
        #        in here (or the inventory sources, so we can recreate the list
        #        of hosts)
        #return self._flatten(inventory.Inventory(self.host_list).list_hosts(terms))
        return terms

