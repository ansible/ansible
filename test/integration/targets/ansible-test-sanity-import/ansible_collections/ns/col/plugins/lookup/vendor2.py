# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
name: vendor2
short_description: lookup
description: Lookup.
author:
  - Ansible Core Team
"""

EXAMPLES = """#"""
RETURN = """#"""

from ansible.plugins.lookup import LookupBase
# noinspection PyUnresolvedReferences
from ansible.plugins import loader  # import the loader to verify it works when the collection loader has already been loaded  # pylint: disable=unused-import

try:
    import demo  # pylint: disable=unused-import
except ImportError:
    pass
else:
    raise Exception('demo import found when it should not be')


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)

        return terms
