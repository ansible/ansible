# (c) 2018, Yanis Guenane <yanis+ansible@guenane.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
    name: vultr
    plugin_type: inventory
    author:
      - "Yanis Guenane (@Spredzy)"
    short_description: Vultr inventory source
    description:
        - Get inventory hosts from Vultr public cloud.
        - Uses C(api_config), C(~/.vultr.ini), C(./vultr.ini) or VULTR_API_CONFIG path to config file.
    options:
        plugin:
            description: token that ensures this is a source file for the 'vultr' plugin.
            required: True
            choices: ['vultr']
        api_account:
            description: Specify the account to be used.
            default: default
        api_config:
            description: Path to the vultr configuration file. If not specified will be taken from regular Vultr configuration.
            env:
              - name: VULTR_API_CONFIG
        api_key:
            description: Vultr API key. If not specified will be taken from regular Vultr configuration.
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
'''

EXAMPLES = r'''
# vultr_inventory.yml file in YAML format
# Example command line: ansible-inventory --list -i vultr_inventory.yml

plugin: vultr
'''

import json

from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.module_utils.six.moves import configparser
from ansible.module_utils.urls import open_url
from ansible.module_utils._text import to_native
from ansible.module_utils.vultr import Vultr, VULTR_API_ENDPOINT, VULTR_USER_AGENT


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


def _retrieve_servers(api_key):
    api_url = '%s/v1/server/list' % VULTR_API_ENDPOINT

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


class InventoryModule(BaseInventoryPlugin):
    NAME = 'vultr'

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path=path)

        conf = _load_conf(self.get_option('api_config'), self.get_option('api_account'))
        try:
            api_key = self.get_option('api_key') or conf.get('key')
        except Exception:
            raise AnsibleError('Could not find an API key. Check inventory file and Vultr configuration files.')

        hostname_preference = self.get_option('hostname')
        for server in _retrieve_servers(api_key):
            server = Vultr.normalize_result(server, SCHEMA)
            for group in ['region', 'os']:
                self.inventory.add_group(group=server[group])
                self.inventory.add_host(group=server[group], host=server['name'])

            for attribute, value in server.items():
                self.inventory.set_variable(server['name'], attribute, value)

            if hostname_preference != 'name':
                self.inventory.set_variable(server['name'], 'ansible_host', server[hostname_preference])
