# (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
    name: casting_individual
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
        test_int:
            description: does nothihng, just to test casting
            type: int
        test_bool:
            description: does nothihng, just to test casting
            type: bool
        test_str:
            description: does nothihng, just to test casting
            type: str
"""

EXAMPLES = """
- name: like some other plugins, this is mostly useless
  debug: msg={{ q('casting_individual', [1,2,3])}}
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

        for cast in (list, int, bool, str):
            option = 'test_%s' % str(cast).replace("<class '", '').replace("'>", '')
            if option in kwargs:
                self.set_option(option, kwargs[option])
                value = self.get_option(option)
                if type(value) is not cast:
                    raise Exception('%s is not a %s: got %s/%s' % (option, cast, type(value), value))

        return terms
