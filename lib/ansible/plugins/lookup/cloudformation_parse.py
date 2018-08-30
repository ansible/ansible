# (c) 2018, Steven Miller
# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: cloudformation_parse
    author: Steven Miller (@sjmiller609)
    version_added: "2.6"
    short_description: Parse cloudformation files
    description:
        - Allows users to parse json or yaml cloudformation files into a list of json objects
    options:
      _terms:
        description: File name or list of filenames for the cloudformation template(s) to load
        required: True
"""

EXAMPLES = """
- debug: msg="{{ lookup('cloudformation_parse','myfile.yml') }}"
"""

RETURN = """
  _list:
    description:
      - The parsed cloudformation file(s)
    type: list
"""

# This module allows us to parse cfn including special tags
# The module is supported by awslabs
# see 'load' function here
# https://github.com/awslabs/aws-cfn-template-flip/blob/master/cfn_flip/__init__.py
from cfn_flip import load as cfn_load

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        ret = []
        for term in terms:
            var = term.split()[0]
            with open(var, "r") as f:
                data = f.read()
            parsed = cfn_load(data)[0]
            ret.append(parsed)

        return ret
