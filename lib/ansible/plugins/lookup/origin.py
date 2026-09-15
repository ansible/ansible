# (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
  name: origin
  author: Ansible Core Team
  version_added: "2.22"
  short_description: show value's origin
  description:
    - Show the origin of the current value(s)
  options:
    _terms:
      description: Value(s) to show the origin for.
      required: true
"""
EXAMPLES = r"""
  - name: show the origin of value of testvar
    debug: msg="{{ q('origin', testvar) }}"

  - name: show the origin of the 2nd value in a list in a dictionary
    debug: msg="{{ lookup('origin', testdict['somekey'][1]) }}"

  - name: show the origin for the values in a list
    debug: msg="{{ query('origin', *testlist) }}"

  - name: show the origin for the the list in the variable
    debug: msg="{{ q('origin', testlist) }}"
"""
RETURN = r"""
  _origin:
    description: A string representing the origin of the value supplied or `None` if no origin data is available
    type: string
"""

from ansible._internal._datatag._tags import Origin
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None):
        ret = []
        for term in terms:
            origin_tag = Origin.get_tag(term)
            ret.append(str(origin_tag) if origin_tag else None)
        return ret
