# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = '''
    name: scaleway
    plugin_type: inventory
    authors:
      - Remy Leone <rleone@online.net>
    short_description: Scaleway inventory source
    description:
        - Get inventory hosts from Scaleway
'''

EXAMPLES = '''
# scaleway_inventory.yml file in YAML format
# Example command line: ansible-inventory --list -i scaleway_inventory.yml

plugin: scaleway
'''

import os
import json
from ansible.module_utils.urls import open_url
from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.module_utils.scaleway import SCALEWAY_LOCATION


def _fetch_information(token, url):
    try:
        response = open_url(url,
                            headers={'X-Auth-Token': token,
                                     'Content-type': 'application/json'})
    except Exception:
        raise AnsibleError("We got the following error while")

    try:
        raw_json = json.loads(response.read())
    except ValueError:
        raise AnsibleError("We got a problem trying to load a JSON objects")

    try:
        return raw_json["servers"]
    except KeyError:
        raise AnsibleError("Incorrect format from the Scaleway API")


def _build_server_url(api_endpoint):
    return "/".join([api_endpoint, "servers"])


class InventoryModule(BaseInventoryPlugin):
    NAME = 'scaleway'

    def __init__(self):
        super(InventoryModule, self).__init__()

        self.token = os.environ["SCW_TOKEN"]
        self.servers_url = "https://api.scaleway.com/servers"

    def _set_credentials(self):
        self.scaleway_access_key = self._options.get('scaleway_access_key')
        if not self.scaleway_access_key:
            raise AnsibleError("Insufficient Scaleway credentials found. Please provide them in your "
                               "inventory configuration file or set them as environment variables.")

        self.scaleway_security_token = self._options.get('scaleway_security_token')
        if not self.scaleway_security_token:
            raise AnsibleError("Insufficient Scaleway credentials found. Please provide them in your "
                               "inventory configuration file or set them as environment variables.")

    def verify_file(self, path):
        return "scaleway" in path

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        config_data = self._read_config_data(path=path)

        targeted_zones = SCALEWAY_LOCATION.items()  # TODO: Users might apply filters
        for zone, zone_info in targeted_zones:
            self.inventory.add_group(zone)
            url = _build_server_url(zone_info["api_endpoint"])
            servers_info = _fetch_information(url=url, token=self.token)
            for server in servers_info:
                server_id = server["id"]
                self.inventory.add_host(group=zone, host=server_id)
                self.inventory.set_variable(server_id, "private_ip", server["private_ip"])
                self.inventory.set_variable(server_id, "arch", server["arch"])
                self.inventory.set_variable(server_id, "commercial_type", server["commercial_type"])
                self.inventory.set_variable(server_id, "organization", server["organization"])
                self.inventory.set_variable(server_id, "state", server["state"])
                self.inventory.set_variable(server_id, "hostname", server["hostname"])
                self.inventory.set_variable(server_id, "tags", server["tags"])
                self.inventory.set_variable(server_id, "ipv4", server["public_ip"]["address"])
                for tag in server["tags"]:
                    self.inventory.add_group(tag)
                    self.inventory.add_host(group=tag, host=server_id)
