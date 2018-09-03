# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)


__metaclass__ = type

DOCUMENTATION = '''
    name: online
    plugin_type: inventory
    author:
      - Remy Leone (@sieben)
    short_description: Online inventory source
    description:
        - Get inventory hosts from Online
    options:
        plugin:
            description: token that ensures this is a source file for the 'online' plugin.
            required: True
            choices: ['online']
        oauth_token:
            required: True
            description: Online OAuth token.
            env:
                # in order of precedence
                - name: ONLINE_TOKEN
                - name: ONLINE_API_KEY
                - name: ONLINE_OAUTH_TOKEN
        hostnames:
            description: List of preference about what to use as an hostname.
            type: list
            default:
                - public_ipv4
            choices:
                - public_ipv4
                - private_ipv4
                - hostname
        groups:
            description: List of groups.
            type: list
            choices:
                - location
                - offer
                - rpn
'''

EXAMPLES = '''
# online_inventory.yml file in YAML format
# Example command line: ansible-inventory --list -i online_inventory.yml

plugin: online
hostnames:
  - public_ipv4
groups:
  - location
  - offer
  - rpn
'''

import json
from sys import version as python_version

from ansible.errors import AnsibleError
from ansible.module_utils.urls import open_url
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.ansible_release import __version__ as ansible_version
from ansible.module_utils.six.moves.urllib.parse import urljoin


class InventoryModule(BaseInventoryPlugin):
    NAME = 'online'
    API_ENDPOINT = "https://api.online.net"

    def extract_public_ipv4(self, host_infos):
        try:
            return host_infos["network"]["ip"][0]
        except (KeyError, TypeError, IndexError):
            self.display.warning("An error happened while extracting public IPv4 address. Information skipped.")
            return None

    def extract_private_ipv4(self, host_infos):
        try:
            return host_infos["network"]["private"][0]
        except (KeyError, TypeError, IndexError):
            self.display.warning("An error happened while extracting private IPv4 address. Information skipped.")
            return None

    def extract_os_name(self, host_infos):
        try:
            return host_infos["os"]["name"]
        except (KeyError, TypeError):
            self.display.warning("An error happened while extracting OS name. Information skipped.")
            return None

    def extract_os_version(self, host_infos):
        try:
            return host_infos["os"]["version"]
        except (KeyError, TypeError):
            self.display.warning("An error happened while extracting OS version. Information skipped.")
            return None

    def extract_hostname(self, host_infos):
        try:
            return host_infos["hostname"]
        except (KeyError, TypeError):
            self.display.warning("An error happened while extracting hostname. Information skipped.")
            return None

    def extract_location(self, host_infos):
        try:
            return host_infos["location"]["datacenter"]
        except (KeyError, TypeError):
            self.display.warning("An error happened while extracting datacenter location. Information skipped.")
            return None

    def extract_offer(self, host_infos):
        try:
            return host_infos["offer"]
        except (KeyError, TypeError):
            self.display.warning("An error happened while extracting commercial offer. Information skipped.")
            return None

    def extract_rpn(self, host_infos):
        try:
            return self.rpn_lookup_cache[host_infos["id"]]
        except (KeyError, TypeError):
            self.display.warning("An error happened while extracting RPN information. Information skipped.")
            return None

    def _fetch_information(self, url):
        try:
            response = open_url(url, headers=self.headers)
        except Exception as e:
            self.display.warning("An error happened while fetching: %s" % url)
            return None

        try:
            raw_data = to_text(response.read(), errors='surrogate_or_strict')
        except UnicodeError:
            raise AnsibleError("Incorrect encoding of fetched payload from Online servers")

        try:
            return json.loads(raw_data)
        except ValueError:
            raise AnsibleError("Incorrect JSON payload")

    @staticmethod
    def extract_rpn_lookup_cache(rpn_list):
        lookup = {}
        for rpn in rpn_list:
            for member in rpn["members"]:
                lookup[member["id"]] = rpn["name"]
        return lookup

    def _fill_host_variables(self, hostname, host_infos):
        targeted_attributes = (
            "offer",
            "id",
            "hostname",
            "location",
            "boot_mode",
            "power",
            "last_reboot",
            "anti_ddos",
            "hardware_watch",
            "support"
        )
        for attribute in targeted_attributes:
            self.inventory.set_variable(hostname, attribute, host_infos[attribute])

        if self.extract_public_ipv4(host_infos=host_infos):
            self.inventory.set_variable(hostname, "public_ipv4", self.extract_public_ipv4(host_infos=host_infos))
            self.inventory.set_variable(hostname, "ansible_host", self.extract_public_ipv4(host_infos=host_infos))

        if self.extract_private_ipv4(host_infos=host_infos):
            self.inventory.set_variable(hostname, "public_ipv4", self.extract_private_ipv4(host_infos=host_infos))

        if self.extract_os_name(host_infos=host_infos):
            self.inventory.set_variable(hostname, "os_name", self.extract_os_name(host_infos=host_infos))

        if self.extract_os_version(host_infos=host_infos):
            self.inventory.set_variable(hostname, "os_version", self.extract_os_name(host_infos=host_infos))

    def _filter_host(self, host_infos, hostname_preferences):

        for pref in hostname_preferences:
            if self.extractors[pref](host_infos):
                return self.extractors[pref](host_infos)

        return None

    def do_server_inventory(self, host_infos, hostname_preferences, group_preferences):

        hostname = self._filter_host(host_infos=host_infos,
                                     hostname_preferences=hostname_preferences)

        # No suitable hostname were found in the attributes and the host won't be in the inventory
        if not hostname:
            return

        self.inventory.add_host(host=hostname)
        self._fill_host_variables(hostname=hostname, host_infos=host_infos)

        for g in group_preferences:
            group = self.group_extractors[g](host_infos)

            if not group:
                return

            self.inventory.add_group(group=group)
            self.inventory.add_host(group=group, host=hostname)

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path=path)

        token = self.get_option("oauth_token")
        hostname_preferences = self.get_option("hostnames")

        group_preferences = self.get_option("groups")
        if group_preferences is None:
            group_preferences = []

        self.extractors = {
            "public_ipv4": self.extract_public_ipv4,
            "private_ipv4": self.extract_private_ipv4,
            "hostname": self.extract_hostname,
        }

        self.group_extractors = {
            "location": self.extract_location,
            "offer": self.extract_offer,
            "rpn": self.extract_rpn
        }

        self.headers = {
            'Authorization': "Bearer %s" % token,
            'User-Agent': "ansible %s Python %s" % (ansible_version, python_version.split(' ')[0]),
            'Content-type': 'application/json'
        }

        servers_url = urljoin(InventoryModule.API_ENDPOINT, "api/v1/server")
        servers_api_path = self._fetch_information(url=servers_url)

        if "rpn" in group_preferences:
            rpn_groups_url = urljoin(InventoryModule.API_ENDPOINT, "api/v1/rpn/group")
            rpn_list = self._fetch_information(url=rpn_groups_url)
            self.rpn_lookup_cache = self.extract_rpn_lookup_cache(rpn_list)

        for server_api_path in servers_api_path:

            server_url = urljoin(InventoryModule.API_ENDPOINT, server_api_path)
            raw_server_info = self._fetch_information(url=server_url)

            if raw_server_info is None:
                continue

            self.do_server_inventory(host_infos=raw_server_info,
                                     hostname_preferences=hostname_preferences,
                                     group_preferences=group_preferences)
