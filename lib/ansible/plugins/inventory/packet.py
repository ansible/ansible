# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
    name: packet
    plugin_type: inventory
    author:
      - Maxime Guyot (@Miouge1)
    short_description: Ansible dynamic inventory plugin for Packet.
    version_added: "2.10"
    requirements:
        - python >= 2.7
        - packet
    description:
        - Reads inventories from the Packet API.
        - Uses a YAML configuration file that ends with packet.(yml|yaml).
        - The inventory groups are built from plan, tags and facility.
    options:
        plugin:
            description: marks this as an instance of the 'packet' plugin
            required: true
            choices: ['packet']
        auth_token:
            description: The Packet API auth token
            required: true
            env:
                - name: PACKET_AUTH_TOKEN
        project_id:
          description: Project ID
          required: true
        compose:
            description: Create vars from jinja2 expressions.
            type: dictionary
            default: {}
        groups:
            description: Add hosts to group based on Jinja2 conditionals.
            type: dictionary
            default: {}
        keyed_groups:
            description: Creates groups based on the value of a host variable. Requires a list of dictionaries,
                defining C(key) (the source dictionary-typed variable), C(prefix) (the prefix to use for the new group
                name), and optionally C(separator) (which defaults to C(_))
        strict:
            default: true
            description: Use strict mode
'''

EXAMPLES = r'''
# Minimal example. `PACKET_AUTH_TOKEN` is exposed in environment.
plugin: packet

# Example with regions, types, groups and access token
plugin: packet
auth_token: foobar
project_id: 12345
compose:
  packet_facility_code: facility.code
  keyed_groups:
  - prefix: packet_facility
    key: packet_facility_code
'''

import os

from ansible.basic import missing_required_lib
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils.six import string_types
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable


try:
    from packet import Manager
    HAS_LIB = True
except ImportError:
    HAS_LIB = False


class InventoryModule(BaseInventoryPlugin, Constructable):

    NAME = 'packet'

    def verify_file(self, path):
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('packet.yml', 'packet.yaml')):
                return True
        self.display.debug(
            "Packet inventory filename must end with 'packet.yml' or 'packet.yaml'"
        )
        return False

    def _set_server_attributes(self, device):
        host = device.hostname
        ip = device.ip_addresses[0]['address']
        self.inventory.set_variable(host, 'ansible_host', ip)
        self.inventory.set_variable(host, 'packet_facility', device.facility)
        self.inventory.set_variable(host, 'packet_plan', device.plan)
        self.inventory.set_variable(host, 'packet_tags', device.tags)

    def parse(self, inventory, loader, path, cache=True):
        """Dynamically parse Packet the cloud inventory."""
        super(InventoryModule, self).parse(inventory, loader, path)

        if not HAS_LIB:
            raise AnsibleParserError(msg=missing_required_lib("packet-python"))

        self._read_config_data(path)

        auth_token = self.get_option('auth_token')
        if auth_token is None:
            try:
                auth_token = os.environ['PACKET_AUTH_TOKEN']
            except KeyError:
                pass

        if auth_token is None:
            raise AnsibleError((
                'Could not retrieve Packet auth token '
                'from plugin configuration or environment'
            ))
        # Use constructed if applicable
        strict = self.get_option('strict')

        manager = Manager(auth_token=auth_token)
        params = {'per_page': 50}
        devices = manager.list_devices(project_id=self.get_option('project_id'),
                                       params=params)
        for device in devices:
            self.inventory.add_host(device.hostname)
            # Composed variables
            self._set_composite_vars(self.get_option('compose'), device.__dict__, device.hostname, strict=strict)

            # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
            self._add_host_to_composed_groups(self.get_option('groups'), device.__dict__, device.hostname, strict=strict)

            # Create groups based on variable values and add the corresponding hosts to it
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'), device.__dict__, device.hostname, strict=strict)

            self._set_server_attributes(device)
