# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.plugins.lookup import LookupBase

DOCUMENTATION = """
name: import_order_lookup
short_description: Import order lookup
description: Import order lookup.
"""


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        return []
