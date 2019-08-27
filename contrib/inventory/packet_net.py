#!/usr/bin/env python

'''
Packet.net external inventory script
=================================

Generates inventory that Ansible can understand by making API request to
Packet.net using the Packet library.

NOTE: This script assumes Ansible is being executed where the environment
variable needed for Packet API Token already been set:
    export PACKET_API_TOKEN=Bfse9F24SFtfs423Gsd3ifGsd43sSdfs

This script also assumes there is a packet_net.ini file alongside it.  To specify a
different path to packet_net.ini, define the PACKET_NET_INI_PATH environment variable:

    export PACKET_NET_INI_PATH=/path/to/my_packet_net.ini

'''

# (c) 2016, Peter Sankauskas
# (c) 2017, Tomas Karasek
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

import sys
import os
import argparse
import re
from time import time

from ansible.module_utils import six
from ansible.module_utils.six.moves import configparser

try:
    import packet
except ImportError as e:
    sys.exit("failed=True msg='`packet-python` library required for this script'")

import traceback


import json


ini_section = 'packet'


class PacketInventory(object):

    def _empty_inventory(self):
        return {"_meta": {"hostvars": {}}}

    def __init__(self):
        ''' Main execution path '''

        # Inventory grouped by device IDs, tags, security groups, regions,
        # and availability zones
        self.inventory = self._empty_inventory()

        # Index of hostname (address) to device ID
        self.index = {}

        # Read settings and parse CLI arguments
        self.parse_cli_args()
        self.read_settings()

        # Cache
        if self.args.refresh_cache:
            self.do_api_calls_update_cache()
        elif not self.is_cache_valid():
            self.do_api_calls_update_cache()

        # Data to print
        if self.args.host:
            data_to_print = self.get_host_info()

        elif self.args.list:
            # Display list of devices for inventory
            if self.inventory == self._empty_inventory():
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
        ''' Reads the settings from the packet_net.ini file '''
        if six.PY3:
            config = configparser.ConfigParser()
        else:
            config = configparser.SafeConfigParser()

        _ini_path_raw = os.environ.get('PACKET_NET_INI_PATH')

        if _ini_path_raw:
            packet_ini_path = os.path.expanduser(os.path.expandvars(_ini_path_raw))
        else:
            packet_ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'packet_net.ini')
        config.read(packet_ini_path)

        # items per page
        self.items_per_page = 999
        if config.has_option(ini_section, 'items_per_page'):
            config.get(ini_section, 'items_per_page')

        # Instance states to be gathered in inventory. Default is all of them.
        packet_valid_device_states = [
            'active',
            'inactive',
            'queued',
            'provisioning'
        ]
        self.packet_device_states = []
        if config.has_option(ini_section, 'device_states'):
            for device_state in config.get(ini_section, 'device_states').split(','):
                device_state = device_state.strip()
                if device_state not in packet_valid_device_states:
                    continue
                self.packet_device_states.append(device_state)
        else:
            self.packet_device_states = packet_valid_device_states

        # Cache related
        cache_dir = os.path.expanduser(config.get(ini_section, 'cache_path'))
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        self.cache_path_cache = cache_dir + "/ansible-packet.cache"
        self.cache_path_index = cache_dir + "/ansible-packet.index"
        self.cache_max_age = config.getint(ini_section, 'cache_max_age')

        # Configure nested groups instead of flat namespace.
        if config.has_option(ini_section, 'nested_groups'):
            self.nested_groups = config.getboolean(ini_section, 'nested_groups')
        else:
            self.nested_groups = False

        # Replace dash or not in group names
        if config.has_option(ini_section, 'replace_dash_in_groups'):
            self.replace_dash_in_groups = config.getboolean(ini_section, 'replace_dash_in_groups')
        else:
            self.replace_dash_in_groups = True

        # Configure which groups should be created.
        group_by_options = [
            'group_by_device_id',
            'group_by_hostname',
            'group_by_facility',
            'group_by_project',
            'group_by_operating_system',
            'group_by_plan_type',
            'group_by_tags',
            'group_by_tag_none',
        ]
        for option in group_by_options:
            if config.has_option(ini_section, option):
                setattr(self, option, config.getboolean(ini_section, option))
            else:
                setattr(self, option, True)

        # Do we need to just include hosts that match a pattern?
        try:
            pattern_include = config.get(ini_section, 'pattern_include')
            if pattern_include and len(pattern_include) > 0:
                self.pattern_include = re.compile(pattern_include)
            else:
                self.pattern_include = None
        except configparser.NoOptionError:
            self.pattern_include = None

        # Do we need to exclude hosts that match a pattern?
        try:
            pattern_exclude = config.get(ini_section, 'pattern_exclude')
            if pattern_exclude and len(pattern_exclude) > 0:
                self.pattern_exclude = re.compile(pattern_exclude)
            else:
                self.pattern_exclude = None
        except configparser.NoOptionError:
            self.pattern_exclude = None

        # Projects
        self.projects = []
        configProjects = config.get(ini_section, 'projects')
        configProjects_exclude = config.get(ini_section, 'projects_exclude')
        if (configProjects == 'all'):
            for projectInfo in self.get_projects():
                if projectInfo.name not in configProjects_exclude:
                    self.projects.append(projectInfo.name)
        else:
            self.projects = configProjects.split(",")

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Packet')
        parser.add_argument('--list', action='store_true', default=True,
                            help='List Devices (default: True)')
        parser.add_argument('--host', action='store',
                            help='Get all the variables about a specific device')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to Packet (default: False - use cache files)')
        self.args = parser.parse_args()

    def do_api_calls_update_cache(self):
        ''' Do API calls to each region, and save data in cache files '''

        for projectInfo in self.get_projects():
            if projectInfo.name in self.projects:
                self.get_devices_by_project(projectInfo)

        self.write_to_cache(self.inventory, self.cache_path_cache)
        self.write_to_cache(self.index, self.cache_path_index)

    def connect(self):
        ''' create connection to api server'''
        token = os.environ.get('PACKET_API_TOKEN')
        if token is None:
            raise Exception("Error reading token from environment (PACKET_API_TOKEN)!")
        manager = packet.Manager(auth_token=token)
        return manager

    def get_projects(self):
        '''Makes a Packet API call to get the list of projects'''
        try:
            manager = self.connect()
            projects = manager.list_projects()
            return projects
        except Exception as e:
            traceback.print_exc()
            self.fail_with_error(e, 'getting Packet projects')

    def get_devices_by_project(self, project):
        ''' Makes an Packet API call to the list of devices in a particular
        project '''

        params = {
            'per_page': self.items_per_page
        }

        try:
            manager = self.connect()
            devices = manager.list_devices(project_id=project.id, params=params)

            for device in devices:
                self.add_device(device, project)

        except Exception as e:
            traceback.print_exc()
            self.fail_with_error(e, 'getting Packet devices')

    def fail_with_error(self, err_msg, err_operation=None):
        '''log an error to std err for ansible-playbook to consume and exit'''
        if err_operation:
            err_msg = 'ERROR: "{err_msg}", while: {err_operation}\n'.format(
                err_msg=err_msg, err_operation=err_operation)
        sys.stderr.write(err_msg)
        sys.exit(1)

    def get_device(self, device_id):
        manager = self.connect()

        device = manager.get_device(device_id)
        return device

    def add_device(self, device, project):
        ''' Adds a device to the inventory and index, as long as it is
        addressable '''

        # Only return devices with desired device states
        if device.state not in self.packet_device_states:
            return

        # Select the best destination address. Only include management
        # addresses as non-management (elastic) addresses need manual
        # host configuration to be routable.
        # See https://help.packet.net/article/54-elastic-ips.
        dest = None
        for ip_address in device.ip_addresses:
            if ip_address['public'] is True and \
               ip_address['address_family'] == 4 and \
               ip_address['management'] is True:
                dest = ip_address['address']

        if not dest:
            # Skip devices we cannot address (e.g. private VPC subnet)
            return

        # if we only want to include hosts that match a pattern, skip those that don't
        if self.pattern_include and not self.pattern_include.match(device.hostname):
            return

        # if we need to exclude hosts that match a pattern, skip those
        if self.pattern_exclude and self.pattern_exclude.match(device.hostname):
            return

        # Add to index
        self.index[dest] = [project.id, device.id]

        # Inventory: Group by device ID (always a group of 1)
        if self.group_by_device_id:
            self.inventory[device.id] = [dest]
            if self.nested_groups:
                self.push_group(self.inventory, 'devices', device.id)

        # Inventory: Group by device name (hopefully a group of 1)
        if self.group_by_hostname:
            self.push(self.inventory, device.hostname, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'hostnames', project.name)

        # Inventory: Group by project
        if self.group_by_project:
            self.push(self.inventory, project.name, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'projects', project.name)

        # Inventory: Group by facility
        if self.group_by_facility:
            self.push(self.inventory, device.facility['code'], dest)
            if self.nested_groups:
                if self.group_by_facility:
                    self.push_group(self.inventory, project.name, device.facility['code'])

        # Inventory: Group by OS
        if self.group_by_operating_system:
            self.push(self.inventory, device.operating_system.slug, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'operating_systems', device.operating_system.slug)

        # Inventory: Group by plan type
        if self.group_by_plan_type:
            self.push(self.inventory, device.plan['slug'], dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'plans', device.plan['slug'])

        # Inventory: Group by tag keys
        if self.group_by_tags:
            for k in device.tags:
                key = self.to_safe("tag_" + k)
                self.push(self.inventory, key, dest)
                if self.nested_groups:
                    self.push_group(self.inventory, 'tags', self.to_safe("tag_" + k))

        # Global Tag: devices without tags
        if self.group_by_tag_none and len(device.tags) == 0:
            self.push(self.inventory, 'tag_none', dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'tags', 'tag_none')

        # Global Tag: tag all Packet devices
        self.push(self.inventory, 'packet', dest)

        self.inventory["_meta"]["hostvars"][dest] = self.get_host_info_dict_from_device(device)

    def get_host_info_dict_from_device(self, device):
        device_vars = {}
        for key in vars(device):
            value = getattr(device, key)
            key = self.to_safe('packet_' + key)

            # Handle complex types
            if key == 'packet_state':
                device_vars[key] = device.state or ''
            elif key == 'packet_hostname':
                device_vars[key] = value
            elif isinstance(value, (int, bool)):
                device_vars[key] = value
            elif isinstance(value, six.string_types):
                device_vars[key] = value.strip()
            elif value is None:
                device_vars[key] = ''
            elif key == 'packet_facility':
                device_vars[key] = value['code']
            elif key == 'packet_operating_system':
                device_vars[key] = value.slug
            elif key == 'packet_plan':
                device_vars[key] = value['slug']
            elif key == 'packet_tags':
                for k in value:
                    key = self.to_safe('packet_tag_' + k)
                    device_vars[key] = k
            else:
                pass
                # print key
                # print type(value)
                # print value

        return device_vars

    def get_host_info(self):
        ''' Get variables about a specific host '''

        if len(self.index) == 0:
            # Need to load index from cache
            self.load_index_from_cache()

        if self.args.host not in self.index:
            # try updating the cache
            self.do_api_calls_update_cache()
            if self.args.host not in self.index:
                # host might not exist anymore
                return self.json_format_dict({}, True)

        (project_id, device_id) = self.index[self.args.host]

        device = self.get_device(device_id)
        return self.json_format_dict(self.get_host_info_dict_from_device(device), True)

    def push(self, my_dict, key, element):
        ''' Push an element onto an array that may not have been defined in
        the dict '''
        group_info = my_dict.setdefault(key, [])
        if isinstance(group_info, dict):
            host_list = group_info.setdefault('hosts', [])
            host_list.append(element)
        else:
            group_info.append(element)

    def push_group(self, my_dict, key, element):
        ''' Push a group as a child of another group. '''
        parent_group = my_dict.setdefault(key, {})
        if not isinstance(parent_group, dict):
            parent_group = my_dict[key] = {'hosts': parent_group}
        child_groups = parent_group.setdefault('children', [])
        if element not in child_groups:
            child_groups.append(element)

    def get_inventory_from_cache(self):
        ''' Reads the inventory from the cache file and returns it as a JSON
        object '''

        cache = open(self.cache_path_cache, 'r')
        json_inventory = cache.read()
        return json_inventory

    def load_index_from_cache(self):
        ''' Reads the index from the cache file sets self.index '''

        cache = open(self.cache_path_index, 'r')
        json_index = cache.read()
        self.index = json.loads(json_index)

    def write_to_cache(self, data, filename):
        ''' Writes data in JSON format to a file '''

        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()

    def uncammelize(self, key):
        temp = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', key)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', temp).lower()

    def to_safe(self, word):
        ''' Converts 'bad' characters in a string to underscores so they can be used as Ansible groups '''
        regex = r"[^A-Za-z0-9\_"
        if not self.replace_dash_in_groups:
            regex += r"\-"
        return re.sub(regex + "]", "_", word)

    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted
        string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)


# Run the script
PacketInventory()
