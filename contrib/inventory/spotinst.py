#!/usr/bin/env python
#
# (c) 2018 Spotinst, <support@spotinst.com>
#
# This file is part of Ansible
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
#
#
#
# Spotinst external inventory script
# ====================================
# Creates an Ansible inventory of the Spotinst Elastigroup instances
#
# ----
# Requires the `spotinst_sdk` Python module
#
# ----
# Configuration is read from the `spotinst.ini` file where you cane specify:
# api_token     - Spotinst API Token
# account_id    - Spotinst Account ID
# group_id      - Elastigroup ID
# cache_path    - Path to store your cache
# cache_timeout - Time cache remains valid
#
# ----
# The following groups are generated from --list:
# - Elastigroup ID
# - Instance ID
#
# ----
# For each host, the following variables are registered:
# - ansible_host
# - ec2_id
# - ec2_image_id
# - ec2_instance_type
# - ec2_ip_address
# - ec2_launch_time
# - ec2_placement
# - ec2_private_ip_address
# - ec2_region
# - ec2_security_group_ids
# - ec2_spot_instance_request_id
# - ec2_state
# - spotinst_eg_id
#
# ----
# This script has been inspired by the digital_ocean.py inventory. thanks
#
# Author: Jeffrey Noehren (@jeffnoehren)
#
# More information about Ansible Dynamic Inventory here
# http://unix.stackexchange.com/questions/205479/in-ansible-dynamic-inventory-json-can-i-render-hostvars-based-on-the-hostname
#
#
import sys
import os
import argparse
from time import time

from spotinst_sdk import SpotinstClient

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

import json


class SpotinstInventory(object):

    def _empty_inventory(self):
        return {"_meta": {"hostvars": {}}}

    def __init__(self):
        self.inventory = self._empty_inventory()

        self.parse_cli_args()
        self.read_settings()

        self.connect_spotinst(account_id=self.account_id, api_token=self.api_token)

        self.cache = {}

        if self.cache_valid():
            self.read_cache()

        if self.args.host:
            self.collect_host_data(group_id=self.args.host)

        elif self.group_id:
            self.collect_host_data(group_id=self.group_id)

        elif self.args.list:
            self.collect_all_data()

        if len(self.inventory.keys()) > len(self.cache.keys()):
            self.write_cache()

        data_to_print = self.json_format_dict(self.inventory, True)
        print(data_to_print)

    ###########################################################################
    # Set-Up
    ###########################################################################

    def parse_cli_args(self):
        ''' Command line argument processing '''
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        self.args = parser.parse_args()

    def read_settings(self):
        ''' Read spotinst.ini file '''
        config = ConfigParser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'spotinst.ini')
        config.read(config_path)

        self.api_token = config.get('spotinst', 'api_token') if config.has_option('spotinst', 'api_token') else None
        self.account_id = config.get('spotinst', 'account_id') if config.has_option('spotinst', 'account_id') else None
        self.group_id = config.get('spotinst', 'group_id') if config.has_option('spotinst', 'group_id') else None
        self.cache_timeout = config.getint('spotinst', 'cache_timeout') if config.has_option('spotinst', 'cache_timeout') else 300
        self.cache_file = (
            config.get('spotinst', 'cache_path') + "/ansible-spotinst.cache"
            if config.has_option('spotinst', 'cache_path')
            else "./ansible-spotinst.cache")

    def connect_spotinst(self, account_id=None, api_token=None):
        ''' Connect to Spotinst Python SDK '''
        try:
            self.conn = SpotinstClient(auth_token=api_token, account_id=account_id)
        except:
            self.fail_with_error("Could Not Connect: Please make sure you set your credentials at ~/.spotinst/credentials or through the spotinst.ini file")

    ###########################################################################
    # Data Collection
    ###########################################################################

    def collect_all_data(self):
        ''' Collects all data (--list) '''

        groups = self.conn.get_elastigroups()

        for single_group in groups:
            self.collect_single_group_data(single_group=single_group)

    def collect_host_data(self, group_id):
        ''' Collects data on one Elastigroup (either --host HOST_NAME or from the spotinst.ini file'''

        single_group = self.conn.get_elastigroup(group_id=group_id)

        self.collect_single_group_data(single_group=single_group)

    def collect_single_group_data(self, single_group):
        ''' Used to get the data from a single elastigroup '''

        if single_group['id'] in self.cache:
            # group exsists in cache and does not need to be analyized
            self.inventory.update({single_group['id']: self.cache[single_group['id']]})

            for single_host in self.cache['_meta']['hostvars']:
                if self.cache['_meta']['hostvars'][single_host]['spotinst_eg_id'] == single_group['id']:
                    instance_id = self.cache['_meta']['hostvars'][single_host]['ec2_id']

                    self.inventory.update({instance_id: self.cache[instance_id]})
                    self.inventory['_meta']['hostvars'].update({single_host: self.cache['_meta']['hostvars'][single_host]})

        else:
            instance_config = self.conn.get_elastigroup_active_instances(group_id=single_group['id'])

            temp_list = []

            for instance in instance_config:

                if instance["public_ip"]:
                    self.inventory.update({instance['instance_id']: [instance["public_ip"]]})
                    temp_list.append(instance["public_ip"])

                    self.inventory['_meta']['hostvars'].update({
                        instance["public_ip"]: dict(
                            ansible_host=instance["public_ip"],
                            ec2_id=instance['instance_id'],
                            ec2_image_id=single_group['compute']['launch_specification']['image_id'],
                            ec2_instance_type=instance['instance_type'],
                            ec2_ip_address=instance["public_ip"],
                            ec2_launch_time=instance['created_at'],
                            ec2_placement=instance['availability_zone'],
                            ec2_private_ip_address=instance["private_ip"],
                            ec2_region=instance['availability_zone'][:-1],
                            ec2_security_group_ids=single_group['compute']['launch_specification']['security_group_ids'],
                            ec2_spot_instance_request_id=instance['spot_instance_request_id'],
                            ec2_state=instance['status'],
                            spotinst_eg_id=single_group['id']
                        )
                    })

            if(len(temp_list) > 0):
                self.inventory.update({single_group['id']: temp_list})

    ###########################################################################
    # Utils
    ###########################################################################

    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted
        string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

    def fail_with_error(self, err_msg, err_operation=None):
        '''log an error to std err for ansible-playbook to consume and exit'''
        if err_operation:
            err_msg = 'ERROR: "{err_msg}", while: {err_operation}'.format(
                err_msg=err_msg, err_operation=err_operation)
        sys.stderr.write(err_msg)
        sys.exit(1)

    ###########################################################################
    # Manage Cache
    ###########################################################################

    def cache_valid(self):
        ''' Determines if the cache files have expired, or if it is still valid '''
        if os.path.isfile(self.cache_file):
            mod_time = os.path.getmtime(self.cache_file)
            current_time = time()
            if (mod_time + self.cache_timeout) > current_time:
                return True
        return False

    def read_cache(self):
        ''' Reads the data from the cache file and assigns it to member variables as Python Objects '''
        try:
            with open(self.cache_file, 'r') as cache:
                json_data = cache.read()
            data = json.loads(json_data)

        except IOError:
            data = {'inventory': {}}

        self.cache = data['inventory']

    def write_cache(self):
        ''' Writes data in JSON format to a file '''
        data = {'inventory': self.inventory}
        json_data = json.dumps(data, indent=2)

        with open(self.cache_file, 'w') as cache:
            cache.write(json_data)


if __name__ == '__main__':
    # Run the script
    SpotinstInventory()
