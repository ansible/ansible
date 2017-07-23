#!/usr/bin/env python

# (c) 2013, Sebastien Goasguen <runseb@gmail.com>
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

'''
Apache Libcloud generic external inventory script
=================================

Generates inventory that Ansible can understand by making API request to
Cloud providers using the Apache libcloud library.

This script also assumes there is a libcloud.ini file alongside it

'''

import sys
import os
import argparse
import re
from time import time
import ConfigParser

from six import iteritems, string_types
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
import libcloud.security as sec

try:
    import json
except ImportError:
    import simplejson as json


class LibcloudInventory(object):
    def __init__(self):
        ''' Main execution path '''

        # Inventory grouped by instance IDs, tags, security groups, regions,
        # and availability zones
        self.inventory = {}

        # Index of hostname (address) to instance ID
        self.index = {}

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
            # Display list of instances for inventory
            if len(self.inventory) == 0:
                data_to_print = self.get_inventory_from_cache()
            else:
                data_to_print = self.json_format_dict(self.inventory, True)

        print(data_to_print)

    def is_cache_valid(self):
        ''' Determines if the cache files have expired, or if it is still valid '''

        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if os.path.isfile(self.cache_path_index):
                    return True

        return False

    def read_settings(self):
        ''' Reads the settings from the libcloud.ini file '''

        config = ConfigParser.SafeConfigParser()
        libcloud_default_ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'libcloud.ini')
        libcloud_ini_path = os.environ.get('LIBCLOUD_INI_PATH', libcloud_default_ini_path)
        config.read(libcloud_ini_path)

        if not config.has_section('driver'):
            raise ValueError('libcloud.ini file must contain a [driver] section')

        if config.has_option('driver', 'provider'):
            self.provider = config.get('driver', 'provider')
        else:
            raise ValueError('libcloud.ini does not have a provider defined')

        if config.has_option('driver', 'key'):
            self.key = config.get('driver', 'key')
        else:
            raise ValueError('libcloud.ini does not have a key defined')

        if config.has_option('driver', 'secret'):
            self.secret = config.get('driver', 'secret')
        else:
            raise ValueError('libcloud.ini does not have a secret defined')

        if config.has_option('driver', 'host'):
            self.host = config.get('driver', 'host')
        if config.has_option('driver', 'secure'):
            self.secure = config.get('driver', 'secure')
        if config.has_option('driver', 'verify_ssl_cert'):
            self.verify_ssl_cert = config.get('driver', 'verify_ssl_cert')
        if config.has_option('driver', 'port'):
            self.port = config.get('driver', 'port')
        if config.has_option('driver', 'path'):
            self.path = config.get('driver', 'path')
        if config.has_option('driver', 'api_version'):
            self.api_version = config.get('driver', 'api_version')

        Driver = get_driver(getattr(Provider, self.provider))

        self.conn = Driver(key=self.key, secret=self.secret, secure=self.secure,
                           host=self.host, path=self.path)

        # Cache related
        cache_path = config.get('cache', 'cache_path')
        self.cache_path_cache = cache_path + "/ansible-libcloud.cache"
        self.cache_path_index = cache_path + "/ansible-libcloud.index"
        self.cache_max_age = config.getint('cache', 'cache_max_age')

    def parse_cli_args(self):
        '''
        Command line argument processing
        '''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on libcloud supported providers')
        parser.add_argument('--list', action='store_true', default=True,
                            help='List instances (default: True)')
        parser.add_argument('--host', action='store',
                            help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to libcloud supported providers (default: False - use cache files)')
        self.args = parser.parse_args()

    def do_api_calls_update_cache(self):
        '''
        Do API calls to a location, and save data in cache files
        '''

        self.get_nodes()

        self.write_to_cache(self.inventory, self.cache_path_cache)
        self.write_to_cache(self.index, self.cache_path_index)

    def get_nodes(self):
        '''
        Gets the list of all nodes
        '''

        for node in self.conn.list_nodes():
            self.add_node(node)

    def get_node(self, node_id):
        '''
        Gets details about a specific node
        '''

        return [node for node in self.conn.list_nodes() if node.id == node_id][0]

    def add_node(self, node):
        '''
        Adds a node to the inventory and index, as long as it is
        addressable
        '''

        # Only want running instances
        if node.state != 0:
            return

        # Select the best destination address
        if not node.public_ips == []:
            dest = node.public_ips[0]
        if not dest:
            # Skip instances we cannot address (e.g. private VPC subnet)
            return

        # Add to index
        self.index[dest] = node.name

        # Inventory: Group by instance ID (always a group of 1)
        self.inventory[node.name] = [dest]
        '''
        # Inventory: Group by region
        self.push(self.inventory, region, dest)

        # Inventory: Group by availability zone
        self.push(self.inventory, node.placement, dest)

        # Inventory: Group by instance type
        self.push(self.inventory, self.to_safe('type_' + node.instance_type), dest)
        '''
        # Inventory: Group by key pair
        if node.extra['key_name']:
            self.push(self.inventory, self.to_safe('key_' + node.extra['key_name']), dest)

        # Inventory: Group by security group, quick thing to handle single sg
        if node.extra['security_group']:
            self.push(self.inventory, self.to_safe('sg_' + node.extra['security_group'][0]), dest)

        # Inventory: Group by tag
        if node.extra['tags']:
            for tagkey in node.extra['tags'].keys():
                self.push(self.inventory, self.to_safe('tag_' + tagkey + '_' + node.extra['tags'][tagkey]), dest)

    def get_host_info(self):
        '''
        Get variables about a specific host
        '''

        if len(self.index) == 0:
            # Need to load index from cache
            self.load_index_from_cache()

        if self.args.host not in self.index:
            # try updating the cache
            self.do_api_calls_update_cache()
            if self.args.host not in self.index:
                # host migh not exist anymore
                return self.json_format_dict({}, True)

        node_id = self.index[self.args.host]

        node = self.get_node(node_id)
        instance_vars = {}
        for key, value in vars(node).items():
            key = self.to_safe('ec2_' + key)

            # Handle complex types
            if isinstance(value, (int, bool)):
                instance_vars[key] = value
            elif isinstance(value, string_types):
                instance_vars[key] = value.strip()
            elif value is None:
                instance_vars[key] = ''
            elif key == 'ec2_region':
                instance_vars[key] = value.name
            elif key == 'ec2_tags':
                for k, v in iteritems(value):
                    key = self.to_safe('ec2_tag_' + k)
                    instance_vars[key] = v
            elif key == 'ec2_groups':
                group_ids = []
                group_names = []
                for group in value:
                    group_ids.append(group.id)
                    group_names.append(group.name)
                instance_vars["ec2_security_group_ids"] = ','.join(group_ids)
                instance_vars["ec2_security_group_names"] = ','.join(group_names)
            else:
                pass
                # TODO Product codes if someone finds them useful
                # print(key)
                # print(type(value))
                # print(value)

        return self.json_format_dict(instance_vars, True)

    def push(self, my_dict, key, element):
        '''
        Pushed an element onto an array that may not have been defined in
        the dict
        '''

        if key in my_dict:
            my_dict[key].append(element)
        else:
            my_dict[key] = [element]

    def get_inventory_from_cache(self):
        '''
        Reads the inventory from the cache file and returns it as a JSON
        object
        '''

        cache = open(self.cache_path_cache, 'r')
        json_inventory = cache.read()
        return json_inventory

    def load_index_from_cache(self):
        '''
        Reads the index from the cache file sets self.index
        '''

        cache = open(self.cache_path_index, 'r')
        json_index = cache.read()
        self.index = json.loads(json_index)

    def write_to_cache(self, data, filename):
        '''
        Writes data in JSON format to a file
        '''

        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()

    def to_safe(self, word):
        '''
        Converts 'bad' characters in a string to underscores so they can be
        used as Ansible groups
        '''

        return re.sub("[^A-Za-z0-9\-]", "_", word)

    def json_format_dict(self, data, pretty=False):
        '''
        Converts a dict to a JSON object and dumps it as a formatted
        string
        '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)


def main():
    LibcloudInventory()

if __name__ == '__main__':
    main()
