#!/usr/bin/env python
#
# (c) 2017 Apstra Inc, <community@apstra.com>
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
#
"""
Apstra AOS external inventory script
=================================

Ansible has a feature where instead of reading from /etc/ansible/hosts
as a text file, it can query external programs to obtain the list
of hosts, groups the hosts are in, and even variables to assign to each host.

To use this:
 - copy this file over /etc/ansible/hosts and chmod +x the file.
 - Copy both files (.py and .ini) in your prefered directory

More information about Ansible Dynamic Inventory here
http://unix.stackexchange.com/questions/205479/in-ansible-dynamic-inventory-json-can-i-render-hostvars-based-on-the-hostname

Tested with Apstra AOS 1.1

This script has been inspired by the cobbler.py inventory. thanks
"""

import argparse
import ConfigParser
import os
import xmlrpclib

try:
    from apstra.aosom.session import Session
    from apstra.aosom.exc import SessionError, SessionRqstError, LoginError

    HAS_AOS_PYEZ = True
except ImportError:
    HAS_AOS_PYEZ = False

try:
    import json
except ImportError:
    import simplejson as json

"""
##
Expected output format
{
    "groupname": {
        "hosts": [
            "192.168.28.71",
            "192.168.28.72"
        ],
        "vars": {
            "ansible_ssh_user": "johndoe",
            "ansible_ssh_private_key_file": "~/.ssh/mykey",
            "example_variable": "value"
        }
    },
    "_meta": {
        "hostvars": {
            "192.168.28.71": {
                "host_specific_var": "bar"
            },
            "192.168.28.72": {
                "host_specific_var": "foo"
            }
        }
    }
}
"""
class AosInventory(object):

    def __init__(self):

        """ Main execution path """

        if not HAS_AOS_PYEZ:
            raise Exception('aos-pyez is not installed.  Please see details here: https://github.com/Apstra/aos-pyez')

        # Initialize inventory
        self.inventory = dict()  # A list of groups and the hosts in that group
        self.inventory['_meta'] = dict()
        self.inventory['_meta']['hostvars'] = dict()

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        #----------------------------------------------------
        # Open session to AOS
        #----------------------------------------------------

        # aos = Session(self.aos_server)
        aos = Session(  self.aos_server,
                        port=self.aos_server_port,
                        user=self.aos_username,
                        passwd=self.aos_password)

        aos.login()

        #----------------------------------------------------
        # Build the inventory
        #----------------------------------------------------
        for device in aos.Devices:
            # If not reacheable, create by key and
            # If reacheable, create by hostname

            self.add_host_to_group('all', device.name)

            # populate information for this host
            if 'status' in device.value.keys():
                for key, value in device.value['status'].items():
                    self.add_var_to_host(device.name, key, value)

            if 'user_config' in device.value.keys():
                for key, value in device.value['user_config'].items():
                    self.add_var_to_host(device.name, key, value)

            ## Based on device status online|offline, collect facts as well
            if device.value['status']['comm_state'] == 'on':

                # Populate variables for this host
                self.add_var_to_host(device.name,
                                     'ansible_ssh_host',
                                     device.value['facts']['mgmt_ipaddr'])

                # self.add_host_to_group('all', device.name)
                for key, value in device.value['facts'].items():
                    self.add_var_to_host(device.name, key, value)

                    if key == 'os_family':
                        self.add_host_to_group(value, device.name)
                    elif key == 'hw_model':
                        self.add_host_to_group(value, device.name)

            ## Check if device is associated with a blueprint
            ##   if it's create a new group
            if 'blueprint_active' in device.value['status'].keys():
                if 'blueprint_id' in device.value['status'].keys():
                    bp = aos.Blueprints.find(method='id', key=device.value['status']['blueprint_id'])

                    if bp:
                        self.add_host_to_group(bp['display_name'], device.name)

        #----------------------------------------------------
        # Convert the inventory and return a JSON String
        #----------------------------------------------------
        data_to_print = ""
        data_to_print += self.json_format_dict(self.inventory, True)

        print(data_to_print)

    def read_settings(self):
        """ Reads the settings from the apstra_aos.ini file """

        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/apstra_aos.ini')

        self.aos_server = config.get('aos', 'aos_server')
        self.aos_server_port = config.get('aos', 'port')
        self.aos_username = config.get('aos', 'username')
        self.aos_password = config.get('aos', 'password')

    def parse_cli_args(self):
        """ Command line argument processing """

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Apstra AOS')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        self.args = parser.parse_args()

    def json_format_dict(self, data, pretty=False):
        """ Converts a dict to a JSON object and dumps it as a formatted string """

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

    def add_host_to_group(self, group, host):

        # Check if the group exist, if not initialize it
        if group not in self.inventory.keys():
            self.inventory[group] = {}
            self.inventory[group]['hosts'] = []
            self.inventory[group]['vars'] = {}

        self.inventory[group]['hosts'].append(host)

    def add_var_to_host(self, host, var, value):

        # Check if the host exist, if not initialize it
        if host not in self.inventory['_meta']['hostvars'].keys():
            self.inventory['_meta']['hostvars'][host] = {}

        self.inventory['_meta']['hostvars'][host][var] = value

AosInventory()
