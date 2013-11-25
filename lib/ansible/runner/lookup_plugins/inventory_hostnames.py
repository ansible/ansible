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

from ansible.utils import safe_eval
import ansible.utils as utils
import ansible.errors as errors
import ansible.inventory as inventory

def flatten(terms):
    ret = []
    for term in terms:
        if isinstance(term, list):
            ret.extend(term)
        else:
            ret.append(term)
    return ret

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir
        if 'runner' in kwargs:
            self.host_list = kwargs['runner'].inventory.host_list
        else:
            raise errors.AnsibleError("inventory_hostnames must be used as a loop. Example: \"with_inventory_hostnames: \'all\'\"")

    def run(self, terms, inject=None, **kwargs):
        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject) 

        if not isinstance(terms, list):
            raise errors.AnsibleError("with_inventory_hostnames expects a list")
        return flatten(inventory.Inventory(self.host_list).list_hosts(terms))

