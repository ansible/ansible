# (c) 2012, Jan-Piet Mens <jpmens(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: env
    author: Jan-Piet Mens (@jpmens) <jpmens(at)gmail.com>
    version_added: "0.9"
    short_description: Read the value of environment variables
    description:
      - Allows you to query the environment variables available on the
        controller when you invoked Ansible.
    options:
      _terms:
        description:
          - Environment variable or list of them to lookup the values for.
        required: True
      default:
        description: What return when the variable is undefined
        type: raw
        default: ''
        version_added: '2.13'
    notes:
        - You can pass the C(Undefined) object as O(default) to force an undefined error
"""

EXAMPLES = """
- name: Basic usage
  ansible.builtin.debug:
    msg: "'{{ lookup('ansible.builtin.env', 'HOME') }}' is the HOME environment variable."

- name: Before 2.13, how to set default value if the variable is not defined
  ansible.builtin.debug:
    msg: "Hello {{ lookup('ansible.builtin.env', 'UNDEFINED_VARIABLE') | default('World', True) }}"

- name: Example how to set default value if the variable is not defined
  ansible.builtin.debug:
    msg: "Hello {{ lookup('ansible.builtin.env', 'UNDEFINED_VARIABLE', default='World') }}"

- name: Fail if the variable is not defined by setting default value to 'Undefined'
  ansible.builtin.debug:
    msg: "Hello {{ lookup('ansible.builtin.env', 'UNDEFINED_VARIABLE', default=Undefined) }}"

- name: Fail if the variable is not defined by setting default value to 'undef()'
  ansible.builtin.debug:
    msg: "Hello {{ lookup('ansible.builtin.env', 'UNDEFINED_VARIABLE', default=undef()) }}"
"""

RETURN = """
  _list:
    description:
      - Values from the environment variables.
    type: list
"""

import os

from jinja2.runtime import Undefined

from ansible.errors import AnsibleUndefinedVariable
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)

        ret = []
        d = self.get_option('default')
        for term in terms:
            var = term.split()[0]
            val = os.environ.get(var, d)
            if isinstance(val, Undefined):
                raise AnsibleUndefinedVariable('The "env" lookup, found an undefined variable: %s' % var)
            ret.append(val)
        return ret
