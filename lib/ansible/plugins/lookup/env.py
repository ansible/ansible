# (c) 2012, Jan-Piet Mens <jpmens(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: env
    author: Jan-Piet Mens (@jpmens) <jpmens(at)gmail.com>
    version_added: "0.9"
    short_description: read the value of environment variables
    description:
      - Allows you to query the environment variables available on the
        controller when you invoked Ansible.
    options:
      _terms:
        description:
          - Environment variable or list of them to lookup the values for.
        required: True
      default:
        description:
          - Default value when the environment variable is not defined.
        type: string
        default: ""
        required: False
"""

EXAMPLES = """
- debug:
    msg: "'{{ lookup('env','HOME') }}' is the HOME environment variable."
- debug:
    msg: "'{{ lookup('env','USERNAME', 'nobody') }}' is the user name."
"""

RETURN = """
  _list:
    description:
      - Values from the environment variables.
    type: list
"""


import os

from ansible.plugins.lookup import LookupBase
from ansible.utils import py3compat


class LookupModule(LookupBase):
    def run(self, terms, variables=None, default=''):
        ret = []

        for term in terms:
            var = term.split()[0]
            ret.append(py3compat.environ.get(var, default))

        return ret
