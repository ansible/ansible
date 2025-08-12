# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: varnames
    author: Ansible Core Team
    version_added: "2.8"
    short_description: Lookup matching variable names
    description:
      - Retrieves a list of matching Ansible variable names.
    options:
      _terms:
        description: List of Python regex patterns to search for in variable names.
        required: True
    seealso:
        - plugin_type: lookup
          plugin: ansible.builtin.vars
"""

EXAMPLES = """
- name: List variables that start with qz_
  ansible.builtin.debug: msg="{{ lookup('ansible.builtin.varnames', '^qz_.+') }}"
  vars:
    qz_1: hello
    qz_2: world
    qa_1: "I won't show"
    qz_: "I won't show either"

- name: Show all variables
  ansible.builtin.debug: msg="{{ lookup('ansible.builtin.varnames', '.+') }}"

- name: Show variables with 'hosts' in their names
  ansible.builtin.debug: msg="{{ q('varnames', 'hosts') }}"

- name: Find several related variables that end specific way
  ansible.builtin.debug: msg="{{ query('ansible.builtin.varnames', '.+_zone$', '.+_location$') }}"

- name: display values from variables found via varnames (note "*" is used to dereference the list to a 'list of arguments')
  debug: msg="{{ lookup('vars', *lookup('varnames', 'ansible_play_.+')) }}"

"""

RETURN = """
_value:
  description:
    - List of the variable names requested.
  type: list
"""

import re

from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        if variables is None:
            raise AnsibleError('No variables available to search')

        self.set_options(var_options=variables, direct=kwargs)

        ret = []
        variable_names = list(variables.keys())
        for term in terms:

            if not isinstance(term, str):
                raise AnsibleError('Invalid setting identifier, "%s" is not a string, it is a %s' % (term, type(term)))

            try:
                name = re.compile(term)
            except Exception as e:
                raise AnsibleError('Unable to use "%s" as a search parameter: %s' % (term, to_native(e)))

            for varname in variable_names:
                if name.search(varname):
                    ret.append(varname)

        return ret
