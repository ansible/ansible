# Copyright 2017 RedHat, inc
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#############################################
'''
DOCUMENTATION:
    inventory: advanced_host_list
    version_added: "2.4"
    short_description: Parses a 'host list' with ranges
    description:
        - Parses a host list string as a comma separated values of hosts and supports host ranges.
        - This plugin only applies to inventory sources that are not paths and contain at least one comma.
EXAMPLES: |
    # simple range
    ansible -i 'host[1:10],' -m ping

    # still supports w/o ranges also
    ansible-playbook -i 'localhost,' play.yml
'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_bytes, to_native
from ansible.parsing.utils.addresses import parse_address
from ansible.plugins.inventory import BaseInventoryPlugin, detect_range, expand_hostname_range


class InventoryModule(BaseInventoryPlugin):

    NAME = 'advanced_host_list'

    def verify_file(self, host_list):

        valid = False
        b_path = to_bytes(host_list)
        if not os.path.exists(b_path) and ',' in host_list:
                valid = True
        return valid

    def parse(self, inventory, loader, host_list, cache=True):
        ''' parses the inventory file '''

        super(InventoryModule, self).parse(inventory, loader, host_list)

        try:
            for h in host_list.split(','):
                h = h.strip()
                if h:
                    try:
                        (hostnames, port) = self._expand_hostpattern(h)
                    except AnsibleError as e:
                        self.display.vvv("Unable to parse address from hostname, leaving unchanged: %s" % to_native(e))
                        host = [h]
                        port = None

                    for host in hostnames:
                        if host not in self.inventory.hosts:
                            self.inventory.add_host(host, group='ungrouped', port=port)
        except Exception as e:
            raise AnsibleParserError("Invalid data from string, could not parse: %s" % str(e))

    def _expand_hostpattern(self, hostpattern):
        '''
        Takes a single host pattern and returns a list of hostnames and an
        optional port number that applies to all of them.
        '''
        # Can the given hostpattern be parsed as a host with an optional port
        # specification?

        try:
            (pattern, port) = parse_address(hostpattern, allow_ranges=True)
        except:
            # not a recognizable host pattern
            pattern = hostpattern
            port = None

        # Once we have separated the pattern, we expand it into list of one or
        # more hostnames, depending on whether it contains any [x:y] ranges.

        if detect_range(pattern):
            hostnames = expand_hostname_range(pattern)
        else:
            hostnames = [pattern]

        return (hostnames, port)
