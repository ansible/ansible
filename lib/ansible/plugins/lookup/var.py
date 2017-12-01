# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: var
    author: Ansible Core
    version_added: "2.5"
    short_description: Lookup templated value of variable
    description:
      - Retrieves the value of an Ansible variable.
    options:
      _term:
        description: The variable name to look up.
        required: True
      default:
        description:
            - What to return when the variable is undefined.
            - If no default is set, it will result in an error if the variable is undefined.
"""

EXAMPLES = """
- name: Show value of 'variablename'
  debug: msg="{{ lookup('var', 'variabl' + myvar)}}"
  vars:
    variablename: hello
    myvar: ename

- name: Show default empty since i dont have 'variablnotename'
  debug: msg="{{ lookup('var', 'variabl' + myvar, default='')}}"
  vars:
    variablename: hello
    myvar: notename

- name: Produce an error since i dont have 'variablnotename'
  debug: msg="{{ lookup('var', 'variabl' + myvar)}}"
  ignore_errors: True
  vars:
    variablename: hello
    myvar: notename

- name:  find some 'prefixed vars' in loop
  debug: msg="{{ lookup('var', 'ansible_play_' + item) }}"
  loop:
    - hosts
    - batch
    - hosts_all

"""

RETURN = """
_value:
  description:
    - valueof the variable requested
"""

from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.module_utils.six import string_types
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = None
        if variables is not None:
            self._templar.set_available_variables(variables)
        myvars = getattr(self._templar, '_available_variables', {})

        self.set_options(direct=kwargs)
        default = self.get_option('default')

        # Assumes listify_plugin_terms is called previous to run so each term is already templated and terms is always a list
        if isinstance(terms, list):
            term = terms[0]
        elif isinstance(terms, string_types):
            term = terms
        else:
            raise AnsibleError('Invalid terms passed to "var" lookup, "%s" is not a string, its a %s' % (terms, type(terms)))

        if not isinstance(term, string_types):
            raise AnsibleError('Invalid setting identifier, "%s" is not a string, its a %s' % (term, type(term)))

        try:
            if term in myvars:
                value = myvars[term]
            elif 'hostvars' in myvars and term in myvars['hostvars']:
                # maybe it is a host var?
                value = myvars['hostvars'][term]
            else:
                raise AnsibleUndefinedVariable('No variable found with this name: %s' % term)
            ret = self._templar.template(value, fail_on_undefined=True)
        except AnsibleUndefinedVariable:
            if default is None:
                ret = default
            else:
                raise
        return ret
