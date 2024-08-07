# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
    name: cidr
    version_added: "2.18"
    short_description: Parses CIDR expressions to generate inventory
    description:
        - Parses a host list string as a comma separated values of CIDR notations to generate an IP range of hosts
    notes:
        - To ensure addresses are parsed as CIDR, make sure this plugin is before
          host_list and advance_host_list in enabled inventory plugins.
        - This is not meant to handle big ranges, specially with IPV6. Generating
          the range is quick but adding all those hosts to inventory can take a
          long time.
'''

EXAMPLES = '''
    # simple range
    # ansible -i '@CIDR, 192.168.0.1/24,' -m ping

    # still supports w/o ranges also
    # ansible-playbook -i '@CIDR, 192.168.0.1, 192.168.0.23,' myplay.yml
'''

import os
import ipaddress

from ansible.errors import AnsibleParserError
from ansible.module_utils.common.text.converters import to_bytes
from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):

    NAME = 'cidr'

    def verify_file(self, path):

        valid = False
        b_path = to_bytes(path, errors='surrogate_or_strict')
        if not os.path.exists(b_path) and ',' in path and path.startswith('@CIDR,'):
            valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):
        ''' parses the inventory string'''

        super(InventoryModule, self).parse(inventory, loader, path)

        # not really a path at this point
        host_list = path

        for h in host_list.split(','):
            if h == '@CIDR':
                # skip marker
                continue

            h = h.strip()
            if h:
                try:
                    hostnames = ipaddress.ip_network(h, False)
                except ValueError as e:
                    raise AnsibleParserError(f"Unable to parse address from '{h}'") from e

                for ip in hostnames.hosts():
                    host = ip.exploded
                    self.inventory.add_host(host, group='ungrouped')
