#!/usr/bin/env python

'''
Nutanix external inventory script
=================================

Generates inventory that Ansible can understand by making API requests to one or
more Nutanix clusters.

This script assumes there is a nutanix.yml configuration file alongside it. To
specify a different path to nutanix.yml, define the NUTANIX_YML_PATH environment
variable:

    export NUTANIX_YML_PATH=/path/to/nutanix.yml

This script requires that all VM names and IP addresses be unique across
clusters, and will fail otherwise. This is to prevent VMs with identical names
or IP addresses from overwriting each other in the inventory.

----
Caching is implemented in order to reduce traffic and speed up inventory
results. The length of time cache files are kept is determined by
cache_max_age in nutanix.yml. To never read from cache, set cache_max_age to 0.

You can also force an update of the cache with the --refresh-cache switch.

----
For each host, the following variables are registered:
 - acropolisVm
 - clusterUuid
 - consistencyGroupName
 - containerIds - list
 - containerUuids - list
 - controllerVm
 - cpuReservedInHz
 - diskCapacityInBytes
 - displayable
 - fingerPrintOnWrite
 - guestOperatingSystem
 - hostId
 - hostName
 - hostUuid
 - hypervisorType
 - ipAddresses - list
 - memoryCapacityInBytes
 - memoryReservedCapacityInBytes
 - numNetworkAdapters
 - numVCpus
 - nutanixGuestTools - object
 - nutanixVirtualDiskIds - list
 - nutanixVirtualDiskUuids - list
 - nutanixVirtualDisks - list
 - onDiskDedup
 - powerState
 - protectionDomainName
 - runningOnNdfs
 - stats - object
 - usageStats - object
 - uuid
 - vdiskFilePaths - list
 - vdiskNames - list
 - virtualNicIds - list
 - virtualNicUuids - list
 - vmId
 - vmName

You can run against a specific host by using --host and specifying either
the VM name or IP address.

When run in --list mode, which is the default mode when Ansible calls this
script, VMs are enumerated by their IP (note that VMs without assigned IPs will
not be output) and grouped according to the following:
 - Name of their respective cluster.
 - Any groups specified in the VM description field.
 - The _meta group, with the above variables registered plus any hostvars
   specified in the VM description field.

When run in --names mode, or when environment variable NUTANIX_MODE=names, VMs
are enumerated by their names and grouped according to the following:
 - Name of their respective cluster.
 - Any groups specified in the VM description field.
 - Power state.
 - The _meta group, with the above variables registered plus any hostvars
   specified in the VM description field.

Ansible can use --names mode on the command line as in the following:

    NUTANIX_MODE=names ansible-playbook -i nutanix.py myplaybook.yml

A VM description should look something like one of the following:

    {"groups":["tomcat"]}
    {"groups":["texas","pd","tomcat"]}
    {"groups":["texas","pd","nfs"],"hostvars":{"foo":"bar","boo":"far"}}

VM descriptions can also be enclosed in quotes, which can be useful if using a
script to pass descriptions as strings when creating or updating VMs.

NOTE: VMs whose descriptions are not in JSON will not be grouped according to
any description field information, though they will still be grouped according
to cluster name and, if listed by name, power state.

The --pretty option pretty-prints the output for better human readability.

----
usage: nutanix.py [-h] [--list] [--host HOST] [--names] [--pretty]
                  [--refresh-cache]

Produce an Ansible inventory file from Nutanix

optional arguments:
  -h, --help       show this help message and exit
  --list           List instances by IP address (default: True)
  --host HOST      Get all variables about a VM
  --names          List instances by VM name
  --pretty         Pretty-print results
  --refresh-cache  Force refresh of cache by making API requests to Nutanix
                   (default: False - use cache files)
----

'''

# (c) 2017, Matthew Keeler <matt@keeler.org>
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

import os
import sys
from time import time
import argparse
import socket
import requests
import yaml

try:
    import json
except ImportError:
    import simplejson as json


class NutanixInventory(object):

    def __init__(self):
        ''' Main execution path '''

        requests.packages.urllib3.disable_warnings()
        self.session = requests.Session()

        # Parse CLI arguments
        self.parse_cli_args()
        # Get environment variable
        nutanix_mode = os.environ.get('NUTANIX_MODE')

        if self.args.host:
            self.nutanix_inventory('host')
        elif self.args.names or bool(nutanix_mode == 'names'):
            self.names = True
            if self.args.refresh_cache:
                self.nutanix_cache('refresh')
            else:
                self.nutanix_cache('cache')
        else:
            self.names = False
            if self.args.refresh_cache:
                self.nutanix_cache('refresh')
            else:
                self.nutanix_cache('cache')

        if self.args.pretty:
            print(json.dumps(self.inventory, sort_keys=True, indent=2))
        else:
            print(self.inventory)

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(
            description='Produce an Ansible inventory file from Nutanix')

        parser.add_argument('--list', action='store_true', default=True,
                            help='List instances by IP address (default: True)')
        parser.add_argument('--host', action='store',
                            help='Get all variables about a VM')
        parser.add_argument('--names', action='store_true',
                            help='List instances by VM name')
        parser.add_argument('--pretty', action='store_true',
                            help='Pretty-print results')
        parser.add_argument('--refresh-cache', action='store_true',
                            help='Force refresh of cache by making API requests to Nutanix (default: False - use cache files)')

        self.args = parser.parse_args()

    @staticmethod
    def get_settings():
        ''' Retrieve settings from nutanix.yml '''

        nutanix_default_yml_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'nutanix.yml')

        nutanix_yml_path = os.path.expanduser(
            os.path.expandvars(
                os.environ.get('NUTANIX_YML_PATH', nutanix_default_yml_path)))

        try:
            with open(nutanix_yml_path) as nutanix_yml_file:
                config = yaml.safe_load(nutanix_yml_file)
        except IOError:
            print('Could not find nutanix.yml file at {}'
                  .format(nutanix_yml_path))
            sys.exit(1)

        return config

    def authenticate(self):
        ''' Authenticate to the Nutanix cluster API '''

        payload = {
            'j_username': self.nutanix_username,
            'j_password': self.nutanix_password
        }

        response = self.session.post(
            'https://{}:{}/PrismGateway/j_spring_security_check'
            .format(self.nutanix_address, self.nutanix_port),
            data=payload, verify=self.verify_ssl)

        if response.status_code == 401:
            print("Failed to authenticate to {}.".format(self.nutanix_address))
            sys.exit(1)

    @staticmethod
    def validate_auth(data):
        ''' Validate API authentication '''

        if 'An Authentication object was not found in the SecurityContext' not in data:
            return True

    def get_ahv_list(self):
        ''' Pull from the Nutanix Acropolis API '''

        ahv = self.session.get(
            'https://{}:{}/api/nutanix/v0.8/vms'
            .format(self.nutanix_address, self.nutanix_port),
            verify=self.verify_ssl)

        if not self.validate_auth(ahv.text):
            self.authenticate()
            self.get_ahv_list()
        else:
            self.ahv_list = json.loads(ahv.text)

    def get_prism_list(self):
        ''' Pull from the Nutanix Prism API '''

        prism = self.session.get(
            'https://{}:{}/PrismGateway/services/rest/v1/vms'
            .format(self.nutanix_address, self.nutanix_port),
            verify=self.verify_ssl)

        if not self.validate_auth(prism.text):
            self.authenticate()
            self.get_prism_list()
        else:
            self.prism_list = json.loads(prism.text)

    def get_vm_details(self):
        ''' Get details of a VM '''

        vm = self.session.get(
            'https://{}:{}/PrismGateway/services/rest/v1/vms/{}'
            .format(self.nutanix_address, self.nutanix_port, self.vm_uuid),
            verify=self.verify_ssl)

        if not self.validate_auth(vm.text):
            self.authenticate()
            self.get_vm_details()
        else:
            self.vm_details = json.loads(vm.text)

    def get_host_info(self):
        ''' Return information about a VM '''

        # Needed for VM IP and name
        self.get_prism_list()

        host = self.args.host

        # Check if --host arg is IP or VM name
        try:
            socket.inet_aton(host)
            host_by_ip = True
        except socket.error:
            host_by_ip = False

        # Find host by IP
        if host_by_ip:
            for entity in self.prism_list['entities']:
                for address in entity['ipAddresses']:
                    if address == host:
                        self.vm_uuid = entity['uuid']
                        self.get_vm_details()
                        self.inventory.update(self.vm_details)
                        break
                else:
                    continue
                break
        # Find host by VM name
        else:
            for entity in self.prism_list['entities']:
                if entity['vmName'].lower() == host.lower():
                    self.vm_uuid = entity['uuid']
                    self.get_vm_details()
                    self.inventory.update(self.vm_details)
                    break

        return self.inventory

    def get_cluster_info(self):
        ''' Get details of a cluster '''

        cluster = self.session.get(
            'https://{}:{}/PrismGateway/services/rest/v1/cluster'
            .format(self.nutanix_address, self.nutanix_port),
            verify=self.verify_ssl)

        if not self.validate_auth(cluster.text):
            self.authenticate()
            self.get_cluster_info()
        else:
            self.cluster_info = json.loads(cluster.text)

    def build_cluster_inventory(self):
        ''' Generate inventory per cluster '''

        # Needed for VM IPs
        self.get_prism_list()
        # Needed for VM descriptions
        self.get_ahv_list()
        # Needed to get the cluster name
        self.get_cluster_info()

        for prism_entity in self.prism_list['entities']:
            for ahv_entity in self.ahv_list['entities']:
                if prism_entity['uuid'] == ahv_entity['uuid']:
                    # Only build inventory by VM name, or by IP when IPs present
                    if (self.names is True) or (self.names is False and prism_entity['ipAddresses']):
                        if '_meta' not in self.inventory:
                            self.inventory['_meta'] = {'hostvars': {}}
                        if self.cluster_info['name'].lower() not in self.inventory:
                            self.inventory[self.cluster_info['name'].lower()] = {'hosts': []}
                        if self.names:
                            # Only add unique VM names to inventory
                            if prism_entity['vmName'].lower() not in self.inventory['_meta']['hostvars']:
                                self.inventory['_meta']['hostvars'][prism_entity['vmName'].lower()] = {}
                                self.inventory['_meta']['hostvars'][prism_entity['vmName'].lower()].update(prism_entity)
                                self.inventory[self.cluster_info['name'].lower()]['hosts'].append(prism_entity['vmName'].lower())
                            # Fail otherwise
                            else:
                                print('{} exists more than once. Stopping.'.format(prism_entity['vmName'].lower()))
                                sys.exit(1)
                            # Group VMs by power state
                            if ('powerstate_{}'.format(prism_entity['powerState'])) not in self.inventory:
                                self.inventory['powerstate_{}'.format(prism_entity['powerState'])] = {'hosts': []}
                            self.inventory['powerstate_{}'.format(prism_entity['powerState'])]['hosts'].append(prism_entity['vmName'].lower())
                        else:
                            for address in prism_entity['ipAddresses']:
                                # Only add unique IPs to inventory
                                if address not in self.inventory['_meta']['hostvars']:
                                    self.inventory['_meta']['hostvars'][address] = {}
                                    self.inventory['_meta']['hostvars'][address].update(prism_entity)
                                    self.inventory[self.cluster_info['name'].lower()]['hosts'].append(address)
                                # Fail otherwise
                                else:
                                    print('{} exists more than once. Stopping'.format(address))
                                    sys.exit(1)
                        # Look for VMs with a description field
                        if 'description' in ahv_entity['config']:
                            # Look for non-empty descriptions
                            if ahv_entity['config']['description']:
                                # Look for a JSON object in the description
                                try:
                                    # Strip outer quotes, if present
                                    description = json.loads(ahv_entity['config']['description'].strip('"'))
                                    # Register any specified groups
                                    if 'groups' in description:
                                        for group in description['groups']:
                                            if group.lower() not in self.inventory:
                                                self.inventory[group.lower()] = {'hosts': []}
                                            if self.names:
                                                self.inventory[group.lower()]['hosts'].append(prism_entity['vmName'].lower())
                                            else:
                                                for address in prism_entity['ipAddresses']:
                                                    self.inventory[group.lower()]['hosts'].append(address)
                                    # Register any specified hostvars
                                    if 'hostvars' in description:
                                        if '_meta' not in self.inventory:
                                            self.inventory['_meta'] = {'hostvars': {}}
                                        if self.names:
                                            for var in description['hostvars']:
                                                self.inventory['_meta']['hostvars'][prism_entity['vmName'].lower()].update({var: description['hostvars'][var]})
                                        else:
                                            for var in description['hostvars']:
                                                self.inventory['_meta']['hostvars'][address].update({var: description['hostvars'][var]})
                                # Ignore VMs whose description is not in JSON
                                except ValueError:
                                    pass

        return self.inventory

    def nutanix_inventory(self, inventory_type):
        ''' Generate inventory from one or more configured clusters '''

        config = self.get_settings()

        self.inventory = {}

        try:
            cluster_list = config.get('clusters')

            for cluster in cluster_list:
                cluster_details = cluster_list.get(cluster)
                # Get cluster address
                try:
                    self.nutanix_address = cluster_details['address']
                except KeyError:
                    print('An address must be configured for cluster {}.'
                          .format(cluster))
                    sys.exit(1)
                # API port defaults to 9440 unless specified otherwise
                if 'port' in cluster_details:
                    self.nutanix_port = cluster_details['port']
                else:
                    self.nutanix_port = 9440
                # Get cluster username
                try:
                    self.nutanix_username = cluster_details['username']
                except KeyError:
                    print('A username must be configured for cluster {}.'
                          .format(cluster))
                    sys.exit(1)
                # Get cluster password
                try:
                    self.nutanix_password = cluster_details['password']
                except KeyError:
                    print('A password must be configured for cluster {}.'
                          .format(cluster))
                    sys.exit(1)
                # SSL verification defaults to True unless specified otherwise
                if 'verify_ssl' in cluster_details:
                    self.verify_ssl = cluster_details['verify_ssl']
                else:
                    self.verify_ssl = True

                if inventory_type == 'all':
                    self.inventory.update(self.build_cluster_inventory())
                elif inventory_type == 'host':
                    self.inventory.update(self.get_host_info())

            return self.inventory

        except TypeError:
            print('No cluster found in the nutanix.yml configuration file.')
            sys.exit(1)

    def validate_cache(self, filename):
        ''' Determines whether cache file has expired '''

        if os.path.isfile(filename):
            mod_time = os.path.getmtime(filename)
            current_time = time()
            if (mod_time + int(self.cache_max_age)) > current_time:
                return True
        return False

    @staticmethod
    def write_to_cache(data, filename):
        ''' Writes inventory data to a file '''

        cache = open(filename, 'w')
        cache.write(json.dumps(data))
        cache.close()

    def load_from_cache(self, filename):
        ''' Reads inventory data from cache file '''

        cache = open(filename, 'r')
        json_data = cache.read()
        cache.close()
        self.inventory = json.loads(json_data)

    def nutanix_cache(self, status):
        ''' Retrieve or refresh cache '''

        config = self.get_settings()

        try:
            cache_settings = config.get('caching')

            try:
                self.cache_max_age = cache_settings['cache_max_age']
            except KeyError:
                print('A caching time must be set, even if set to 0.')
                sys.exit(1)
            try:
                self.cache_path = cache_settings['cache_path']
            except KeyError:
                print('A path must be set for cached inventory files.')
                sys.exit(1)
            try:
                self.cache_base_name = cache_settings['cache_base_name']
            except KeyError:
                print('A base name must be set for cached inventory files.')
                sys.exit(1)

        except TypeError:
            print('Could not load caching settings from nutanix.yml.')
            sys.exit(1)

        if self.names:
            file_extension = '-names'
        else:
            file_extension = '-list'

        # Pull from cache or update cache if expired
        if status == 'cache':
            if self.validate_cache(self.cache_path
                                   + self.cache_base_name
                                   + file_extension):
                self.load_from_cache(self.cache_path
                                     + self.cache_base_name
                                     + file_extension)
            else:
                self.nutanix_inventory('all')
                try:
                    self.write_to_cache(self.inventory, self.cache_path
                                        + self.cache_base_name
                                        + file_extension)
                except IOError as error:
                    print(error)
                    sys.exit(1)
                self.nutanix_cache('cache')
        # Force refresh
        elif status == 'refresh':
            self.nutanix_inventory('all')
            try:
                self.write_to_cache(self.inventory, self.cache_path
                                    + self.cache_base_name
                                    + file_extension)
            except IOError as error:
                print(error)
                sys.exit(1)
            self.nutanix_cache('cache')

NutanixInventory()
