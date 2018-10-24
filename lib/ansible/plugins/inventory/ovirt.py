# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: ovirt
    plugin_type: inventory
    short_description: oVirt inventory source
    requirements:
        - ovirt-engine-sdk-python >= 4.2.5
    extends_documentation_fragment:
        - inventory_cache
        - constructed
    description:
        - Get inventory hosts from oVirt.
        - Groups by cluster_<cluster_name>, tag_<tag_name>, status_<vm_status>, affinity_group_<affinity_group_name>, affinity_label_<affinity_label_name>
        - Uses a YAML configuration file that ends with ovirt.(yml|yaml).
    options:
        plugin:
            description: token that ensures this is a source file for the 'ovirt' plugin.
            required: True
            choices: ['ovirt']
        username:
            description:
                - The name of the user, something like I(admin@internal).
                - Default value is set by I(OVIRT_USERNAME) environment variable.
            required: True
        password:
            description:
                - The password of the user. Default value is set by I(OVIRT_PASSWORD) environment variable."
        url:
            description:
                - A string containing the API URL of the server, usually
                  something like `I(https://server.example.com/ovirt-engine/api)`. Default value is set by I(OVIRT_URL) environment variable.
                  Either C(url) or C(hostname) is required."
        hostname:
            description:
                - A string containing the hostname of the server, usually
                  something like `I(server.example.com)`. Default value is set by I(OVIRT_HOSTNAME) environment variable.
                  Either C(url) or C(hostname) is required."
        token:
            description:
                - Token to be used instead of login with username/password. Default value is set by I(OVIRT_TOKEN) environment variable."
        insecure:
            description:
                - A boolean flag that indicates if the server TLS
                  certificate and host name should be checked."
        ca_file:
            description:
                - A PEM file containing the trusted CA certificates. The
                  certificate presented by the server will be verified using these CA
                  certificates. If `C(ca_file)` parameter is not set, system wide
                  CA certificate store is used. Default value is set by I(OVIRT_CAFILE) environment variable."
                  kerberos - A boolean flag indicating if Kerberos authentication
                  should be used instead of the default basic authentication."
        pattern:
            description:
                - "Search term which is accepted by oVirt/RHV search backend."
                - "For example to search VM X from pattern Y use following pattern:
                   name=X and pattern=Y"
        interface:
            description:
                - "Check if this interface report IP address and if yes return this IP address as host."
                - "By default takes first IP address in list, which is reported by oVirt."
'''

EXAMPLES = '''
# Search for virtual machines in cluster test
plugin: ovirt
pattern: cluster=test

# Search for virtual machines with name starting httpd
plugin: ovirt
pattern: name=httpd*

# Search for virtual machines with from domain example.com
plugin: ovirt
pattern: fqdn=*.example.com

# Search for virtual machines with memory usage more than 90%
plugin: ovirt
pattern: mem_usage>90

# Search for virtual machines in cluster test and return IP address of interface eth0
plugin: ovirt
pattern: cluster=test
interface: eth0
'''

import os

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.six import string_types
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable, to_safe_group_name
try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

try:
    import ovirtsdk4 as sdk
    import ovirtsdk4.types as otypes
except ImportError:
    raise AnsibleError('oVirt inventory script requires ovirt-engine-sdk-python >= 4.2.5')


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'ovirt'

    def __init__(self):
        super(InventoryModule, self).__init__()
        self.group_prefix = 'ovirt_'

        # credentials
        self.username = None
        self.password = None
        self.url = None
        self.insecure = True

    def _get_dev_ipv4(self, vm, interface):
        def get_ipv4(dev):
            return next((ip.address for ip in dev.ips if ip.version == otypes.IpVersion.V4), None)

        for dev in vm.reported_devices or []:
            if dev.type == otypes.ReportedDeviceType.NETWORK and dev.ips:
                if interface:
                    if dev.name == interface:
                        return get_ipv4(dev)
                else:
                    return get_ipv4(dev)

    def _get_instances_by_pattern(self, pattern):
        vms_service = self.connection.system_service().vms_service()
        return [vm for vm in vms_service.list(search=str(pattern), follow='reported_devices') if vm.status == otypes.VmStatus.UP]

    def _query(self, pattern):
        return {'ovirt': self._get_instances_by_pattern(pattern)}

    def _add_host_to_groups(self, vm, vm_ip):
        vm_service = self.connection.system_service().vms_service().vm_service(vm.id)
        cluster_service = self.connection.system_service().clusters_service().cluster_service(vm.cluster.id)

        # Add vm to cluster group:
        cluster_name = self.connection.follow_link(vm.cluster).name
        self.inventory.add_group('cluster_%s' % cluster_name)
        self.inventory.add_host(vm_ip, group='cluster_%s' % cluster_name)

        # Add vm to tag group:
        tags_service = vm_service.tags_service()
        for tag in tags_service.list():
            self.inventory.add_group('tag_%s' % tag.name)
            self.inventory.add_host(vm_ip, group='tag_%s' % tag.name)

        # Add vm to status group:
        self.inventory.add_group('status_%s' % vm.status)
        self.inventory.add_host(vm_ip, group='status_%s' % vm.status)

        # Add vm to affinity group:
        for group in cluster_service.affinity_groups_service().list():
            if vm.name in [
                v.name for v in connection.follow_link(group.vms)
            ]:
                self.inventory.add_group('affinity_group_%s' % group.name)
                self.inventory.add_host(vm_ip, group='affinity_group_%s' % group.name)

        # Add vm to affinity label group:
        affinity_labels_service = vm_service.affinity_labels_service()
        for label in affinity_labels_service.list():
            self.inventory.add_group('affinity_label_%s' % label.name)
            self.inventory.add_host(vm_ip, group='affinity_label_%s' % label.name)

    def _populate(self, groups, interface):
        for group in groups:
            self.inventory.add_group(group)
            for host in groups[group]:
                host_ip = self._get_dev_ipv4(host, interface)
                if host_ip:
                    self.inventory.add_host(host_ip, group=group)
                    self._add_host_to_groups(host, host_ip)       
            self.inventory.add_child('all', group)

    def create_connection(self):
        def get_required_parameter(param, env_var, required=False):
            var = self.get_option(param) or os.environ.get(env_var)
            if not var and required:
                display.warning("'%s' is a required parameter." % param)

            return var

        url = get_required_parameter('url', 'OVIRT_URL', required=False)
        hostname = get_required_parameter('hostname', 'OVIRT_HOSTNAME', required=False)
        if url is None and hostname is None:
            display.warning("You must specify either 'url' or 'hostname'.")

        if url is None and hostname is not None:
            url = 'https://{0}/ovirt-engine/api'.format(hostname)

        username = get_required_parameter('username', 'OVIRT_USERNAME')
        password = get_required_parameter('password', 'OVIRT_PASSWORD')
        token = get_required_parameter('token', 'OVIRT_TOKEN')
        ca_file = get_required_parameter('ca_file', 'OVIRT_CAFILE')
        insecure = self.get_option('insecure') if self.get_option('insecure') is not None else not bool(ca_file)

        return sdk.Connection(
            url=url,
            username=username,
            password=password,
            ca_file=ca_file,
            insecure=insecure,
            token=token,
        )

    def verify_file(self, path):
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('ovirt.yml', 'ovirt.yaml')):
                return True
        display.debug("oVirt inventory filename must end with 'ovirt.yml' or 'ovirt.yaml'")
        return False

    def _get_query_options(self, config_data):
        return config_data.get('pattern', ""), config_data.get('interface', None)

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)

        config_data = self._read_config_data(path)
        self.connection = self.create_connection()

        # Parse filters:
        pattern, interface = self._get_query_options(config_data)

        cache_key = self.get_cache_key(path)
        # false when refresh_cache or --flush-cache is used
        if cache:
            # get the user-specified directive
            cache = self.get_option('cache')

        # Generate inventory
        cache_needs_update = False
        if cache:
            try:
                results = self.cache.get(cache_key)
            except KeyError:
                # if cache expires or cache file doesn't exist
                cache_needs_update = True

        if not cache or cache_needs_update:
            results = self._query(pattern)

        self._populate(results, interface)

        # If the cache has expired/doesn't exist or if refresh_inventory/flush cache is used
        # when the user is using caching, update the cached inventory
        if cache_needs_update or (not cache and self.get_option('cache')):
            self.cache.set(cache_key, results)
