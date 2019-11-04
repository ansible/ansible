# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: ovirt
    plugin_type: inventory
    short_description: oVirt inventory source
    version_added: "2.10"
    author: Bram Verschueren (@bverschueren)
    requirements:
      - ovirt-engine-sdk-python >= 4.2.4
    extends_documentation_fragment:
        - inventory_cache
        - constructed
    description:
      - Get inventory hosts from the ovirt service.
      - Requires a YAML file ending in 'ovirt.yml', 'ovirt4.yml', 'ovirt.yaml', 'ovirt4.yaml'.
    options:
      plugin:
        description: the name of this plugin, it should always be set to 'ovirt' for this plugin to recognise it as it's own.
        required: True
        choices: ['ovirt']
      ovirt_url:
        description: URL to ovirt-engine API.
        required: True
        env:
          - name: OVIRT_URL
      ovirt_username:
        description: ovirt authentication user.
        required: True
        env:
          - name: OVIRT_USERNAME
      ovirt_password:
        description: ovirt authentication password.
        required : True
        env:
          - name: OVIRT_PASSWORD
      ovirt_cafile:
        description: path to ovirt-engine CA file.
        required: False
      ovirt_query_filter:
        required: false
        description: dictionary of filter key-values to query VM's. See U(https://ovirt.github.io/ovirt-engine-sdk/master/services.m.html#ovirtsdk4\
.services.VmsService.list) for filter parameters.
      ovirt_hostname_preference:
        required: false
        description: list of options that describe the ordering for which hostnames should be assigned. See U(https://ovirt.github.io/ovirt-engin\
e-api-model/master/#types/vm) for available attributes.
        default: ['fqdn', 'name']
        type: list
'''

EXAMPLES = '''
# Sample content of ovirt.yml
# plugin: ovirt
# ovirt_url: http://localhost/ovirt-engine/api
# ovirt_username: ansible-tester
# ovirt_password: secure
# ovirt_query_filter:
#   search: 'name=myvm AND cluster=mycluster'
#   case_sensitive: no
#   max: 15
# keyed_groups:
#   - key: cluster
#     prefix: 'cluster'
# groups:
#   dev: "'dev' in tags"
# compose:
#   ansible_host: devices["eth0"][0]
'''

import sys

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.errors import AnsibleError, AnsibleParserError

HAS_OVIRT_LIB = False

try:
    import ovirtsdk4 as sdk
    HAS_OVIRT_LIB = True
except ImportError:
    HAS_OVIRT_LIB = False


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

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

    def _get_dict_of_struct(self, vm):
        '''  Transform SDK Vm Struct type to Python dictionary.
             :param vm: host struct of which to create dict
             :return dict of vm struct type
        '''

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
        }

    def _query(self, query_filter=None):
        '''
            :param query_filter: dictionary of filter parameter/values
            :return dict of oVirt vm dicts
        '''
        return [self._get_dict_of_struct(host) for host in self._get_hosts(query_filter=query_filter)]

    def _get_hosts(self, query_filter=None):
        '''
            :param filter: dictionary of vm filter parameter/values
            :return list of oVirt vm structs
        '''
        connection = self._get_connection()

        vms_service = connection.system_service().vms_service()
        if query_filter is not None:
            return vms_service.list(**query_filter)
        else:
            return vms_service.list()

    def _get_query_options(self, param_dict):
        ''' Get filter parameters and cast these to comply with sdk VmsService.list param types
            :param param_dict: dictionary of filter parameters and values
            :return dictionary with casted parameter/value
        '''
        if param_dict is None:
            return None

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

    def _get_hostname(self, host):
        '''
          Get the host's hostname based on prefered attribute
          :param host: dict representation of oVirt VmStruct
          :param return: preferred hostname for the host
        '''
        hostname_preference = self.get_option('ovirt_hostname_preference')
        if not hostname_preference:
            raise AnsibleParserError('Invalid value for option ovirt_hostname_preference: {0}'.format(hostname_preference))
        hostname = None

        for preference in hostname_preference:
            hostname = host.get(preference)
            if hostname is not None:
                return hostname

        raise AnsibleParserError("No valid name found for host id={0}".format(host.get('id')))

    def _populate_from_source(self, source_data):

        for host in source_data:

            hostname = self._get_hostname(host)

            self.inventory.add_host(hostname)

            for fact, value in host.items():
                self.inventory.set_variable(hostname, fact, value)

            self._set_composite_vars(self.get_option('compose'), host, hostname)
            self._add_host_to_composed_groups(self.get_option('groups'), host, hostname)
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'), host, hostname)

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('ovirt.yml', 'ovirt4.yml', 'ovirt.yaml', 'ovirt4.yaml')):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):

        if not HAS_OVIRT_LIB:
            raise AnsibleError('oVirt inventory script requires ovirt-engine-sdk-python >= 4.2.4')

        super(InventoryModule, self).parse(inventory, loader, path, cache)

        config = self._read_config_data(path)

        self.ovirt_engine_url = self.get_option('ovirt_url')
        self.ovirt_engine_user = self.get_option('ovirt_username')
        self.ovirt_engine_password = self.get_option('ovirt_password')
        self.ovirt_engine_cafile = self.get_option('ovirt_cafile')

        query_filter = self._get_query_options(self.get_option('ovirt_query_filter', None))

        cache_key = self.get_cache_key(path)
        source_data = None

        user_cache_setting = self.get_option('cache')
        attempt_to_read_cache = user_cache_setting and cache
        cache_needs_update = user_cache_setting and not cache

        if attempt_to_read_cache:
            try:
                source_data = self._cache[cache_key]
            except KeyError:
                cache_needs_update = True

        if source_data is None:
            source_data = self._query(query_filter=query_filter)

        if cache_needs_update:
            self._cache[cache_key] = source_data

        self._populate_from_source(source_data)
