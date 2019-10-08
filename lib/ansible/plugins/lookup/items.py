# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: items
    author: Michael DeHaan <michael.dehaan@gmail.com>
    version_added: historical
    short_description: list of items
    description:
      - this lookup returns a list of items given to it, if any of the top level items is also a list it will flatten it, but it will not recurse
    notes:
      - this is the standard lookup used for loops in most examples
      - check out the 'flattened' lookup for recursive flattening
      - if you do not want flattening nor any other transformation look at the 'list' lookup.
    options:
      _terms:
        description: list of items
        required: True
"""

EXAMPLES = """
- name: "loop through list"
  debug:
    msg: "An item: {{ item }}"
  with_items:
    - 1
    - 2
    - 3

- name: add several users
  user:
    name: "{{ item }}"
    groups: "wheel"
    state: present
  with_items:
     - testuser1
     - testuser2

- name: "loop through list from a variable"
  debug:
    msg: "An item: {{ item }}"
  with_items: "{{ somelist }}"

- name: more complex items to add several users
  user:
    name: "{{ item.name }}"
    uid: "{{ item.uid }}"
    groups: "{{ item.groups }}"
    state: present
  with_items:
     - { name: testuser1, uid: 1002, groups: "wheel, staff" }
     - { name: testuser2, uid: 1003, groups: staff }

"""

RETURN = """
  _raw:
    description:
      - once flattened list
    type: list
"""

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, **kwargs):

        return self._flatten(terms)
