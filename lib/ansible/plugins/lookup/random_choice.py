# (c) 2013, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: random_choice
    author: Michael DeHaan
    version_added: "1.1"
    short_description: return random element from list
    description:
      - The 'random_choice' feature can be used to pick something at random. While it's not a load balancer (there are modules for those),
        it can somewhat be used as a poor man's load balancer in a MacGyver like situation.
      - At a more basic level, they can be used to add chaos and excitement to otherwise predictable automation environments.
"""

EXAMPLES = """
- name: Magic 8 ball for MUDs
  debug:
    msg: "{{ item }}"
  with_random_choice:
     - "go through the door"
     - "drink from the goblet"
     - "press the red button"
     - "do nothing"
"""

RETURN = """
  _raw:
    description:
      - random item
    type: raw
"""
import random

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, inject=None, **kwargs):

        ret = terms
        if terms:
            try:
                ret = [random.choice(terms)]
            except Exception as e:
                raise AnsibleError("Unable to choose random term: %s" % to_native(e))

        return ret
