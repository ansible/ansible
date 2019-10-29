#!/usr/bin/env python
"""
SoftLayer external inventory script.

The SoftLayer Python API client is required. Use `pip install softlayer` to install it.
You have a few different options for configuring your username and api_key. You can pass
environment variables (SL_USERNAME and SL_API_KEY). You can also write INI file to
~/.softlayer or /etc/softlayer.conf. For more information see the SL API at:
- https://softlayer-python.readthedocs.io/en/latest/config_file.html

The SoftLayer Python client has a built in command for saving this configuration file
via the command `sl config setup`.
"""

# Copyright (C) 2014  AJ Bourg <aj@ajbourg.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# I found the structure of the ec2.py script very helpful as an example
# as I put this together. Thanks to whoever wrote that script!
#

import SoftLayer
import re
import argparse
import itertools
import json


class SoftLayerInventory(object):
    common_items = [
        'id',
        'globalIdentifier',
        'hostname',
        'domain',
        'fullyQualifiedDomainName',
        'primaryBackendIpAddress',
        'primaryIpAddress',
        'datacenter',
        'tagReferences',
        'userData.value',
    ]

    vs_items = [
        'lastKnownPowerState.name',
        'powerState',
        'maxCpu',
        'maxMemory',
        'activeTransaction.transactionStatus[friendlyName,name]',
        'status',
    ]

    hw_items = [
        'hardwareStatusId',
        'processorPhysicalCoreAmount',
        'memoryCapacity',
    ]

    def _empty_inventory(self):
        return {"_meta": {"hostvars": {}}}

    def __init__(self):
        '''Main path'''

        self.inventory = self._empty_inventory()

        self.parse_options()

        if self.args.list:
            self.get_all_servers()
            print(self.json_format_dict(self.inventory, True))
        elif self.args.host:
            self.get_all_servers()
            print(self.json_format_dict(self.inventory["_meta"]["hostvars"][self.args.host], True))

    def to_safe(self, word):
        '''Converts 'bad' characters in a string to underscores so they can be used as Ansible groups'''

        return re.sub(r"[^A-Za-z0-9\-\.]", "_", word)

    def push(self, my_dict, key, element):
        '''Push an element onto an array that may not have been defined in the dict'''

        if key in my_dict:
            my_dict[key].append(element)
        else:
            my_dict[key] = [element]

    def parse_options(self):
        '''Parse all the arguments from the CLI'''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on SoftLayer')
        parser.add_argument('--list', action='store_true', default=False,
                            help='List instances (default: False)')
        parser.add_argument('--host', action='store',
                            help='Get all the variables about a specific instance')
        self.args = parser.parse_args()

    def json_format_dict(self, data, pretty=False):
        '''Converts a dict to a JSON object and dumps it as a formatted string'''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

    def process_instance(self, instance, instance_type="virtual"):
        '''Populate the inventory dictionary with any instance information'''

        # only want active instances
        if 'status' in instance and instance['status']['name'] != 'Active':
            return

        # and powered on instances
        if 'powerState' in instance and instance['powerState']['name'] != 'Running':
            return

        # 5 is active for hardware... see https://forums.softlayer.com/forum/softlayer-developer-network/general-discussion/2955-hardwarestatusid
        if 'hardwareStatusId' in instance and instance['hardwareStatusId'] != 5:
            return

        # if there's no IP address, we can't reach it
        if 'primaryIpAddress' not in instance:
            return

        instance['userData'] = instance['userData'][0]['value'] if instance['userData'] else ''

        dest = instance['primaryIpAddress']

        instance['tags'] = list()
        for tag in instance['tagReferences']:
            instance['tags'].append(tag['tag']['name'])

        del instance['tagReferences']

        self.inventory["_meta"]["hostvars"][dest] = instance

        # Inventory: group by memory
        if 'maxMemory' in instance:
            self.push(self.inventory, self.to_safe('memory_' + str(instance['maxMemory'])), dest)
        elif 'memoryCapacity' in instance:
            self.push(self.inventory, self.to_safe('memory_' + str(instance['memoryCapacity'])), dest)

        # Inventory: group by cpu count
        if 'maxCpu' in instance:
            self.push(self.inventory, self.to_safe('cpu_' + str(instance['maxCpu'])), dest)
        elif 'processorPhysicalCoreAmount' in instance:
            self.push(self.inventory, self.to_safe('cpu_' + str(instance['processorPhysicalCoreAmount'])), dest)

        # Inventory: group by datacenter
        self.push(self.inventory, self.to_safe('datacenter_' + instance['datacenter']['name']), dest)

        # Inventory: group by hostname
        self.push(self.inventory, self.to_safe(instance['hostname']), dest)

        # Inventory: group by FQDN
        self.push(self.inventory, self.to_safe(instance['fullyQualifiedDomainName']), dest)

        # Inventory: group by domain
        self.push(self.inventory, self.to_safe(instance['domain']), dest)

        # Inventory: group by type (hardware/virtual)
        self.push(self.inventory, instance_type, dest)

        for tag in instance['tags']:
            self.push(self.inventory, tag, dest)

    def get_virtual_servers(self):
        '''Get all the CCI instances'''
        vs = SoftLayer.VSManager(self.client)
        mask = "mask[%s]" % ','.join(itertools.chain(self.common_items, self.vs_items))
        instances = vs.list_instances(mask=mask)

        for instance in instances:
            self.process_instance(instance)

    def get_physical_servers(self):
        '''Get all the hardware instances'''
        hw = SoftLayer.HardwareManager(self.client)
        mask = "mask[%s]" % ','.join(itertools.chain(self.common_items, self.hw_items))
        instances = hw.list_hardware(mask=mask)

        for instance in instances:
            self.process_instance(instance, 'hardware')

    def get_all_servers(self):
        self.client = SoftLayer.Client()
        self.get_virtual_servers()
        self.get_physical_servers()


SoftLayerInventory()
