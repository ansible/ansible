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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.listify import listify_lookup_plugin_terms

class LookupModule(LookupBase):

    def __lookup_variabless(self, terms, variables):
        results = []
        for x in terms:
            intermediate = listify_lookup_plugin_terms(x, variables, loader=self._loader)
            results.append(intermediate)
        return results

    def run(self, terms, variables=None, **kwargs):

        terms = self.__lookup_variabless(terms, variables)

        my_list = terms[:]
        my_list.reverse()
        result = []
        if len(my_list) == 0:
            raise AnsibleError("with_nested requires at least one element in the nested list")
        result = my_list.pop()
        while len(my_list) > 0:
            result2 = self._combine(result, my_list.pop())
            result  = result2
        new_result = []
        for x in result:
            new_result.append(self._flatten(x))
        return new_result


