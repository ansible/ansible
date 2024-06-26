# (c) 2013, Bradley Young <young.bradley@gmail.com>
# (c) 2012-17 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: together
    author:  Bradley Young (!UNKNOWN) <young.bradley@gmail.com>
    version_added: '1.3'
    short_description: merges lists into synchronized list
    description:
      - Creates a list with the iterated elements of the supplied lists
      - "To clarify with an example, [ 'a', 'b' ] and [ 1, 2 ] turn into [ ('a',1), ('b', 2) ]"
      - This is basically the same as the 'zip_longest' filter and Python function
      - Any 'unbalanced' elements will be substituted with 'None'
    options:
      _terms:
        description: list of lists to merge
        required: True
"""

EXAMPLES = """
- name: item.0 returns from the 'a' list, item.1 returns from the '1' list
  ansible.builtin.debug:
    msg: "{{ item.0 }} and {{ item.1 }}"
  with_together:
    - ['a', 'b', 'c', 'd']
    - [1, 2, 3, 4]
"""

RETURN = """
  _list:
    description: synchronized list
    type: list
    elements: list
"""
import itertools

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.listify import listify_lookup_plugin_terms


class LookupModule(LookupBase):
    """
    Transpose a list of arrays:
    [1, 2, 3], [4, 5, 6] -> [1, 4], [2, 5], [3, 6]
    Replace any empty spots in 2nd array with None:
    [1, 2], [3] -> [1, 3], [2, None]
    """

    def _lookup_variables(self, terms):
        results = []
        for x in terms:
            intermediate = listify_lookup_plugin_terms(x, templar=self._templar)
            results.append(intermediate)
        return results

    def run(self, terms, variables=None, **kwargs):

        terms = self._lookup_variables(terms)

        my_list = terms[:]
        if len(my_list) == 0:
            raise AnsibleError("with_together requires at least one element in each list")

        return [self._flatten(x) for x in itertools.zip_longest(*my_list, fillvalue=None)]
