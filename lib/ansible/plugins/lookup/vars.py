# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: vars
    author: Ansible Core Team
    version_added: "2.5"
    short_description: Lookup templated value of variables
    description:
      - 'Retrieves the value of an Ansible variable. Note: Only returns top level variable names.'
    options:
      _terms:
        description: The variable names to look up.
        required: True
      default:
        description:
            - What to return if a variable is undefined.
            - If no default is set, it will result in an error if any of the variables is undefined.
"""

EXAMPLES = """
- name: Show value of 'variablename'
  ansible.builtin.debug: msg="{{ lookup('ansible.builtin.vars', 'variabl' + myvar) }}"
  vars:
    variablename: hello
    myvar: ename

- name: Show default empty since i dont have 'variablnotename'
  ansible.builtin.debug: msg="{{ lookup('ansible.builtin.vars', 'variabl' + myvar, default='')}}"
  vars:
    variablename: hello
    myvar: notename

- name: Produce an error since i dont have 'variablnotename'
  ansible.builtin.debug: msg="{{ lookup('ansible.builtin.vars', 'variabl' + myvar)}}"
  ignore_errors: True
  vars:
    variablename: hello
    myvar: notename

- name: find several related variables
  ansible.builtin.debug: msg="{{ lookup('ansible.builtin.vars', 'ansible_play_hosts', 'ansible_play_batch', 'ansible_play_hosts_all') }}"

- name: Access nested variables
  ansible.builtin.debug: msg="{{ lookup('ansible.builtin.vars', 'variabl' + myvar).sub_var }}"
  ignore_errors: True
  vars:
    variablename:
        sub_var: 12
    myvar: ename

- name: alternate way to find some 'prefixed vars' in loop
  ansible.builtin.debug: msg="{{ lookup('ansible.builtin.vars', 'ansible_play_' + item) }}"
  loop:
    - hosts
    - batch
    - hosts_all
"""

RETURN = """
_value:
  description:
    - value of the variables requested.
  type: list
  elements: raw
"""

from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.module_utils.six import string_types
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        if variables is not None:
            self._templar.available_variables = variables
        myvars = getattr(self._templar, '_available_variables', {})

        self.set_options(var_options=variables, direct=kwargs)
        default = self.get_option('default')

        ret = []
        for term in terms:
            if not isinstance(term, string_types):
                raise AnsibleError('Invalid setting identifier, "%s" is not a string, its a %s' % (term, type(term)))

            try:
                try:
                    value = myvars[term]
                except KeyError:
                    try:
                        value = myvars['hostvars'][myvars['inventory_hostname']][term]
                    except KeyError:
                        raise AnsibleUndefinedVariable('No variable found with this name: %s' % term)

                ret.append(self._templar.template(value, fail_on_undefined=True))
            except AnsibleUndefinedVariable:
                if default is not None:
                    ret.append(default)
                else:
                    raise

        return ret
