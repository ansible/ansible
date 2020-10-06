# (c) 2014, Kent R. Spillner <kspillner@acm.org>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: dict
    version_added: "1.5"
    short_description: returns key/value pair items from dictionaries
    description:
        - Takes dictionaries as input and returns a list with each item in the list being a dictionary with 'key' and 'value' as
          keys to the previous dictionary's structure.
    options:
        _terms:
            description:
                - A list of dictionaries
            required: True
"""

EXAMPLES = """
vars:
  users:
    alice:
      name: Alice Appleworth
      telephone: 123-456-7890
    bob:
      name: Bob Bananarama
      telephone: 987-654-3210
tasks:
  # with predefined vars
  - name: Print phone records
    debug:
      msg: "User {{ item.key }} is {{ item.value.name }} ({{ item.value.telephone }})"
    loop: "{{ lookup('dict', users) }}"
  # with inline dictionary
  - name: show dictionary
    debug:
      msg: "{{item.key}}: {{item.value}}"
    with_dict: {a: 1, b: 2, c: 3}
  # Items from loop can be used in when: statements
  - name: set_fact when alice in key
    set_fact:
      alice_exists: true
    loop: "{{ lookup('dict', users) }}"
    when: "'alice' in item.key"
"""

RETURN = """
  _list:
    description:
      - list of composed dictonaries with key and value
    type: list
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.common._collections_compat import Mapping


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        # FIXME: can remove once with_ special case is removed
        if not isinstance(terms, list):
            terms = [terms]

        results = []
        for term in terms:
            # Expect any type of Mapping, notably hostvars
            if not isinstance(term, Mapping):
                raise AnsibleError("with_dict expects a dict")

            results.extend(self._flatten_hash_to_list(term))
        return results
