# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
name: world
short_description: World lookup
description: A world lookup.
author:
  - Ansible Core Team
'''

EXAMPLES = '''
- debug:
    msg: "{{ lookup('ns.col.world') }}"
'''

RETURN = ''' # '''

from ansible.plugins.lookup import LookupBase
from ansible import constants


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)

        return terms
