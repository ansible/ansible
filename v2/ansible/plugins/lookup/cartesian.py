# (c) 2013, Bradley Young <young.bradley@gmail.com>
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

from itertools import product

from ansible.errors import *
from ansible.plugins.lookup import LookupBase
from ansible.utils.listify import listify_lookup_plugin_terms

class LookupModule(LookupBase):
    """
    Create the cartesian product of lists
    [1, 2, 3], [a, b] -> [1, a], [1, b], [2, a], [2, b], [3, a], [3, b]
    """

    def __lookup_variabless(self, terms, variables):
        results = []
        for x in terms:
            intermediate = listify_lookup_plugin_terms(x, variables, loader=self._loader)
            results.append(intermediate)
        return results

    def run(self, terms, variables=None, **kwargs):

        terms = self.__lookup_variabless(terms, variables)

        my_list = terms[:]
        if len(my_list) == 0:
            raise errors.AnsibleError("with_cartesian requires at least one element in each list")

        return [self._flatten(x) for x in product(*my_list, fillvalue=None)]

