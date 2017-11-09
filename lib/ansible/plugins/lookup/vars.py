# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: vars
    author: Ansible Core
    version_added: "2.5"
    short_description: Lookup templated value of variable
    description:
      - Retrieves the value of an Ansible variable.
    options:
      _terms:
        description: The variable name(s) to look up.
        required: True
      default:
        description:
            - What to return when the variable is undefined.
            - If no default is set, it will result in an error if the variable is undefined.
"""

EXAMPLES = """
- name: Show value of 'variablename'
  debug: msg="{{ lookup('vars', 'variabl' + myvar)}}"
  vars:
    variablename: hello
    myvar: ename

- name: Show default empty since i dont have 'variablnotename'
  debug: msg="{{ lookup('vars', 'variabl' + myvar, default='')}}"
  vars:
    variablename: hello
    myvar: notename

- name: Produce an error since i dont have 'variablnotename'
  debug: msg="{{ lookup('vars', 'variabl' + myvar)}}"
  ignore_errors: True
  vars:
    variablename: hello
    myvar: notename

- name:  find some 'prefixed vars' in loop
  debug: msg="{{ lookup('vars', 'ansible_play_' + item) }}"
  loop:
    - hosts
    - batch
    - hosts_all

- name:  pass list of vars
  debug: msg="{{ lookup('vars', 'ansible_distribution', 'ansible_pkg_mgr', 'ansible_service_mgr')}}"
"""

RETURN = """
_values:
  description:
    - list value(s) of the variable(s) requested
"""

from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.module_utils.six import string_types
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = []
        if variables is not None:
            self._templar.set_available_variables(variables)
        myvars = getattr(self._templar, '_available_variables', {})

        self.set_options(direct=kwargs)
        default = self.get_option('default')

        # Assumes listify_plugin_terms is called previous to run so each term is already templated and terms is always a list
        for term in terms:
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
                ret.append(self._templar.template(value, fail_on_undefined=True))
            except AnsibleUndefinedVariable:
                if default is not None:
                    ret.append(default)
                else:
                    raise
        return ret
