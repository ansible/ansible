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
    options:
        regions:
            description: Filter results on a specific Scaleway region
            type: list
            default:
                - ams1
                - par1
        tags:
            description: Filter results on a specific tag
            type: list
        oauth_token:
            required: True
            description: Scaleway OAuth token.
            env:
                # in order of precedence
                - name: SCW_TOKEN
                - name: SCW_API_KEY
                - name: SCW_OAUTH_TOKEN
'''

EXAMPLES = '''
# scaleway_inventory.yml file in YAML format
# Example command line: ansible-inventory --list -i scaleway_inventory.yml

plugin: scaleway
regions:
  - ams1
  - par1
tags:
  - foobar
'''

import json
import os

from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.module_utils.scaleway import SCALEWAY_LOCATION
from ansible.module_utils.urls import open_url
from ansible.module_utils._text import to_native


def _fetch_information(token, url):
    try:
        response = open_url(url,
                            headers={'X-Auth-Token': token,
                                     'Content-type': 'application/json'})
    except Exception as e:
        raise AnsibleError("Error while fetching %s: %s" % (url, to_native(e)))

    try:
        raw_json = json.loads(response.read())
    except ValueError:
        raise AnsibleError("Incorrect JSON payload")

    try:
        return raw_json["servers"]
    except KeyError:
        raise AnsibleError("Incorrect format from the Scaleway API response")


def _build_server_url(api_endpoint):
    return "/".join([api_endpoint, "servers"])


class InventoryModule(BaseInventoryPlugin):
    NAME = 'scaleway'

    def verify_file(self, path):
        return "scaleway" in path

    def _fill_host_variables(self, server_id, server_info):
        targeted_attributes = (
            "arch",
            "commercial_type",
            "organization",
            "state",
            "hostname",
            "state"
        )
        for attribute in targeted_attributes:
            self.inventory.set_variable(server_id, attribute, server_info[attribute])

        self.inventory.set_variable(server_id, "tags", server_info["tags"])
        self.inventory.set_variable(server_id, "ipv4", server_info["public_ip"]["address"])

    def _get_zones(self, config_zones):
        return set(SCALEWAY_LOCATION.keys()).intersection(config_zones)

    def match_groups(self, server_info, tags):
        server_zone = server_info["location"]["zone_id"]
        server_tags = server_info["tags"]

        # If no filtering is defined, all tags are valid groups
        if tags is None:
            return set(server_tags).union((server_zone,))

        matching_tags = set(server_tags).intersection(tags)

        if not matching_tags:
            return set()
        else:
            return matching_tags.union((server_zone,))

    def do_zone_inventory(self, zone, token, tags):
        self.inventory.add_group(zone)
        zone_info = SCALEWAY_LOCATION[zone]

        url = _build_server_url(zone_info["api_endpoint"])
        all_servers = _fetch_information(url=url, token=token)

        for server_info in all_servers:

            groups = self.match_groups(server_info, tags)
            server_id = server_info["id"]

            for group in groups:
                self.inventory.add_group(group=group)
                self.inventory.add_host(group=group, host=server_id)
                self._fill_host_variables(server_id=server_id, server_info=server_info)

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path=path)

        config_zones = self.get_option("regions")
        tags = self.get_option("tags")
        token = self.get_option("oauth_token")

        for zone in self._get_zones(config_zones):
            self.do_zone_inventory(zone=zone, token=token, tags=tags)
