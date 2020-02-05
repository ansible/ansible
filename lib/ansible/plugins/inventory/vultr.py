# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yanis Guenane <yanis+ansible@guenane.org>
# Copyright (c) 2019, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
    name: vultr
    plugin_type: inventory
    author:
        - Yanis Guenane (@Spredzy)
        - René Moser (@resmo)
    short_description: Vultr inventory source
    version_added: "2.7"
    extends_documentation_fragment:
        - constructed
    description:
        - Get inventory hosts from Vultr public cloud.
        - Uses an YAML configuration file ending with either I(vultr.yml) or I(vultr.yaml) to set parameter values (also see examples).
        - Uses I(api_config), I(~/.vultr.ini), I(./vultr.ini) or C(VULTR_API_CONFIG) pointing to a Vultr credentials INI file
          (see U(https://docs.ansible.com/ansible/latest/scenario_guides/guide_vultr.html)).
    options:
        plugin:
            description: Token that ensures this is a source file for the 'vultr' plugin.
            type: string
            required: True
            choices: [ vultr ]
        api_account:
            description: Specify the account to be used.
            type: string
            default: default
        api_config:
            description: Path to the vultr configuration file. If not specified will be taken from regular Vultr configuration.
            type: path
            env:
                - name: VULTR_API_CONFIG
        api_key:
            description: Vultr API key. If not specified will be taken from regular Vultr configuration.
            type: string
            env:
                - name: VULTR_API_KEY
        hostname:
            description: Field to match the hostname. Note v4_main_ip corresponds to the main_ip field returned from the API and name to label.
            type: string
            default: v4_main_ip
            choices:
                - v4_main_ip
                - v6_main_ip
                - name
        filter_by_tag:
            description: Only return servers filtered by this tag
            type: string
            version_added: "2.8"
        strict:
            version_added: "2.8"
        compose:
            version_added: "2.8"
        groups:
            version_added: "2.8"
        keyed_groups:
            version_added: "2.8"
'''

EXAMPLES = r'''
# inventory_vultr.yml file in YAML format
# Example command line: ansible-inventory --list -i inventory_vultr.yml

# Group by a region as lower case and with prefix e.g. "vultr_region_amsterdam" and by OS without prefix e.g. "CentOS_7_x64"
plugin: vultr
keyed_groups:
  - prefix: vultr_region
    key: region | lower
  - separator: ""
    key: os

# Pass a tag filter to the API
plugin: vultr
filter_by_tag: Cache
'''

import json

from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.module_utils.six.moves import configparser
from ansible.module_utils.urls import open_url
from ansible.module_utils._text import to_native
from ansible.module_utils.vultr import Vultr, VULTR_API_ENDPOINT, VULTR_USER_AGENT
from ansible.module_utils.six.moves.urllib.parse import quote


SCHEMA = {
    'SUBID': dict(key='id'),
    'label': dict(key='name'),
    'date_created': dict(),
    'allowed_bandwidth_gb': dict(convert_to='int'),
    'auto_backups': dict(key='auto_backup_enabled', convert_to='bool'),
    'current_bandwidth_gb': dict(),
    'kvm_url': dict(),
    'default_password': dict(),
    'internal_ip': dict(),
    'disk': dict(),
    'cost_per_month': dict(convert_to='float'),
    'location': dict(key='region'),
    'main_ip': dict(key='v4_main_ip'),
    'network_v4': dict(key='v4_network'),
    'gateway_v4': dict(key='v4_gateway'),
    'os': dict(),
    'pending_charges': dict(convert_to='float'),
    'power_status': dict(),
    'ram': dict(),
    'plan': dict(),
    'server_state': dict(),
    'status': dict(),
    'firewall_group': dict(),
    'tag': dict(),
    'v6_main_ip': dict(),
    'v6_network': dict(),
    'v6_network_size': dict(),
    'v6_networks': dict(),
    'vcpu_count': dict(convert_to='int'),
}


def _load_conf(path, account):

    if path:
        conf = configparser.ConfigParser()
        conf.read(path)

        if not conf._sections.get(account):
            return None

        return dict(conf.items(account))
    else:
        return Vultr.read_ini_config(account)


def _retrieve_servers(api_key, tag_filter=None):
    api_url = '%s/v1/server/list' % VULTR_API_ENDPOINT
    if tag_filter is not None:
        api_url = api_url + '?tag=%s' % quote(tag_filter)

    try:
        response = open_url(
            api_url, headers={'API-Key': api_key, 'Content-type': 'application/json'},
            http_agent=VULTR_USER_AGENT,
        )
        servers_list = json.loads(response.read())

        return servers_list.values() if servers_list else []
    except ValueError:
        raise AnsibleError("Incorrect JSON payload")
    except Exception as e:
        raise AnsibleError("Error while fetching %s: %s" % (api_url, to_native(e)))


class InventoryModule(BaseInventoryPlugin, Constructable):

    NAME = 'vultr'

    def verify_file(self, path):
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('vultr.yaml', 'vultr.yml')):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path=path)

        conf = _load_conf(self.get_option('api_config'), self.get_option('api_account'))
        try:
            api_key = self.get_option('api_key') or conf.get('key')
        except Exception:
            raise AnsibleError('Could not find an API key. Check inventory file and Vultr configuration files.')

        hostname_preference = self.get_option('hostname')

        # Add a top group 'vultr'
        self.inventory.add_group(group='vultr')

        # Filter by tag is supported by the api with a query
        filter_by_tag = self.get_option('filter_by_tag')
        for server in _retrieve_servers(api_key, filter_by_tag):

            server = Vultr.normalize_result(server, SCHEMA)

            self.inventory.add_host(host=server['name'], group='vultr')

            for attribute, value in server.items():
                self.inventory.set_variable(server['name'], attribute, value)

            if hostname_preference != 'name':
                self.inventory.set_variable(server['name'], 'ansible_host', server[hostname_preference])

            # Use constructed if applicable
            strict = self.get_option('strict')

            # Composed variables
            self._set_composite_vars(self.get_option('compose'), server, server['name'], strict=strict)

            # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
            self._add_host_to_composed_groups(self.get_option('groups'), server, server['name'], strict=strict)

            # Create groups based on variable values and add the corresponding hosts to it
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'), server, server['name'], strict=strict)
