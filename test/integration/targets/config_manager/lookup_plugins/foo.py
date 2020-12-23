from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
lookup: foo
author: Felix Fontein
short_description: Test lookup
description:
  - Nothing.
options:
  deprecated_option:
    description: Deprecated
    type: str
    deprecated:
      why: this option should not be used
      version: 10.0.0
      alternatives: no option instead
'''

RETURN = """
  _raw:
    description:
      - The input list.
    type: list
    elements: str
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)

        return terms
