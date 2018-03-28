# (c) 2013, Serge van Ginderachter <serge@vanginderachter.be>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: flattened
    author: Serge van Ginderachter <serge@vanginderachter.be>
    version_added: "1.3"
    short_description: return single list completely flattened
    description:
      - given one or more lists, this lookup will flatten any list elements found recursively until only 1 list is left.
    options:
      _terms:
        description: lists to flatten
        required: True
    notes:
      - unlike 'items' which only flattens 1 level, this plugin will continue to flatten until it cannot find lists anymore.
      - aka highlander plugin, there can only be one (list).
"""

EXAMPLES = """
- name: "'unnest' all elements into single list"
  debug: msg="all in one list {{lookup('flattened', [1,2,3,[5,6]], [a,b,c], [[5,6,1,3], [34,a,b,c]])}}"
"""

RETURN = """
  _raw:
    description:
      - flattened list
    type: list
"""
from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types
from ansible.plugins.lookup import LookupBase
from ansible.utils.listify import listify_lookup_plugin_terms


class LookupModule(LookupBase):

    def _check_list_of_one_list(self, term):
        # make sure term is not a list of one (list of one..) item
        # return the final non list item if so

        if isinstance(term, list) and len(term) == 1:
            term = term[0]
            if isinstance(term, list):
                term = self._check_list_of_one_list(term)

        return term

    def _do_flatten(self, terms, variables):

        ret = []
        for term in terms:
            term = self._check_list_of_one_list(term)

            if term == 'None' or term == 'null':
                # ignore undefined items
                break

            if isinstance(term, string_types):
                # convert a variable to a list
                term2 = listify_lookup_plugin_terms(term, templar=self._templar, loader=self._loader)
                # but avoid converting a plain string to a list of one string
                if term2 != [term]:
                    term = term2

            if isinstance(term, list):
                # if it's a list, check recursively for items that are a list
                term = self._do_flatten(term, variables)
                ret.extend(term)
            else:
                ret.append(term)

        return ret

    def run(self, terms, variables, **kwargs):

        if not isinstance(terms, list):
            raise AnsibleError("with_flattened expects a list")

        return self._do_flatten(terms, variables)
