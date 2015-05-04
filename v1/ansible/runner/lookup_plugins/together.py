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

import ansible.utils as utils
from ansible.utils import safe_eval
import ansible.errors as errors
from itertools import izip_longest

def flatten(terms):
    ret = []
    for term in terms:
        if isinstance(term, list):
            ret.extend(term)
        elif isinstance(term, tuple):
            ret.extend(term)
        else:
            ret.append(term)
    return ret

class LookupModule(object):
    """
    Transpose a list of arrays:
    [1, 2, 3], [4, 5, 6] -> [1, 4], [2, 5], [3, 6]
    Replace any empty spots in 2nd array with None:
    [1, 2], [3] -> [1, 3], [2, None]
    """

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def __lookup_injects(self, terms, inject):
        results = []
        for x in terms:
            intermediate = utils.listify_lookup_plugin_terms(x, self.basedir, inject)
            results.append(intermediate)
        return results

    def run(self, terms, inject=None, **kwargs):

        # this code is common with 'items.py' consider moving to utils if we need it again

        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)
        terms = self.__lookup_injects(terms, inject)

        my_list = terms[:]
        if len(my_list) == 0:
            raise errors.AnsibleError("with_together requires at least one element in each list")
        return [flatten(x) for x in izip_longest(*my_list, fillvalue=None)]


