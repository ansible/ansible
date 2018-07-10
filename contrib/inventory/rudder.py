#!/usr/bin/env python

# Copyright (c) 2015, Normation SAS
#
# Inspired by the EC2 inventory plugin:
# https://github.com/ansible/ansible/blob/devel/contrib/inventory/ec2.py
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
Rudder external inventory script
=================================

Generates inventory that Ansible can understand by making API request to
a Rudder server. This script is compatible with Rudder 2.10 or later.

The output JSON includes all your Rudder groups, containing the hostnames of
their nodes. Groups and nodes have a variable called rudder_group_id and
rudder_node_id, which is the Rudder internal id of the item, allowing to identify
them uniquely. Hosts variables also include your node properties, which are
key => value properties set by the API and specific to each node.

This script assumes there is an rudder.ini file alongside it. To specify a
different path to rudder.ini, define the RUDDER_INI_PATH environment variable:

    export RUDDER_INI_PATH=/path/to/my_rudder.ini

You have to configure your Rudder server information, either in rudder.ini or
by overriding it with environment variables:

    export RUDDER_API_VERSION='latest'
    export RUDDER_API_TOKEN='my_token'
    export RUDDER_API_URI='https://rudder.local/rudder/api'
'''


import sys
import os
import re
import argparse
import six
import httplib2 as http
from time import time
from ansible.module_utils.six.moves import configparser
from ansible.module_utils.six.moves.urllib.parse import urlparse

try:
    import json
except ImportError:
    import simplejson as json


class RudderInventory(object):
    def __init__(self):
        ''' Main execution path '''

        # Empty inventory by default
        self.inventory = {}

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        # Create connection
        self.conn = http.Http(disable_ssl_certificate_validation=self.disable_ssl_validation)

        # Cache
        if self.args.refresh_cache:
            self.update_cache()
        elif not self.is_cache_valid():
            self.update_cache()
        else:
            self.load_cache()

        data_to_print = {}

        if self.args.host:
            data_to_print = self.get_host_info(self.args.host)
        elif self.args.list:
            data_to_print = self.get_list_info()

        print(self.json_format_dict(data_to_print, True))

    def read_settings(self):
        ''' Reads the settings from the rudder.ini file '''
        if six.PY2:
            config = configparser.SafeConfigParser()
        else:
            config = configparser.ConfigParser()
        rudder_default_ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'rudder.ini')
        rudder_ini_path = os.path.expanduser(os.path.expandvars(os.environ.get('RUDDER_INI_PATH', rudder_default_ini_path)))
        config.read(rudder_ini_path)

        self.token = os.environ.get('RUDDER_API_TOKEN', config.get('rudder', 'token'))
        self.version = os.environ.get('RUDDER_API_VERSION', config.get('rudder', 'version'))
        self.uri = os.environ.get('RUDDER_API_URI', config.get('rudder', 'uri'))

        self.disable_ssl_validation = config.getboolean('rudder', 'disable_ssl_certificate_validation')
        self.group_name = config.get('rudder', 'group_name')
        self.fail_if_name_collision = config.getboolean('rudder', 'fail_if_name_collision')

        self.cache_path = config.get('rudder', 'cache_path')
        self.cache_max_age = config.getint('rudder', 'cache_max_age')

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Rudder inventory')
        parser.add_argument('--list', action='store_true', default=True,
                            help='List instances (default: True)')
        parser.add_argument('--host', action='store',
                            help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to Rudder (default: False - use cache files)')
        self.args = parser.parse_args()

    def is_cache_valid(self):
        ''' Determines if the cache files have expired, or if it is still valid '''

        if os.path.isfile(self.cache_path):
            mod_time = os.path.getmtime(self.cache_path)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                return True

        return False

    def load_cache(self):
        ''' Reads the cache from the cache file sets self.cache '''

        cache = open(self.cache_path, 'r')
        json_cache = cache.read()

        try:
            self.inventory = json.loads(json_cache)
        except ValueError as e:
            self.fail_with_error('Could not parse JSON response from local cache', 'parsing local cache')

    def write_cache(self):
        ''' Writes data in JSON format to a file '''

        json_data = self.json_format_dict(self.inventory, True)
        cache = open(self.cache_path, 'w')
        cache.write(json_data)
        cache.close()

    def get_nodes(self):
        ''' Gets the nodes list from Rudder '''

        path = '/nodes?select=nodeAndPolicyServer'
        result = self.api_call(path)

        nodes = {}

        for node in result['data']['nodes']:
            nodes[node['id']] = {}
            nodes[node['id']]['hostname'] = node['hostname']
            if 'properties' in node:
                nodes[node['id']]['properties'] = node['properties']
            else:
                nodes[node['id']]['properties'] = []

        return nodes

    def get_groups(self):
        ''' Gets the groups list from Rudder '''

        path = '/groups'
        result = self.api_call(path)

        groups = {}

        for group in result['data']['groups']:
            groups[group['id']] = {'hosts': group['nodeIds'], 'name': self.to_safe(group[self.group_name])}

        return groups

    def update_cache(self):
        ''' Fetches the inventory information from Rudder and creates the inventory '''

        nodes = self.get_nodes()
        groups = self.get_groups()

        inventory = {}

        for group in groups:
            # Check for name collision
            if self.fail_if_name_collision:
                if groups[group]['name'] in inventory:
                    self.fail_with_error('Name collision on groups: "%s" appears twice' % groups[group]['name'], 'creating groups')
            # Add group to inventory
            inventory[groups[group]['name']] = {}
            inventory[groups[group]['name']]['hosts'] = []
            inventory[groups[group]['name']]['vars'] = {}
            inventory[groups[group]['name']]['vars']['rudder_group_id'] = group
            for node in groups[group]['hosts']:
                # Add node to group
                inventory[groups[group]['name']]['hosts'].append(nodes[node]['hostname'])

        properties = {}

        for node in nodes:
            # Check for name collision
            if self.fail_if_name_collision:
                if nodes[node]['hostname'] in properties:
                    self.fail_with_error('Name collision on hosts: "%s" appears twice' % nodes[node]['hostname'], 'creating hosts')
            # Add node properties to inventory
            properties[nodes[node]['hostname']] = {}
            properties[nodes[node]['hostname']]['rudder_node_id'] = node
            for node_property in nodes[node]['properties']:
                properties[nodes[node]['hostname']][self.to_safe(node_property['name'])] = node_property['value']

        inventory['_meta'] = {}
        inventory['_meta']['hostvars'] = properties

        self.inventory = inventory

        if self.cache_max_age > 0:
            self.write_cache()

    def get_list_info(self):
        ''' Gets inventory information from local cache '''

        return self.inventory

    def get_host_info(self, hostname):
        ''' Gets information about a specific host from local cache '''

        if hostname in self.inventory['_meta']['hostvars']:
            return self.inventory['_meta']['hostvars'][hostname]
        else:
            return {}

    def api_call(self, path):
        ''' Performs an API request '''

        headers = {
            'X-API-Token': self.token,
            'X-API-Version': self.version,
            'Content-Type': 'application/json;charset=utf-8'
        }

        target = urlparse(self.uri + path)
        method = 'GET'
        body = ''

        try:
            response, content = self.conn.request(target.geturl(), method, body, headers)
        except:
            self.fail_with_error('Error connecting to Rudder server')

        try:
            data = json.loads(content)
        except ValueError as e:
            self.fail_with_error('Could not parse JSON response from Rudder API', 'reading API response')

        return data

    def fail_with_error(self, err_msg, err_operation=None):
        ''' Logs an error to std err for ansible-playbook to consume and exit '''
        if err_operation:
            err_msg = 'ERROR: "{err_msg}", while: {err_operation}'.format(
                err_msg=err_msg, err_operation=err_operation)
        sys.stderr.write(err_msg)
        sys.exit(1)

    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted
        string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

    def to_safe(self, word):
        ''' Converts 'bad' characters in a string to underscores so they can be
        used as Ansible variable names '''

        return re.sub(r'[^A-Za-z0-9\_]', '_', word)

# Run the script
RudderInventory()
