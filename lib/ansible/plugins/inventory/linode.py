# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
    name: linode
    plugin_type: inventory
    author:
      - Luke Murphy (@lwm)
    short_description: Ansible dynamic inventory plugin for Linode.
    version_added: "2.8"
    requirements:
        - python >= 2.7
        - linode_api4 >= 2.0.0
    description:
        - Reads inventories from the Linode API v4.
        - Uses a YAML configuration file that ends with linode.(yml|yaml).
        - Linode labels are used by default as the hostnames.
        - The inventory groups are built from groups and not tags.
    options:
        plugin:
            description: marks this as an instance of the 'linode' plugin
            required: true
            choices: ['linode']
        access_token:
            description: The Linode account personal access token.
            required: true
            env:
                - name: LINODE_ACCESS_TOKEN
        regions:
          description: Populate inventory with instances in this region.
          default: []
          type: list
          required: false
        types:
          description: Populate inventory with instances with this type.
          default: []
          type: list
          required: false
'''

EXAMPLES = r'''
# Minimal example. `LINODE_ACCESS_TOKEN` is exposed in environment.
plugin: linode

# Example with regions, types, groups and access token
plugin: linode
access_token: foobar
regions:
  - eu-west
types:
  - g5-standard-2
'''

import os

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils.six import string_types
from ansible.plugins.inventory import BaseInventoryPlugin


try:
    from linode_api4 import LinodeClient
    from linode_api4.errors import ApiError as LinodeApiError
except ImportError:
    raise AnsibleError('the Linode dynamic inventory plugin requires linode_api4.')


class InventoryModule(BaseInventoryPlugin):

    NAME = 'linode'

    def _build_client(self):
        """Build the Linode client."""

        access_token = self.get_option('access_token')

        if access_token is None:
            try:
                access_token = os.environ['LINODE_ACCESS_TOKEN']
            except KeyError:
                pass

        if access_token is None:
            raise AnsibleError((
                'Could not retrieve Linode access token '
                'from plugin configuration or environment'
            ))

        self.client = LinodeClient(access_token)

    def _get_instances_inventory(self):
        """Retrieve Linode instance information from cloud inventory."""
        try:
            self.instances = self.client.linode.instances()
        except LinodeApiError as exception:
            raise AnsibleError('Linode client raised: %s' % exception)

    def _add_groups(self):
        """Add Linode instance groups to the dynamic inventory."""
        self.linode_groups = set(
            filter(None, [
                instance.group
                for instance
                in self.instances
            ])
        )

        for linode_group in self.linode_groups:
            self.inventory.add_group(linode_group)

    def _filter_by_config(self, regions, types):
        """Filter instances by user specified configuration."""
        if regions:
            self.instances = [
                instance for instance in self.instances
                if instance.region.id in regions
            ]

        if types:
            self.instances = [
                instance for instance in self.instances
                if instance.type.id in types
            ]

    def _add_instances_to_groups(self):
        """Add instance names to their dynamic inventory groups."""
        for instance in self.instances:
            self.inventory.add_host(instance.label, group=instance.group)

    def _add_hostvars_for_instances(self):
        """Add hostvars for instances in the dynamic inventory."""
        for instance in self.instances:
            hostvars = instance._raw_json
            for hostvar_key in hostvars:
                self.inventory.set_variable(
                    instance.label,
                    hostvar_key,
                    hostvars[hostvar_key]
                )

    def _validate_option(self, name, desired_type, option_value):
        """Validate user specified configuration data against types."""
        if isinstance(option_value, string_types) and desired_type == list:
            option_value = [option_value]

        if option_value is None:
            option_value = desired_type()

        if not isinstance(option_value, desired_type):
            raise AnsibleParserError(
                'The option %s (%s) must be a %s' % (
                    name, option_value, desired_type
                )
            )

        return option_value

    def _get_query_options(self, config_data):
        """Get user specified query options from the configuration."""
        options = {
            'regions': {
                'type_to_be': list,
                'value': config_data.get('regions', [])
            },
            'types': {
                'type_to_be': list,
                'value': config_data.get('types', [])
            },
        }

        for name in options:
            options[name]['value'] = self._validate_option(
                name,
                options[name]['type_to_be'],
                options[name]['value']
            )

        regions = options['regions']['value']
        types = options['types']['value']

        return regions, types

    def verify_file(self, path):
        """Verify the Linode configuration file."""
        if super(InventoryModule, self).verify_file(path):
            endings = ('linode.yaml', 'linode.yml')
            if any((path.endswith(ending) for ending in endings)):
                return True
        return False

    def parse(self, inventory, loader, path, cache=True):
        """Dynamically parse Linode the cloud inventory."""
        super(InventoryModule, self).parse(inventory, loader, path)

        self._build_client()

        self._get_instances_inventory()

        config_data = self._read_config_data(path)
        regions, types = self._get_query_options(config_data)
        self._filter_by_config(regions, types)

        self._add_groups()
        self._add_instances_to_groups()
        self._add_hostvars_for_instances()
