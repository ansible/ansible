# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: lookup2
    author: Ansible Core Team
    short_description: hello test lookup
    description:
        - Hello test lookup.
    options: {}
"""

EXAMPLES = """
- minimal:
"""

RETURN = """
"""

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        return []
