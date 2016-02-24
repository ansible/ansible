#!/usr/bin/env python

'''
Linode external inventory script
=================================

Generates inventory that Ansible can understand by making API request to
Linode using the Chube library.

NOTE: This script assumes Ansible is being executed where Chube is already
installed and has a valid config at ~/.chube. If not, run:

    pip install chube
    echo -e "---\napi_key: <YOUR API KEY GOES HERE>" > ~/.chube

For more details, see: https://github.com/exosite/chube

NOTE: This script also assumes that the Linodes in your account all have
labels that correspond to hostnames that are in your resolver search path.
Your resolver search path resides in /etc/hosts.

When run against a specific host, this script returns the following variables:

    - api_id
    - datacenter_id
    - datacenter_city (lowercase city name of data center, e.g. 'tokyo')
    - label
    - display_group
    - create_dt
    - total_hd
    - total_xfer
    - total_ram
    - status
    - public_ip (The first public IP found)
    - private_ip (The first private IP found, or empty string if none)
    - alert_cpu_enabled
    - alert_cpu_threshold
    - alert_diskio_enabled
    - alert_diskio_threshold
    - alert_bwin_enabled
    - alert_bwin_threshold
    - alert_bwout_enabled
    - alert_bwout_threshold
    - alert_bwquota_enabled
    - alert_bwquota_threshold
    - backup_weekly_daily
    - backup_window
    - watchdog

Peter Sankauskas did most of the legwork here with his linode plugin; I
just adapted that for Linode.
'''

# (c) 2013, Dan Slimmon
#
# This file is part of Ansible,
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

######################################################################

# Standard imports
import os
import re
import sys
import argparse
from time import time

try:
    import json
except ImportError:
    import simplejson as json

try:
    from chube import load_chube_config
    from chube import api as chube_api
    from chube.datacenter import Datacenter
    from chube.linode_obj import Linode
except:
    try:
        # remove local paths and other stuff that may
        # cause an import conflict, as chube is sensitive
        # to name collisions on importing
        old_path = sys.path
        sys.path = [d for d in sys.path if d not in ('', os.getcwd(), os.path.dirname(os.path.realpath(__file__)))]

        from chube import load_chube_config
        from chube import api as chube_api
        from chube.datacenter import Datacenter
        from chube.linode_obj import Linode

        sys.path = old_path
    except Exception as e:
        raise Exception("could not import chube")

load_chube_config()

# Imports for ansible
import ConfigParser

class LinodeInventory(object):
    def __init__(self):
        """Main execution path."""
        # Inventory grouped by display group
        self.inventory = {}
        # Index of label to Linode ID
        self.index = {}
        # Local cache of Datacenter objects populated by populate_datacenter_cache()
        self._datacenter_cache = None

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        # Cache
        if self.args.refresh_cache:
            self.do_api_calls_update_cache()
        elif not self.is_cache_valid():
            self.do_api_calls_update_cache()

        # Data to print
        if self.args.host:
            data_to_print = self.get_host_info()
        elif self.args.list:
            # Display list of nodes for inventory
            if len(self.inventory) == 0:
                data_to_print = self.get_inventory_from_cache()
            else:
                data_to_print = self.json_format_dict(self.inventory, True)

        print(data_to_print)

    def is_cache_valid(self):
        """Determines if the cache file has expired, or if it is still valid."""
        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if os.path.isfile(self.cache_path_index):
                    return True
        return False

    def read_settings(self):
        """Reads the settings from the .ini file."""
        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/linode.ini')

        # Cache related
        cache_path = config.get('linode', 'cache_path')
        self.cache_path_cache = cache_path + "/ansible-linode.cache"
        self.cache_path_index = cache_path + "/ansible-linode.index"
        self.cache_max_age = config.getint('linode', 'cache_max_age')

    def parse_cli_args(self):
        """Command line argument processing"""
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Linode')
        parser.add_argument('--list', action='store_true', default=True,
                           help='List nodes (default: True)')
        parser.add_argument('--host', action='store',
                           help='Get all the variables about a specific node')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                           help='Force refresh of cache by making API requests to Linode (default: False - use cache files)')
        self.args = parser.parse_args()

    def do_api_calls_update_cache(self):
        """Do API calls, and save data in cache files."""
        self.get_nodes()
        self.write_to_cache(self.inventory, self.cache_path_cache)
        self.write_to_cache(self.index, self.cache_path_index)

    def get_nodes(self):
        """Makes an Linode API call to get the list of nodes."""
        try:
            for node in Linode.search(status=Linode.STATUS_RUNNING):
                self.add_node(node)
        except chube_api.linode_api.ApiError as e:
            print("Looks like Linode's API is down:")
            print("")
            print(e)
            sys.exit(1)

    def get_node(self, linode_id):
        """Gets details about a specific node."""
        try:
            return Linode.find(api_id=linode_id)
        except chube_api.linode_api.ApiError as e:
            print("Looks like Linode's API is down:")
            print("")
            print(e)
            sys.exit(1)

    def populate_datacenter_cache(self):
        """Creates self._datacenter_cache, containing all Datacenters indexed by ID."""
        self._datacenter_cache = {}
        dcs = Datacenter.search()
        for dc in dcs:
            self._datacenter_cache[dc.api_id] = dc

    def get_datacenter_city(self, node):
        """Returns a the lowercase city name of the node's data center."""
        if self._datacenter_cache is None:
            self.populate_datacenter_cache()
        location = self._datacenter_cache[node.datacenter_id].location
        location = location.lower()
        location = location.split(",")[0]
        return location

    def add_node(self, node):
        """Adds an node to the inventory and index."""

        dest = node.label

        # Add to index
        self.index[dest] = node.api_id

        # Inventory: Group by node ID (always a group of 1)
        self.inventory[node.api_id] = [dest]

        # Inventory: Group by datacenter city
        self.push(self.inventory, self.get_datacenter_city(node), dest)

        # Inventory: Group by dipslay group
        self.push(self.inventory, node.display_group, dest)

    def get_host_info(self):
        """Get variables about a specific host."""

        if len(self.index) == 0:
            # Need to load index from cache
            self.load_index_from_cache()

        if not self.args.host in self.index:
            # try updating the cache
            self.do_api_calls_update_cache()
            if not self.args.host in self.index:
                # host might not exist anymore
                return self.json_format_dict({}, True)

        node_id = self.index[self.args.host]

        node = self.get_node(node_id)
        node_vars = {}
        for direct_attr in [
            "api_id",
            "datacenter_id",
            "label",
            "display_group",
            "create_dt",
            "total_hd",
            "total_xfer",
            "total_ram",
            "status",
            "alert_cpu_enabled",
            "alert_cpu_threshold",
            "alert_diskio_enabled",
            "alert_diskio_threshold",
            "alert_bwin_enabled",
            "alert_bwin_threshold",
            "alert_bwout_enabled",
            "alert_bwout_threshold",
            "alert_bwquota_enabled",
            "alert_bwquota_threshold",
            "backup_weekly_daily",
            "backup_window",
            "watchdog"
        ]:
            node_vars[direct_attr] = getattr(node, direct_attr)

        node_vars["datacenter_city"] = self.get_datacenter_city(node)
        node_vars["public_ip"] = [addr.address for addr in node.ipaddresses if addr.is_public][0]

        # Set the SSH host information, so these inventory items can be used if
        # their labels aren't FQDNs
        node_vars['ansible_ssh_host'] = node_vars["public_ip"]
        node_vars['ansible_host'] = node_vars["public_ip"]

        private_ips = [addr.address for addr in node.ipaddresses if not addr.is_public]

        if private_ips:
            node_vars["private_ip"] = private_ips[0]

        return self.json_format_dict(node_vars, True)

    def push(self, my_dict, key, element):
        """Pushed an element onto an array that may not have been defined in the dict."""
        if key in my_dict:
            my_dict[key].append(element);
        else:
            my_dict[key] = [element]

    def get_inventory_from_cache(self):
        """Reads the inventory from the cache file and returns it as a JSON object."""
        cache = open(self.cache_path_cache, 'r')
        json_inventory = cache.read()
        return json_inventory

    def load_index_from_cache(self):
        """Reads the index from the cache file and sets self.index."""
        cache = open(self.cache_path_index, 'r')
        json_index = cache.read()
        self.index = json.loads(json_index)

    def write_to_cache(self, data, filename):
        """Writes data in JSON format to a file."""
        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()

    def to_safe(self, word):
        """Escapes any characters that would be invalid in an ansible group name."""
        return re.sub("[^A-Za-z0-9\-]", "_", word)

    def json_format_dict(self, data, pretty=False):
        """Converts a dict to a JSON object and dumps it as a formatted string."""
        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)


LinodeInventory()
