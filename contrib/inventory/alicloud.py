#!/usr/bin/env python

# Copyright (c) 2017 Alibaba Group Holding Limited. He Guimin <heguimin36@163.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
#  This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see http://www.gnu.org/licenses/.

import sys
import os
import argparse
import re
import yaml

from time import time
from ansible.module_utils.alicloud_ecs import connect_to_acs
if sys.version_info >= (3, 0):
    import configparser
else:
    import ConfigParser as configparser

try:
    import json
except ImportError:
    import simplejson as json

HAS_FOOTMARK = False

try:
    import footmark
    import footmark.ecs
    import footmark.regioninfo
    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


class EcsInventory(object):

    def _empty_inventory(self):
        return {"_meta": {"hostvars": {}}}

    def __init__(self):
        ''' Main execution path '''

        self.inventory = self._empty_inventory()

        # Index of hostname (address) to instance ID
        self.index = {}

        # Alicloud credentials.
        self.credentials = {}

        # Init some variables
        self.regions = []
        self.destination_variable = ""
        self.hostname_variable = ""
        self.destination_format = ""
        self.destination_format_tags = ""
        self.ecs_instance_states = []

        self.cache_path_cache = ""
        self.cache_path_index = ""
        self.cache_max_age = 0

        self.nested_groups = False
        self.replace_dash_in_groups = True

        self.expand_csv_tags = False

        self.pattern_include = None
        self.pattern_exclude = None

        self.ecs_instance_filters = dict(page_size=100)

        # Read settings and parse CLI arguments
        self.args = None
        self.parse_cli_args()
        self.read_settings()

        # Cache
        if self.args.refresh_cache:
            self.do_api_calls_update_cache()
        elif os.path.isfile(self.cache_path_cache) and os.path.isfile(self.cache_path_index):
            if os.path.getmtime(self.cache_path_cache) + self.cache_max_age < time():
                self.do_api_calls_update_cache()
        else:
            self.do_api_calls_update_cache()

        # Data to print
        if self.args.host:
            data_to_print = self.get_host_info()

        elif self.args.list:
            # Display list of instances for inventory
            if self.inventory == self._empty_inventory():
                data_to_print = self.get_inventory_from_cache()
            else:
                data_to_print = self.json_format_dict(self.inventory, True)

        print(data_to_print)

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on ECS')
        parser.add_argument('--list', action='store_true', default=True,
                            help='List instances (default: True)')
        parser.add_argument('--host', action='store',
                            help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to ECS (default: False - use cache files)')
        self.args = parser.parse_args()

    def read_settings(self):
        ''' Reads the settings from the alicloud.ini file '''

        config = configparser.SafeConfigParser()

        ecs_default_ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'alicloud.ini')
        ecs_ini_path = os.path.expanduser(os.path.expandvars(os.environ.get('ALICLOUD_INI_PATH', ecs_default_ini_path)))
        config.read(ecs_ini_path)

        access_key = os.environ.get('ALICLOUD_ACCESS_KEY', os.environ.get('ALICLOUD_ACCESS_KEY_ID', None))
        if not access_key:
            access_key = self.get_option(config, 'credentials', 'alicloud_access_key')

        secret_key = os.environ.get('ALICLOUD_SECRET_KEY', os.environ.get('ALICLOUD_SECRET_ACCESS_KEY', None))
        if not secret_key:
            secret_key = self.get_option(config, 'credentials', 'alicloud_secret_key')

        security_token = os.environ.get('ALICLOUD_SECURITY_TOKEN', None)
        if not security_token:
            security_token = self.get_option(config, 'credentials', 'alicloud_security_token')

        self.credentials = {
            'acs_access_key_id': access_key,
            'acs_secret_access_key': secret_key,
            'security_token': security_token,
        }

        # Regions
        config_regions = self.get_option(config, 'ecs', 'regions')
        if not config_regions or config_regions == 'all':
            all_regions = self.connect_to_ecs(footmark.ecs, "cn-beijing").get_all_regions()

            exclude_regions = []
            if self.get_option(config, 'ecs', 'regions_exclude'):
                exclude_regions = [ex.strip() for ex in self.get_option(config, 'ecs', 'regions_exclude').split(',') if ex.strip()]

            for region in all_regions:
                if exclude_regions and region.id in exclude_regions:
                    continue
                self.regions.append(region.id)
        else:
            self.regions = config_regions.split(",")

        # # Destination addresses
        self.destination_variable = self.get_option(config, 'ecs', 'destination_variable', "")

        self.hostname_variable = self.get_option(config, 'ecs', 'hostname_variable', "")

        self.destination_format = self.get_option(config, 'ecs', 'destination_format', "")
        self.destination_format_tags = self.get_option(config, 'ecs', 'destination_format_tags', "")

        # Instance states to be gathered in inventory. Default is 'running'.
        ecs_valid_instance_states = ['pending', 'running', 'starting', 'stopping', 'stopped']

        if self.get_option(config, 'ecs', 'all_instances'):
            self.ecs_instance_states.extend(ecs_valid_instance_states)
        elif self.get_option(config, 'ecs', 'instance_states'):
            for instance_state in self.get_option(config, 'ecs', 'instance_states').split(","):
                instance_state = instance_state.strip()
                if instance_state not in ecs_valid_instance_states:
                    continue
                self.ecs_instance_states.append(instance_state)
        else:
            self.ecs_instance_states.append('running')

        # Cache related
        cache_dir = os.path.expanduser(self.get_option(config, 'ecs', 'cache_path'))
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        cache_name = 'ansible-alicloud'
        self.cache_path_cache = cache_dir + "/%s.cache" % cache_name
        self.cache_path_index = cache_dir + "/%s.index" % cache_name
        self.cache_max_age = float(self.get_option(config, 'ecs', 'cache_max_age'))

        self.expand_csv_tags = self.get_option(config, 'ecs', 'expand_csv_tags')

        # Configure nested groups instead of flat namespace.
        self.nested_groups = self.get_option(config, 'ecs', 'nested_groups')

        # Configure which groups should be created.
        group_by_options = [
            'group_by_instance_id',
            'group_by_region',
            'group_by_availability_zone',
            'group_by_instance_type',
            'group_by_image_id',
            'group_by_vpc_id',
            'group_by_vswitch_id',
            'group_by_security_group',
            'group_by_tag_keys',
            'group_by_tag_none'
        ]
        for option in group_by_options:
            setattr(self, option, self.get_option(config, 'ecs', option))

        # Do we need to just include hosts that match a pattern?
        try:
            pattern_include = self.get_option(config, 'ecs', 'pattern_include')
            if pattern_include and len(pattern_include) > 0:
                self.pattern_include = re.compile(pattern_include)
        except configparser.NoOptionError:
            raise

        # Do we need to exclude hosts that match a pattern?
        try:
            pattern_exclude = self.get_option(config, 'ecs', 'pattern_exclude')
            if pattern_exclude and len(pattern_exclude) > 0:
                self.pattern_exclude = re.compile(pattern_exclude)
        except configparser.NoOptionError:
            raise

        instance_filters = self.get_option(config, 'ecs', 'instance_filters')
        if instance_filters and len(instance_filters) > 0:
            tags = {}
            for field in instance_filters.split(','):
                field = field.strip()
                if not field or '=' not in field:
                    continue
                key, value = [x.strip() for x in field.split('=', 1)]
                if not key:
                    continue
                elif key.startswith("tag:"):
                    tags[key[4:]] = value
                    continue
                elif key in ['page_size', 'page_number']:
                    try:
                        if value and int(value):
                            value = int(value)
                    except Exception:
                        raise
                self.ecs_instance_filters[key] = value
            if tags:
                self.ecs_instance_filters['tags'] = tags

    def do_api_calls_update_cache(self):
        ''' Do API calls to each region, and save data in cache files '''

        for region in self.regions:
            self.get_instances_by_region(region)

        self.write_to_cache(self.inventory, self.cache_path_cache)
        self.write_to_cache(self.index, self.cache_path_index)

    def get_instances_by_region(self, region):
        ''' List ECS instances in a specified region '''

        conn = connect_to_acs(footmark.ecs, region, **self.credentials)
        instances = []
        page_number = 1
        while True:
            self.ecs_instance_filters['page_number'] = page_number
            insts = conn.describe_instances(**self.ecs_instance_filters)
            instances.extend(insts)
            if insts and len(insts) == self.ecs_instance_filters['page_size']:
                page_number += 1
                continue
            break

        for instance in instances:
            self.add_instance(instance, region)

    def get_instance_by_id(self, region, instance_id):
        ''' Fetch ECS instances in a specified instance ID '''

        instances = connect_to_acs(footmark.ecs, region, **self.credentials).describe_instances(instance_ids=[instance_id])
        if instances and len(instances) > 0:
            return instances[0]

    def add_instance(self, instance, region):
        ''' Adds an instance to the inventory and index, as long as it is addressable '''

        if str.lower(instance.status) not in self.ecs_instance_states:
            return

        # Select the best destination address
        if self.destination_variable:
            if self.destination_variable == 'inner_ip_address':
                self.destination_variable = 'private_ip_address'
            elif self.destination_variable == 'eip_address':
                self.destination_variable = 'public_ip_address'

            dest = getattr(instance, self.destination_variable, None)

        if not dest:
            # Skip instances we cannot address
            return

        # Set the inventory name
        hostname = None
        if self.hostname_variable:
            if self.hostname_variable.startswith('tag_'):
                hostname = instance.tags.get(self.hostname_variable[4:], None)
            else:
                hostname = getattr(instance, self.hostname_variable)

        # If we can't get a nice hostname, use the destination address
        if not hostname:
            hostname = dest
        else:
            hostname = self.to_safe(hostname).lower()

        # if we only want to include hosts that match a pattern, skip those that don't
        if self.pattern_include and not self.pattern_include.match(hostname):
            return

        # if we need to exclude hosts that match a pattern, skip those
        if self.pattern_exclude and self.pattern_exclude.match(hostname):
            return

        # # Add to index
        self.index[hostname] = [region, instance.id, instance.name]

        # Inventory: Group by instance ID (always a group of 1)
        if self.group_by_instance_id:
            self.push(self.inventory, instance.id, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'instances', instance.id)

        # Inventory: Group by region
        if self.group_by_region:
            self.push(self.inventory, region, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'regions', region)

        # Inventory: Group by availability zone
        if self.group_by_availability_zone:
            self.push(self.inventory, instance.zone_id, hostname)
            if self.nested_groups:
                if self.group_by_region:
                    self.push_group(self.inventory, region, instance.zone_id)
                self.push_group(self.inventory, 'zones', instance.zone_id)

        # Inventory: Group by Alicloud Machine Image ID
        if self.group_by_image_id:
            self.push(self.inventory, instance.image_id, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'images', instance.image_id)

        # Inventory: Group by instance type
        if self.group_by_instance_type:
            key = self.to_safe('type_' + instance.instance_type)
            self.push(self.inventory, key, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'types', key)

        # Inventory: Group by VPC
        if self.group_by_vpc_id and instance.vpc_id:
            key = self.to_safe('vpc_id_' + instance.vpc_id)
            self.push(self.inventory, key, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'vpcs', key)

        # Inventory: Group by vswitch
        if self.group_by_vswitch_id and instance.vswitch_id:
            key = self.to_safe('subnet_' + instance.vswitch_id)
            self.push(self.inventory, key, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'subnets', key)

        # Inventory: Group by security group
        if self.group_by_security_group:
            for group in instance.security_group_ids['security_group_id']:
                key = self.to_safe("security_group_" + group)
                self.push(self.inventory, key, hostname)
                if self.nested_groups:
                    self.push_group(self.inventory, 'security_groups', key)

        # Inventory: Group by tag keys
        if self.group_by_tag_keys:
            for k, v in instance.tags.items():
                if self.expand_csv_tags and v and ',' in v:
                    values = map(lambda x: x.strip(), v.split(','))
                else:
                    values = [v]

                for v in values:
                    key = self.to_safe("tag_" + k)
                    if v:
                        key = self.to_safe("tag_" + k + "=" + v)

                    self.push(self.inventory, key, hostname)
                    if self.nested_groups:
                        self.push_group(self.inventory, 'tags', self.to_safe("tag_" + k))
                        if v:
                            self.push_group(self.inventory, self.to_safe("tag_" + k), key)

        # Global Tag: instances without tags
        if self.group_by_tag_none and len(instance.tags) == 0:
            self.push(self.inventory, 'tag_none', hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'tags', 'tag_none')

        self.push(self.inventory, hostname, dest)
        self.push_group(self.inventory, 'alicloud', hostname)

        self.inventory["_meta"]["hostvars"][hostname] = instance.read()
        self.inventory["_meta"]["hostvars"][hostname]['ansible_ssh_host'] = dest

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

        region, instance_id, instance_name = self.index[self.args.host]

        instance = self.get_instance_by_id(region, instance_id)
        return self.json_format_dict(instance.read(), True)

    def connect_to_ecs(self, module, region):

        # Check module args for credentials, then check environment vars access key pair and region
        connect_args = self.credentials
        connect_args['user_agent'] = 'Ansible-Provider-Alicloud'
        conn = connect_to_acs(module, region, **connect_args)
        if conn is None:
            self.fail_with_error("region name: %s likely not supported. Connection to region failed." % region)
        return conn

    def get_option(self, config, module, name, default=None):
        # Check module args and then return them from option
        option = None
        if config.has_option(module, name):
            option = config.get(module, name)
        if option is None:
            return default
        # if str.lower()option in
        return yaml.safe_load(option)

    def push(self, my_dict, key, element):
        ''' Push an element into an array that may not have been defined in the dict '''
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
        ''' Reads the inventory from the cache file and returns it as a JSON object '''

        cache = open(self.cache_path_cache, 'r')
        json_inventory = cache.read()
        return json_inventory

    def load_index_from_cache(self):
        ''' Reads the index from the cache file sets self.index '''
        if not os.path.isfile(self.cache_path_cache) or not os.path.isfile(self.cache_path_index):
            self.write_to_cache(self.inventory, self.cache_path_cache)
            self.write_to_cache(self.index, self.cache_path_index)
        cache = open(self.cache_path_index, 'r')
        json_index = cache.read()
        self.index = json.loads(json_index)

    def write_to_cache(self, data, filename):
        ''' Writes data in JSON format to a file '''
        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()

    def to_safe(self, word):
        ''' Converts 'bad' characters in a string to underscores so they can be used as Ansible groups '''
        regex = r"[^A-Za-z0-9\_"
        if not self.replace_dash_in_groups:
            regex += r"\-"
        return re.sub(regex + "]", "_", word)

    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)


if __name__ == '__main__':
    EcsInventory()
