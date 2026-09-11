# (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
  name: tags
  author: Ansible Core Team
  version_added: "2.22"
  short_description: show a value's data tags
  description:
    - Show a list of any Tags associaated with the input value
  positional: _input
  options:
    _input:
      description: Value for which tag information is requested
      required: true
  notes:
    - Not all values have tags, so an empty list is possible, but most should have at least an `Origin` tag.
"""
EXAMPLES = r"""
  - name: show the tags of the value in testvar
    debug: msg="{{ lookup('tags', testvar)}}"

  - name: show the tags of the first value in a list in a dictionary
    debug: msg="{{ query('tags', testdict['somekey'][0]) }}"

  - name: show the tags for the list in the variable testlist
    debug: msg="{{ q('tags', testlist) }}"

  - name: show the tags for first 3 values in a list
    debug: msg="{{ q('tags', *testlist[0:2]) }}"
"""
RETURN = r"""
  _tags:
    description: A list of strings representing the tags associated with the value supplied
    type: list
    elements: string
"""

from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None):
        ret = []
        for term in terms:
            ret.append(sorted(tag_type.__name__ for tag_type in AnsibleTagHelper.tag_types(term)))
        return ret
