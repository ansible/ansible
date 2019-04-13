#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# (c) 2019, Brian Clemens <brian@tiuxo.com>
#
# This file is part of Ansible.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

######################################################################
"""
ZeroTier external inventory script
==================================

Generates Ansible inventory from a ZeroTier network.  This script takes configuration from a file named zerotier.ini or the following environmental variables:
    ZT_CONTROLLER - String, URL to the ZeroTier controller
    ZT_NETWORK - String, ZeroTier network ID
    ZT_TOKEN - String, ZeroTier authentication token
    ZT_INCLUDEOFFLINE - Boolean, include offline hosts in generated inventory

usage: zerotier.py [--list]
"""

# Standard imports
import os
import sys
import argparse

import json
import requests

# Imports from Ansible
from ansible.module_utils.six.moves import configparser as ConfigParser


class ZeroTierInventory(object):
    def __init__(self):
        """ Main execution path """
        self.inventory = self._empty_inventory()

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        # Get host information and populate inventory
        self.get_hosts()

        if self.args.list:
            data_to_print = self.json_format_dict(self.inventory, True)

        print(data_to_print)

    def add_host(self, host):
        """Adds a host to the inventory"""
        dest = host['name']

        # Inventory: Group by network
        self.push(self.inventory, host['networkId'], dest)

        # Inventory: Add a "zerotier" global tag group
        self.push(self.inventory, "zerotier", dest)

        # Add host info to hostvars
        self.inventory['_meta']['hostvars'][dest] = self._get_host_info(host)

    def _empty_inventory(self):
        return {"_meta": {"hostvars": {}}}

    def _get_host_info(self, host):
        host_vars = {}
        for attr in [
                'description',
                'physicalAddress',
                'physicalLocation',
        ]:
            host_vars[attr] = host[attr]

        host_vars['zerotier_authorized'] = host['config']['authorized']
        host_vars['zerotier_bridge'] = host['config']['activeBridge']
        host_vars['zerotier_id'] = host['nodeId']
        host_vars['zerotier_ips'] = host['config']['ipAssignments']
        host_vars['zerotier_lastOnline'] = host['lastOnline']
        host_vars['zerotier_network'] = host['networkId']
        host_vars['zerotier_online'] = host['online']
        host_vars['zerotier_version'] = host['clientVersion']

        host_vars['ansible_host'] = host['config']['ipAssignments'][0]
        host_vars['ansible_ssh_host'] = host['config']['ipAssignments'][0]

        return host_vars

    def get_hosts(self):
        """Make API call and add hosts to inventory"""

        r = requests.get(
            self.controller + '/api/network/' + self.network + '/member',
            headers={'Authorization': 'bearer ' + self.token})

        for host in r.json():
            if host['online'] or self.include_offline:
                self.add_host(host)

    def json_format_dict(self, data, pretty=False):
        """Converts a dict to a JSON object and dumps it as a formatted string."""
        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

    def parse_cli_args(self):
        """Command line argument processing"""
        parser = argparse.ArgumentParser(
            description='Produce an Ansible inventory from a ZeroTier network')
        parser.add_argument(
            '--list',
            action='store_true',
            default=True,
            help='List hosts (default: True)')
        self.args = parser.parse_args()

    def push(self, my_dict, key, element):
        """Pushed an element onto an array that may not have been defined in the dict."""
        if key in my_dict:
            my_dict[key].append(element)
        else:
            my_dict[key] = [element]

    def read_settings(self):
        """Reads the settings from the .ini file and environment"""
        config_file = os.path.dirname(
            os.path.realpath(__file__)) + '/zerotier.ini'

        if os.path.isfile(config_file):
            config = ConfigParser.ConfigParser()
            config.read(config_file)

            self.controller = config.get('zerotier', 'controller')
            self.network = config.get('zerotier', 'network')
            self.token = config.get('zerotier', 'token')
            self.include_offline = config.getboolean('zerotier',
                                                     'include_offline')

        if os.environ.get('ZT_CONTROLLER'):
            self.controller = os.environ.get('ZT_CONTROLLER')
        if os.environ.get('ZT_NETWORK'):
            self.network = os.environ.get('ZT_NETWORK')
        if os.environ.get('ZT_TOKEN'):
            self.token = os.environ.get('ZT_TOKEN')
        if os.environ.get('ZT_INCLUDEOFFLINE'):
            self.include_offline = os.environ.get('ZT_INCLUDEOFFLINE')
            if self.include_offline in ('False', 'false', '0'):
                self.include_offline = False


if __name__ == '__main__':
    ZeroTierInventory()
