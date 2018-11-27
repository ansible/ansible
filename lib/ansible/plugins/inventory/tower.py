# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = '''
    name: tower
    plugin_type: inventory
    author:
      - Matthew Jones (@matburt)
      - Yunfan Zhang (@YunfanZhang42)
    short_description: Ansible dynamic inventory plugin for Ansible Tower.
    version_added: "2.7"
    description:
        - Reads inventories from Ansible Tower.
        - Supports reading configuration from both YAML config file and environment variables.
        - If reading from the YAML file, the file name must end with tower.(yml|yaml) or tower_inventory.(yml|yaml),
          the path in the command would be /path/to/tower_inventory.(yml|yaml). If some arguments in the config file
          are missing, this plugin will try to fill in missing arguments by reading from environment variables.
        - If reading configurations from environment variables, the path in the command must be @tower_inventory.
    options:
        plugin:
            description: the name of this plugin, it should always be set to 'tower'
                for this plugin to recognize it as it's own.
            env:
                - name: ANSIBLE_INVENTORY_ENABLED
            required: True
            choices: ['tower']
        host:
            description: The network address of your Ansible Tower host.
            type: string
            env:
                - name: TOWER_HOST
            required: True
        username:
            description: The user that you plan to use to access inventories on Ansible Tower.
            type: string
            env:
                - name: TOWER_USERNAME
            required: True
        password:
            description: The password for your Ansible Tower user.
            type: string
            env:
                - name: TOWER_PASSWORD
            required: True
        inventory_id:
            description: The ID of the Ansible Tower inventory that you wish to import.
            type: string
            env:
                - name: TOWER_INVENTORY
            required: True
        verify_ssl:
            description: Specify whether Ansible should verify the SSL certificate of Ansible Tower host.
            type: bool
            default: True
            env:
                - name: TOWER_VERIFY_SSL
            required: False
'''

EXAMPLES = '''
# Before you execute the following commands, you should make sure this file is in your plugin path,
# and you enabled this plugin.

# Example for using tower_inventory.yml file

plugin: tower
host: your_ansible_tower_server_network_address
username: your_ansible_tower_username
password: your_ansible_tower_password
inventory_id: the_ID_of_targeted_ansible_tower_inventory
# Then you can run the following command.
# If some of the arguments are missing, Ansible will attempt to read them from environment variables.
# ansible-inventory -i /path/to/tower_inventory.yml --list

# Example for reading from environment variables:

# Set environment variables:
# export TOWER_HOST=YOUR_TOWER_HOST_ADDRESS
# export TOWER_USERNAME=YOUR_TOWER_USERNAME
# export TOWER_PASSWORD=YOUR_TOWER_PASSWORD
# export TOWER_INVENTORY=THE_ID_OF_TARGETED_INVENTORY
# Read the inventory specified in TOWER_INVENTORY from Ansible Tower, and list them.
# The inventory path must always be @tower_inventory if you are reading all settings from environment variables.
# ansible-inventory -i @tower_inventory --list
'''

import re
import os
import json
from ansible.module_utils import six
from ansible.module_utils.urls import Request, urllib_error, ConnectionError, socket, httplib
from ansible.module_utils._text import to_native
from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin

# Python 2/3 Compatibility
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin


class InventoryModule(BaseInventoryPlugin):
    NAME = 'tower'
    # Stays backward compatible with tower inventory script.
    # If the user supplies '@tower_inventory' as path, the plugin will read from environment variables.
    no_config_file_supplied = False

    def read_tower_inventory(self, tower_host, tower_user, tower_pass, inventory, verify_ssl=True):
        if not re.match('(?:http|https)://', tower_host):
            tower_host = 'https://{tower_host}'.format(tower_host=tower_host)
        inventory_id = inventory.replace('/', '')
        inventory_url = '/api/v2/inventories/{inv_id}/script/?hostvars=1&towervars=1&all=1'.format(inv_id=inventory_id)
        inventory_url = urljoin(tower_host, inventory_url)

        request_handler = Request(url_username=tower_user,
                                  url_password=tower_pass,
                                  force_basic_auth=True,
                                  validate_certs=verify_ssl)

        try:
            response = request_handler.get(inventory_url)
        except (ConnectionError, urllib_error.URLError, socket.error, httplib.HTTPException) as e:
            error_msg = 'Connection to remote host failed: {err}'.format(err=e)
            # If Tower gives a readable error message, display that message to the user.
            if callable(getattr(e, 'read', None)):
                error_msg += ' with message: {err_msg}'.format(err_msg=e.read())
            raise AnsibleParserError(to_native(error_msg))

        # Attempt to parse JSON.
        try:
            return json.loads(response.read())
        except (ValueError, TypeError) as e:
            # If the JSON parse fails, print the ValueError
            raise AnsibleParserError(to_native('Failed to parse json from host: {err}'.format(err=e)))

    def verify_file(self, path):
        if path.endswith('@tower_inventory'):
            self.no_config_file_supplied = True
            return True
        elif super(InventoryModule, self).verify_file(path):
            return path.endswith(('tower_inventory.yml', 'tower_inventory.yaml', 'tower.yml', 'tower.yaml'))
        else:
            return False

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        if not self.no_config_file_supplied and os.path.isfile(path):
            self._read_config_data(path)
        # Read inventory from tower server.
        # Note the environment variables will be handled automatically by InventoryManager.
        inventory = self.read_tower_inventory(self.get_option('host'),
                                              self.get_option('username'),
                                              self.get_option('password'),
                                              self.get_option('inventory_id'),
                                              verify_ssl=self.get_option('verify_ssl'))
        # To start with, create all the groups.
        for group_name in inventory:
            if group_name != '_meta':
                self.inventory.add_group(group_name)

        # Then, create all hosts and add the host vars.
        all_hosts = inventory['_meta']['hostvars']
        for host_name, host_vars in six.iteritems(all_hosts):
            self.inventory.add_host(host_name)
            for var_name, var_value in six.iteritems(host_vars):
                self.inventory.set_variable(host_name, var_name, var_value)

        # Lastly, create to group-host and group-group relationships, and set group vars.
        for group_name, group_content in six.iteritems(inventory):
            if group_name != 'all' and group_name != '_meta':
                # First add hosts to groups
                for host_name in group_content.get('hosts', []):
                    self.inventory.add_host(host_name, group_name)
                # Then add the parent-children group relationships.
                for child_group_name in group_content.get('children', []):
                    self.inventory.add_child(group_name, child_group_name)
            # Set the group vars. Note we should set group var for 'all', but not '_meta'.
            if group_name != '_meta':
                for var_name, var_value in six.iteritems(group_content.get('vars', {})):
                    self.inventory.set_variable(group_name, var_name, var_value)
        # Clean up the inventory.
        self.inventory.reconcile_inventory()
