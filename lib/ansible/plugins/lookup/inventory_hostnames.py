# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Steven Dossett <sdossett@panath.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: inventory_hostnames
    author:
      - Michael DeHaan
      - Steven Dossett (!UNKNOWN) <sdossett@panath.com>
    version_added: "1.3"
    short_description: list of inventory hosts matching a host pattern
    description:
      - "This lookup understands 'host patterns' as used by the C(hosts:) keyword in plays
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

from ansible.errors import AnsibleError
from ansible.inventory.manager import InventoryManager
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        manager = InventoryManager(self._loader, parse=False)
        for group, hosts in variables['groups'].items():
            manager.add_group(group)
            for host in hosts:
                manager.add_host(host, group=group)

        try:
            return [h.name for h in manager.get_hosts(pattern=terms)]
        except AnsibleError:
            return []
