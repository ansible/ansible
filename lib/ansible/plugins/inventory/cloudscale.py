# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
name: cloudscale
plugin_type: inventory
author:
  - Gaudenz Steinlin (@gaudenz)
short_description: cloudscale.ch inventory source
description:
    - Get inventory hosts from cloudscale.ch API
version_added: '2.8'
extends_documentation_fragment:
  - constructed
options:
    plugin:
        description: |
            Token that ensures this is a source file for the 'cloudscale'
            plugin.
        required: True
        choices: ['cloudscale']
    inventory_hostname:
        description: |
            What to register as the inventory hostname.
            If set to 'uuid' the uuid of the server will be used and a
            group will be created for the server name.
            If set to 'name' the name of the server will be used unless
            there are more than one server with the same name in which
            case the 'uuid' logic will be used.
        type: str
        choices:
            - name
            - uuid
        default: "name"
    ansible_host:
        description: |
            Which IP address to register as the ansible_host. If the
            requested value does not exist or this is set to 'none', no
            ansible_host will be set.
        type: str
        choices:
            - public_v4
            - public_v6
            - private
            - none
        default: public_v4
    api_token:
        description: cloudscale.ch API token
        env:
          - name: CLOUDSCALE_API_TOKEN
        type: str
    api_timeout:
        description: Timeout in seconds for calls to the cloudscale.ch API.
        default: 30
        type: int
'''

EXAMPLES = r'''
# cloudscale_inventory.yml file in YAML format
# Example command line: ansible-inventory --list -i cloudscale_inventory.yml

plugin: cloudscale
'''

from collections import defaultdict
from json import loads

from ansible.errors import AnsibleError
from ansible.module_utils.cloudscale import API_URL
from ansible.module_utils.urls import open_url
from ansible.inventory.group import to_safe_group_name
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable

iface_type_map = {
    'public_v4': ('public', 4),
    'public_v6': ('public', 6),
    'private': ('private', 4),
    'none': (None, None),
}


class InventoryModule(BaseInventoryPlugin, Constructable):

    NAME = 'cloudscale'

    def _get_server_list(self):
        # Get list of servers from cloudscale.ch API
        response = open_url(
            API_URL + '/servers',
            headers={'Authorization': 'Bearer %s' % self._token}
        )
        return loads(response.read())

    def verify_file(self, path):
        '''
            :param path: the path to the inventory config file
            :return the contents of the config file
        '''
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('cloudscale.yml', 'cloudscale.yaml')):
                return True
        self.display.debug(
            "cloudscale inventory filename must end with 'cloudscale.yml' or 'cloudscale.yaml'"
        )
        return False

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)

        self._read_config_data(path)

        self._token = self.get_option('api_token')
        if not self._token:
            raise AnsibleError('Could not find an API token. Set the '
                               'CLOUDSCALE_API_TOKEN environment variable.')

        inventory_hostname = self.get_option('inventory_hostname')
        if inventory_hostname not in ('name', 'uuid'):
            raise AnsibleError('Invalid value for option inventory_hostname: %s'
                               % inventory_hostname)

        ansible_host = self.get_option('ansible_host')
        if ansible_host not in iface_type_map:
            raise AnsibleError('Invalid value for option ansible_host: %s'
                               % ansible_host)

        # Merge servers with the same name
        firstpass = defaultdict(list)
        for server in self._get_server_list():
            firstpass[server['name']].append(server)

        # Add servers to inventory
        for name, servers in firstpass.items():
            if len(servers) == 1 and inventory_hostname == 'name':
                self.inventory.add_host(name)
                servers[0]['inventory_hostname'] = name
            else:
                # Two servers with the same name exist, create a group
                # with this name and add the servers by UUID
                group_name = to_safe_group_name(name)
                if group_name not in self.inventory.groups:
                    self.inventory.add_group(group_name)
                for server in servers:
                    self.inventory.add_host(server['uuid'], group_name)
                    server['inventory_hostname'] = server['uuid']

            # Set variables
            iface_type, iface_version = iface_type_map[ansible_host]
            for server in servers:
                hostname = server.pop('inventory_hostname')
                if ansible_host != 'none':
                    addresses = [address['address']
                                 for interface in server['interfaces']
                                 for address in interface['addresses']
                                 if interface['type'] == iface_type
                                 and address['version'] == iface_version]

                    if len(addresses) > 0:
                        self.inventory.set_variable(
                            hostname,
                            'ansible_host',
                            addresses[0],
                        )
                self.inventory.set_variable(
                    hostname,
                    'cloudscale',
                    server,
                )

                variables = self.inventory.hosts[hostname].get_vars()
                # Set composed variables
                self._set_composite_vars(
                    self.get_option('compose'),
                    variables,
                    hostname,
                    self.get_option('strict'),
                )

                # Add host to composed groups
                self._add_host_to_composed_groups(
                    self.get_option('groups'),
                    variables,
                    hostname,
                    self.get_option('strict'),
                )

                # Add host to keyed groups
                self._add_host_to_keyed_groups(
                    self.get_option('keyed_groups'),
                    variables,
                    hostname,
                    self.get_option('strict'),
                )
