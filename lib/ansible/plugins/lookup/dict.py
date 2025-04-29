# (c) 2014, Kent R. Spillner <kspillner@acm.org>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

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
    ansible.builtin.debug:
      msg: "User {{ item.key }} is {{ item.value.name }} ({{ item.value.telephone }})"
    loop: "{{ lookup('ansible.builtin.dict', users) }}"
  # with inline dictionary
  - name: show dictionary
    ansible.builtin.debug:
      msg: "{{item.key}}: {{item.value}}"
    with_dict: {a: 1, b: 2, c: 3}
  # Items from loop can be used in when: statements
  - name: set_fact when alice in key
    ansible.builtin.set_fact:
      alice_exists: true
    loop: "{{ lookup('ansible.builtin.dict', users) }}"
    when: "'alice' in item.key"
"""

RETURN = """
  _list:
    description:
      - list of composed dictionaries with key and value
    type: list
"""

from collections.abc import Mapping

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        results = []
        for term in terms:
            # Expect any type of Mapping, notably hostvars
            if not isinstance(term, Mapping):
                raise AnsibleError(f"the 'dict' lookup plugin expects a dictionary, got '{term}' of type {type(term)})")

            results.extend(self._flatten_hash_to_list(term))
        return results
