# (c) 2018, Steven Miller
# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: cloudformation_parse
    author: Steven Miller (@sjmiller609)
    version_added: "2.8"
    short_description: Parse CloudFormation files
    description:
        - Allows users to parse json or yaml CloudFormation files into a list of json objects
    requirements:
        - 'cfn-flip python library U(https://github.com/awslabs/aws-cfn-template-flip)'
    options:
      _terms:
        description: File name or list of filenames for the CloudFormation template(s) to load
        required: True
"""

EXAMPLES = """
- debug: msg="{{ lookup('cloudformation_parse','myfile.yml') }}"
"""

RETURN = """
  _list:
    description:
      - The parsed CloudFormation file(s)
    type: list
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

# This module allows us to parse cfn including special tags
# The module is supported by awslabs
# see 'load' function here
# https://github.com/awslabs/aws-cfn-template-flip/blob/master/cfn_flip/__init__.py
try:
    from cfn_flip import load as cfn_load
    HAS_CFN_FLIP = True
except ImportError:
    HAS_CFN_FLIP = False

class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        if not HAS_CFN_FLIP:
            raise AnsibleError(
                'cfn-flip is required for cloudformation_parse lookup. see https://github.com/awslabs/aws-cfn-template-flip')

        ret = []
        for term in terms:
            var = term.split()[0]
            with open(var, "r") as f:
                data = f.read()
            parsed = cfn_load(data)[0]
            ret.append(parsed)

        return ret
