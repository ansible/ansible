# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
name: deprecated
short_description: lookup
description: Lookup.
author:
  - Ansible Core Team
'''

EXAMPLES = '''#'''
RETURN = '''#'''

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, **kwargs):
        return []
