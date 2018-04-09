# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: indexed_items
    author: Michael DeHaan <michael.dehaan@gmail.com>
    version_added: "1.3"
    short_description: rewrites lists to return 'indexed items'
    description:
      - use this lookup if you want to loop over an array and also get the numeric index of where you are in the array as you go
      - any list given will be transformed with each resulting element having the it's previous position in item.0 and its value in item.1
    options:
      _terms:
        description: list of items
        required: True
"""

EXAMPLES = """
- name: indexed loop demo
  debug:
    msg: "at array position {{ item.0 }} there is a value {{ item.1 }}"
  with_indexed_items:
    - "{{ some_list }}"
"""

RETURN = """
  _raw:
    description:
      - list with each item.0 giving you the postiion and item.1 the value
    type: list
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, variables, **kwargs):

        if not isinstance(terms, list):
            raise AnsibleError("with_indexed_items expects a list")

        items = self._flatten(terms)
        return list(zip(range(len(items)), items))
