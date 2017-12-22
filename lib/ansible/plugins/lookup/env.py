# (c) 2012, Jan-Piet Mens <jpmens(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

import os
from ansible.plugins.lookup import LookupBase
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: env
    author: Jan-Piet Mens (@jpmens) <jpmens(at)gmail.com>
    version_added: "0.9"
    short_description: read the value of environment variables
    requirements:
      - none
    description:
        - Allows you to query the environment variables available on the
          controller when you invoked Ansible.
    options:
      _terms:
        description: Environment variable or list of them to lookup the values
          for. To provide a default value, add it after the variable name and a
          comma.
        required: True
"""

EXAMPLES = """
- debug: msg="{{ lookup('env','HOME') }} is an environment variable"
- debug:
    msg: "{{ lookup('env','LANG, fr_FR.UTF-8') }} is an environment variable"
"""

RETURN = """
  _list:
    description:
      - the environment variable values.
    type: list
"""


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):
        ret = []
        for term in terms:
            terms_elem = term.split(',')
            var = terms_elem[0].strip()
            default = terms_elem[1].strip() if len(terms_elem) > 1 else ''
            ret.append(os.getenv(var, default))

        return ret
