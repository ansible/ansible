# (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
    name: types
    author: Ansible Core Team
    version_added: histerical
    short_description: returns what you gave it
    description:
      - this is mostly a noop
    options:
        _terms:
            description: stuff to pass through
        valid:
            description: does nothihng, just for testing values
            type: list
            ini:
                - section: list_values
                  key: valid
            env:
                - name: ANSIBLE_TYPES_VALID
            vars:
                - name: ansible_types_valid
        mustunquote:
            description: does nothihng, just for testing values
            type: list
            ini:
                - section: list_values
                  key: mustunquote
            env:
                - name: ANSIBLE_TYPES_MUSTUNQUOTE
            vars:
                - name: ansible_types_mustunquote
        notvalid:
            description: does nothihng, just for testing values
            type: list
            ini:
                - section: list_values
                  key: notvalid
            env:
                - name: ANSIBLE_TYPES_NOTVALID
            vars:
                - name: ansible_types_notvalid
        totallynotvalid:
            description: does nothihng, just for testing values
            type: list
            ini:
                - section: list_values
                  key: totallynotvalid
            env:
                - name: ANSIBLE_TYPES_TOTALLYNOTVALID
            vars:
                - name: ansible_types_totallynotvalid
        str_mustunquote:
            description: does nothihng, just for testing values
            type: string
            ini:
                - section: string_values
                  key: str_mustunquote
            env:
                - name: ANSIBLE_TYPES_STR_MUSTUNQUOTE
            vars:
                - name: ansible_types_str_mustunquote
"""

EXAMPLES = """
- name: like some other plugins, this is mostly useless
  debug: msg={{ q('types', [1,2,3])}}
"""

RETURN = """
  _list:
    description: basically the same as you fed in
    type: list
    elements: raw
"""

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)

        return terms
