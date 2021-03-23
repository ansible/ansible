# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = """
    lookup: noop
    author: Ansible core team
    short_description: returns input
    description:
      - this is a noop
    deprecated:
        alternative: Use some other lookup
        why: Test deprecation
        removed_in: '3.0.0'
    extends_documentation_fragment:
        - testns.testcol2.version_added
"""

EXAMPLES = """
- name: do nothing
  debug: msg="{{ lookup('testns.testcol.noop', [1,2,3,4] }}"
"""

RETURN = """
  _list:
    description: input given
    version_added: 1.0.0
"""

from ansible.module_utils.common._collections_compat import Sequence
from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError


class LookupModule(LookupBase):

    def run(self, terms, **kwargs):
        if not isinstance(terms, Sequence):
            raise AnsibleError("testns.testcol.noop expects a list")
        return terms
