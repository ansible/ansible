# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: ovirt
    plugin_type: inventory
    short_description: oVirt inventory source
    requirements:
      - ovirt-engine-sdk-python >= 4.2.4
    extends_documentation_fragment:
        - inventory_cache
    description:
      - Get inventory hosts from the ovirt service.
      - Uses 'ovirt.yml', 'ovirt4.yml', 'ovirt.yaml', 'ovirt4.yaml' YAML configuration file.
    options:
      plugin:
        description: the name of this plugin, it should alwys be set to 'ovirt' for this plugin to recognize it as it's own.
        required: True
        choices: ['ovirt']
      ovirt_url:
        description: url to ovirt-engine api
        required: True
      ovirt_username:
        description: ovirt authentication user
        required: True
      ovirt_password:
        description: ovirt authentication password
        required : True
      ovirt_cafile:
        description: path to ovirt-engine ca file
        required: False
      ovirt_preferred_interface:
        description: vm network interface from which the ansible_host ip is selected
        required: False
      ovirt_query_filter:
        description: dictionary of filter key-values to query hosts/clusters. See U(https://ovirt.github.io/ovirt-engine-sdk/master/services.m.html#ovirtsdk4\
.services.VmsService.list) for filter parameters.
        required: False
'''

EXAMPLES = '''
# ovirt.yml
# plugin: ovirt
# ovirt_url: http://localhost/ovirt-engine/api
# ovirt_username: ansible-tester
# ovirt_password: secure
# ovirt_query_filter:
#   vm_filter:
#      search: 'name=myvm'
#      case_sensitive: no
#      max: 15
'''

import sys

from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable
from ansible.errors import AnsibleError, AnsibleParserError

try:
    import ovirtsdk4 as sdk
except ImportError:
    print('oVirt inventory script requires ovirt-engine-sdk-python >= 4.2.4')
    sys.exit(1)


class InventoryModule(BaseInventoryPlugin, Cacheable):

    NAME = 'ovirt'

    def __init__(self):

        super(InventoryModule, self).__init__()
        self.connection = None

    def _get_connection(self):
        if self.connection is None:
            self.connection = sdk.Connection(
                url=self.ovirt_engine_url,
                username=self.ovirt_engine_user,
                password=self.ovirt_engine_password,
                ca_file=self.ovirt_engine_cafile
            )
        return self.connection

    def _get_dict_of_struct(self, vm, preferred_interface=None):
        '''  Transform SDK Vm Struct type to Python dictionary.
             :param vm: host struct of which to create dict
             :param preferred_interface: interface to select the asnible_host ip from
             :return dict of vm struct type
        '''

        def get_preferred_interface_ip(devices, preferred_interface=None):
            for device in reversed(devices):
                if preferred_interface is not None:
                    if device.name == preferred_interface:
                        return (device.ips[0].address)
                else:
                    return device.ips[0].address
                return devices[-1].ips[0].address

        connection = self._get_connection()

        vms_service = connection.system_service().vms_service()
        clusters_service = connection.system_service().clusters_service()
        vm_service = vms_service.vm_service(vm.id)
        devices = vm_service.reported_devices_service().list()
        tags = vm_service.tags_service().list()
        stats = vm_service.statistics_service().list()
        labels = vm_service.affinity_labels_service().list()
        groups = clusters_service.cluster_service(
            vm.cluster.id
        ).affinity_groups_service().list()

        return {
            'id': vm.id,
            'name': vm.name,
            'host': connection.follow_link(vm.host).name if vm.host else None,
            'cluster': connection.follow_link(vm.cluster).name,
            'status': str(vm.status),
            'description': vm.description,
            'fqdn': vm.fqdn,
            'os_type': vm.os.type,
            'template': connection.follow_link(vm.template).name,
            'tags': [tag.name for tag in tags],
            'affinity_labels': [label.name for label in labels],
            'affinity_groups': [
                group.name for group in groups
                if vm.name in [vm.name for vm in connection.follow_link(group.vms)]
            ],
            'statistics': dict(
                (stat.name, stat.values[0].datum) for stat in stats
            ),
            'devices': dict(
                (device.name, [ip.address for ip in device.ips]) for device in devices if device.ips
            ),
            'ansible_host': get_preferred_interface_ip(devices, preferred_interface)
        }

    def _query(self, filter=None, preferred_interface=None):
        '''
            :param filter: dictionary of filter parameter/values
            :param preferred_interface: vm network interface from which the ansible_host ip is selected
            :return dict of oVirt vm dicts
        '''
        return [self._get_dict_of_struct(host, preferred_interface) for host in self._get_hosts(filter=filter)]

    def _get_hosts(self, filter=None):
        '''
            :param filter: dictionary of vm filter parameter/values
            :return list of oVirt vm structs
        '''
        connection = self._get_connection()

        vms_service = connection.system_service().vms_service()
        if filter is not None:
            return vms_service.list(**filter)
        else:
            return vms_service.list()

    def _get_clusters(self):
        '''
            :return list of oVirt cluster structs
        '''
        connection = self._get_connection()

        clusters_service = connection.system_service().clusters_service()
        return clusters_service.list()

    def _add_host_to_inventory_groups(self, host, group_prefix, group_names):
        ''' Create groups based on dynamic retrieved facts
            :param host: host name to add
            :param group_prefix: prefix added to inventory group name
            :param group_name: list of inventory groups to add host to
        '''
        for group_name in group_names:
            self.inventory.add_group('{0}_{1}'.format(group_prefix, group_name))
            self.inventory.add_child("{0}_{1}".format(group_prefix, group_name), host)

    def _cast_filter_params(self, param_dict):
        ''' Convert filter parameters to comply with sdk VmsService.list param types
            :param param_dict: dictionary of filter parameters and values
            :return dictionary with casted parameter/value
        '''
        FILTER_MAPPING = {
            'all_content': bool,
            'case_sensitive': bool,
            'filter': bool,
            'follow': str,
            'max': int,
            'search': str
        }

        casted_dict = {}

        for (param, value) in param_dict.items():
            try:
                casted_dict[param] = FILTER_MAPPING[param](value)
            except KeyError:
                raise AnsibleError("Unknown filter option '{0}'".format(param))

        return casted_dict

    def _populate_from_source(self, source_data):

        for cluster in self._get_clusters():
            self.inventory.add_group('cluster_{0}'.format(cluster.name))

        for host in source_data:

            # add host to inventory and associated <cluster_name>_group
            self.inventory.add_host(host.get('name'), 'cluster_{0}'.format(host.get('cluster')))
            for fact, value in host.items():
                self.inventory.set_variable(host.get('name'), fact, value)

            # add host to status_<status> inventory group
            self._add_host_to_inventory_groups(host.get('name'), 'status', [host.get('status')])

            # add host to tag_<name> inventory group
            self._add_host_to_inventory_groups(host.get('name'), 'tag', host.get('tags'))

            # add host to affinity_group_<name> inventory group
            self._add_host_to_inventory_groups(host.get('name'), 'affinity_group', host.get('affinity_groups'))

            # add host to affinity_label_<name> inventory group
            self._add_host_to_inventory_groups(host.get('name'), 'affinity_label', host.get('affinity_labels'))

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('ovirt.yml', 'ovirt4.yml', 'ovirt.yaml', 'ovirt4.yaml')):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):

        super(InventoryModule, self).parse(inventory, loader, path, cache)

        config = self._read_config_data(path)

        self.ovirt_engine_url = self.get_option('ovirt_url')
        self.ovirt_engine_user = self.get_option('ovirt_username')
        self.ovirt_engine_password = self.get_option('ovirt_password')
        self.ovirt_engine_cafile = self.get_option('ovirt_cafile')

        vm_filter = None
        if self.get_option('ovirt_query_filter'):
            vm_filter = self._cast_filter_params(
                self.get_option('ovirt_query_filter').get('vm_filter')
            )
        preferred_interface = self.get_option('ovirt_preferred_interface') or None

        if cache:
            cache = self.get_option('cache')
            cache_key = self.get_cache_key(path)

        source_data = {}
        update_cache = False

        if cache:
            try:
                source_data = self.cache.get(cache_key)
            except KeyError:
                update_cache = True
            else:
                self._populate_from_source(source_data)

        if not cache or update_cache:
            source_data = self._query(filter=vm_filter, preferred_interface=preferred_interface)

        if update_cache:
            self.cache.set(cache_key, source_data)

        self._populate_from_source(source_data)
