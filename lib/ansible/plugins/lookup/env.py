# (c) 2012, Jan-Piet Mens <jpmens(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: env
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
    notes:
      - The module returns an empty string if the environment variable is not
        defined. This makes it impossbile to differentiate between the case the
        variable is not defined and the case the variable is defined but it
        contains an empty string.
      - The C(default) filter requires second parameter to be set to C(True)
        in order to set a default value in the case the variable is not
        defined (see examples).
"""

EXAMPLES = """
- name: Basic usage
  debug:
    msg: "'{{ lookup('env', 'HOME') }}' is the HOME environment variable."

- name: Example how to set default value if the variable is not defined
  debug:
    msg: "'{{ lookup('env', 'USR') | default('nobody', True) }}' is the user."
"""

RETURN = """
  _list:
    description:
      - Values from the environment variables.
    type: list
"""


from ansible.plugins.lookup import LookupBase
from ansible.utils import py3compat


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        ret = []

        for term in terms:
            var = term.split()[0]
            ret.append(py3compat.environ.get(var, ''))

        return ret
