# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

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
    seealso:
    - plugin_type: lookup
      plugin: ansible.builtin.varnames

"""

EXAMPLES = """
- name: Show value of 'variablename'
  ansible.builtin.debug: msg="{{ lookup('ansible.builtin.vars', 'variabl' + myvar) }}"
  vars:
    variablename: hello
    myvar: ename

- name: Show default empty since i dont have 'variablnotename'
  ansible.builtin.debug: msg="{{ lookup('ansible.builtin.vars', 'variabl' + myvar, default='') }}"
  vars:
    variablename: hello
    myvar: notename

- name: Produce an error since i dont have 'variablnotename'
  ansible.builtin.debug: msg="{{ q('vars', 'variabl' + myvar) }}"
  ignore_errors: True
  vars:
    variablename: hello
    myvar: notename

- name: find several related variables
  ansible.builtin.debug: msg="{{ query('ansible.builtin.vars', 'ansible_play_hosts', 'ansible_play_batch', 'ansible_play_hosts_all') }}"

- name: show values from variables found via varnames (note "*" is used to dereference the list to a 'list of arguments')
  debug: msg="{{ q('vars', *q('varnames', 'ansible_play_.+')) }}"

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

from ansible.errors import AnsibleTypeError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.datatag import native_type_name
from ansible._internal._templating import _jinja_bits


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)

        default = self.get_option('default')

        ret = []

        for term in terms:
            if not isinstance(term, str):
                raise AnsibleTypeError(f'Variable name must be {native_type_name(str)!r} not {native_type_name(term)!r}.', obj=term)

            try:
                value = variables[term]
            except KeyError:
                if default is None:
                    value = _jinja_bits._undef(f'No variable named {term!r} was found.')
                else:
                    value = default

            ret.append(value)

        return self._templar._engine.template(ret)
