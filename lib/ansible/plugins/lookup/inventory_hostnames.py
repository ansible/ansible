# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Steven Dossett <sdossett@panath.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: inventory_hostnames
    author:
      - Michael DeHaan <michael.dehaan@gmail.com>
      - Steven Dossett <sdossett@panath.com>
    version_added: "1.3"
    short_description: list of inventory hosts matching a host pattern
    description:
      - "This lookup understands 'host patterns' as used by the `hosts:` keyword in plays
        and can return a list of matching hosts from inventory"
    notes:
      - this is only worth for 'hostname patterns' it is easier to loop over the group/group_names variables otherwise.
"""

EXAMPLES = """
- name: show all the hosts matching the pattern, i.e. all but the group www
  debug:
    msg: "{{ item }}"
  with_inventory_hostnames:
    - all:!www
"""

RETURN = """
 _hostnames:
    description: list of hostnames that matched the host pattern in inventory
    type: list
"""

from ansible.inventory.manager import split_host_pattern, order_patterns
from ansible.plugins.lookup import LookupBase
from ansible.utils.helpers import deduplicate_list


class LookupModule(LookupBase):

    def get_hosts(self, variables, pattern):
        hosts = []
        if pattern[0] in ('!', '&'):
            obj = pattern[1:]
        else:
            obj = pattern

        if obj in variables['groups']:
            hosts = variables['groups'][obj]
        elif obj in variables['groups']['all']:
            hosts = [obj]
        return hosts

    def run(self, terms, variables=None, **kwargs):

        host_list = []

        for term in terms:
            patterns = order_patterns(split_host_pattern(term))

            for p in patterns:
                that = self.get_hosts(variables, p)
                if p.startswith("!"):
                    host_list = [h for h in host_list if h not in that]
                elif p.startswith("&"):
                    host_list = [h for h in host_list if h in that]
                else:
                    host_list.extend(that)

        # return unique list
        return deduplicate_list(host_list)
