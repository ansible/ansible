# (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = """
    name: bogus
    author: Ansible Core Team
    version_added: histerical
    short_description: returns what you gave it
    description:
      - this is mostly a noop
    options:
        _terms:
            description: stuff to pass through
        test_list:
            description: does nothihng, just for testing values
            type: list
            choices:
                - Dan
                - Yevgeni
                - Carla
                - Manuela
"""

EXAMPLES = """
- name: like some other plugins, this is mostly useless
  debug: msg={{ q('bogus', [1,2,3])}}
"""

RETURN = """
  _list:
    description: basically the same as you fed in
    type: list
    elements: raw
"""

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)
        dump = self.get_option('test_list')

        return terms
