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
          keys to the previous dictionary's structure. The new keys 'key' and 'value' can be overridden using the optional parameters key_name and value_name.
    options:
        _terms:
            description:
                - A list of dictionaries
            required: True
        value_name:
            description:
                - Use it to override the 'key' key name in the dictionaries. By default it will be set to 'value'.
            required: False
            default: 'value'
        key_name:
            description:
                - Use it to override the 'key' key name in the dictionaries. By default it will be set to 'key'.
            required: False
            default: 'key'
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
  # Set key_name and value_name example
  - name: set_fact when alice in key
    ansible.builtin.set_fact:
      alice_exists: true
    loop: "{{ lookup('ansible.builtin.dict', users, key_name='user', value_name='user_data') }}"
    when: "'alice' in item.key"
"""

RETURN = """
  _list:
    description:
      - list of composed dictonaries with key and value
    type: list
"""

from collections.abc import Mapping

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)
        value_name = self.get_option('value_name')
        key_name = self.get_option('key_name')

        # NOTE: can remove if with_ is removed
        if not isinstance(terms, list):
            terms = [terms]

        results = []
        for term in terms:
            # Expect any type of Mapping, notably hostvars
            if not isinstance(term, Mapping):
                raise AnsibleError("with_dict expects a dict")

            results.extend(self._flatten_hash_to_list(term, key_name=key_name, value_name=value_name))
        return results
