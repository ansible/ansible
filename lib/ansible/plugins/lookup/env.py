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


from ansible.plugins.lookup import LookupBase
from ansible._internal._templating._jinja_bits import _undef, _DEFAULT_UNDEF
from ansible._internal._datatag._tags import Origin


class LookupModule(LookupBase):
    accept_args_markers = True  # the `default` arg can accept undefined values

    def run(self, terms, variables=None, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)

        ret = []
        d = self.get_option('default')

        for term in terms:
            var = term.split()[0]
            val = os.environ.get(var, d)

            if val is _DEFAULT_UNDEF:
                val = _undef(f'The environment variable {var!r} is not set.')
            else:
                val = Origin(description=f"<environment variable {var!r}>").try_tag(val)

            ret.append(val)

        return ret
