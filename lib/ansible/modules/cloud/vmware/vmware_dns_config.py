#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_dns_config
short_description: Manage VMware ESXi DNS Configuration
description:
    - Manage VMware ESXi DNS Configuration
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
- Ryan Butler (@ryan_c_butler)
notes:
    - Tested on vSphere 6.0
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    change_hostname_to:
        description:
            - The hostname that an ESXi host should be changed to.
        required: False
    domainname:
        description:
            - The domain the ESXi host should be apart of.
        required: False
    dns_servers:
        description:
            - The DNS servers that the host should be configured to use.
        required: False
    search_domain:
        description:
            - Where to look for hosts
        required: False
    dhcp:
        description:
            - Obtain DNS server address via DHCP (true or false)
        required: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Configure cluster DNS servers, host domain and search domains
  vmware_dns_config:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ vcenter_cluster }}'
    validate_certs: no
    domainname: foo.org
    search_domain:
        - foo.org
        - subdomain.foo.org
    dns_servers:
        - 8.8.8.8
        - 8.8.44
  delegate_to: localhost

- name: Configure ESXi hostname and DNS servers (MUST USE esxi_hostname)
  vmware_dns_config:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    validate_certs: no
    change_hostname_to: esxihost01
    dns_servers:
        - 8.8.8.8
        - 8.8.4.4
  delegate_to: localhost
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
from ansible.module_utils._text import to_native


class VmwareDNSConfig(PyVmomi):
    def __init__(self, module):
        super(VmwareDNSConfig, self).__init__(module)
        self.cluster_name = self.params.get('cluster_name', None)
        self.esxi_host_name = self.params.get('esxi_hostname', None)
        self.dns_servers = self.params.get('dns_servers', list())
        self.search_domain = self.params.get('search_domain', list())
        self.dhcp = self.params.get('dhcp', None)
        self.change_hostname_to = self.params.get('change_hostname_to', None)
        self.domainname = self.params.get('domainname', None)
        self.hosts = self.get_all_host_objs(cluster_name=self.cluster_name, esxi_host_name=self.esxi_host_name)
        self.results = {}

    def check_host_state(self):
        change_list = []
        changed = False
        for host in self.hosts:
            self.results[host.name] = {}
            if self.dns_servers:
                if len(self.dns_servers) != 0:
                    dns_servers_to_change = self.check_dns_servers(host=host)
                    if dns_servers_to_change != 'good':
                        changed = self.update_dns_servers(host=host, dns_servers=self.dns_servers)
                        change_list.append(changed)
            if self.search_domain:
                if len(self.search_domain) != 0:
                    searchdomain_to_change = self.check_dns_searchdomain(host=host)
                    if searchdomain_to_change != 'good':
                        changed = self.update_dns_searchdomain(host=host, search_domain=self.search_domain)
                        change_list.append(changed)
            if self.change_hostname_to:
                if self.esxi_host_name:
                    hostname_to_change = self.check_dns_hostname(host=host)
                    if hostname_to_change != 'good':
                        changed = self.update_dns_hostname(host=host, host_name=self.change_hostname_to)
                        change_list.append(changed)
            if self.domainname:
                domainname_to_change = self.check_dns_domainname(host=host)
                if domainname_to_change != 'good':
                    changed = self.update_dns_domainname(host=host, domainname=self.domainname)
                    change_list.append(changed)
            if self.dhcp:
                dhcp_to_change = self.check_dns_dhcp(host=host)
                if dhcp_to_change != 'good':
                    changed = self.update_dns_dhcp(host=host, dhcp=self.dhcp)
                    change_list.append(changed)

        if any(change_list):
            changed = True

        self.module.exit_json(changed=changed, results=self.results)

    def check_dns_servers(self, host):
        dns_config = host.configManager.networkSystem.dnsConfig
        if dns_config:
            if dns_config.address == self.dns_servers:
                return 'good'
        self.results[host.name]['before_change_dns_server'] = dns_config.address

        return dns_config.address

    def update_dns_servers(self, host, dns_servers):
        changed = False
        dns_config = host.configManager.networkSystem.dnsConfig
        try:
            dns_config.address = dns_servers
            self.results[host.name]['after_change_dns_server'] = dns_servers
            changed = True
            host_network_system = host.configManager.networkSystem
            host_network_system.UpdateDnsConfig(dns_config)
        except vim.fault.HostConfigFault as e:
            self.results[host.name]['error'] = to_native(e.msg)
        except Exception as e:
            self.results[host.name]['error'] = to_native(e)

        return changed

    def check_dns_domainname(self, host):
        dns_config = host.configManager.networkSystem.dnsConfig
        if dns_config:
            if dns_config.domainName == self.domainname:
                return 'good'
            self.results[host.name]['before_change_domain_name'] = dns_config.domainName

        return dns_config.domainName

    def update_dns_domainname(self, host, domainname):
        changed = False
        dns_config = host.configManager.networkSystem.dnsConfig
        try:
            dns_config.domainName = domainname
            self.results[host.name]['after_change_domain_name'] = domainname
            changed = True
            host_network_system = host.configManager.networkSystem
            host_network_system.UpdateDnsConfig(dns_config)
        except vim.fault.HostConfigFault as e:
            self.results[host.name]['error'] = to_native(e.msg)
        except Exception as e:
            self.results[host.name]['error'] = to_native(e)
        return changed

    def update_dns_hostname(self, host, host_name):
        changed = False
        dns_config = host.configManager.networkSystem.dnsConfig
        try:
            dns_config.hostName = host_name
            self.results[host.name]['after_change_host_name'] = host_name
            changed = True
            host_network_system = host.configManager.networkSystem
            host_network_system.UpdateDnsConfig(dns_config)
        except vim.fault.HostConfigFault as e:
            self.results[host.name]['error'] = to_native(e.msg)
        except Exception as e:
            self.results[host.name]['error'] = to_native(e)
        return changed

    def check_dns_hostname(self, host):
        dns_config = host.configManager.networkSystem.dnsConfig
        if dns_config:
            if dns_config.hostName == self.change_hostname_to:
                return 'good'
        self.results[host.name]['before_change_host_name'] = dns_config.hostName
        return dns_config.hostName

    def check_dns_searchdomain(self, host):
        dns_config = host.configManager.networkSystem.dnsConfig
        if dns_config:
            if dns_config.searchDomain == self.search_domain:
                return 'good'
        self.results[host.name]['before_change_search_domain'] = dns_config.searchDomain

        return dns_config.searchDomain

    def update_dns_searchdomain(self, host, search_domain):
        changed = False
        dns_config = host.configManager.networkSystem.dnsConfig
        try:
            dns_config.searchDomain = search_domain
            self.results[host.name]['after_change_search_domain'] = search_domain
            changed = True
            host_network_system = host.configManager.networkSystem
            host_network_system.UpdateDnsConfig(dns_config)
        except vim.fault.HostConfigFault as e:
            self.results[host.name]['error'] = to_native(e.msg)
        except Exception as e:
            self.results[host.name]['error'] = to_native(e)
        return changed

    def check_dns_dhcp(self, host):
        dns_config = host.configManager.networkSystem.dnsConfig
        print(dns_config)
        if dns_config:
            if dns_config.dhcp == self.dhcp:
                return 'good'
        self.results[host.name]['before_change_dhcp'] = dns_config.dhcp
        return dns_config.dhcp

    def update_dns_dhcp(self, host, dhcp):
        changed = False
        dns_config = host.configManager.networkSystem.dnsConfig
        try:
            dns_config.dhcp = dhcp
            self.results[host.name]['after_change_dhcp'] = dhcp
            changed = True
            host_network_system = host.configManager.networkSystem
            host_network_system.UpdateDnsConfig(dns_config)
        except vim.fault.HostConfigFault as e:
            self.results[host.name]['error'] = to_native(e.msg)
        except Exception as e:
            self.results[host.name]['error'] = to_native(e)
        return changed


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str'),
        esxi_hostname=dict(type='str'),
        change_hostname_to=dict(type='str'),
        dhcp=dict(type='str', choices=['true', 'false']),
        domainname=dict(type='str'),
        dns_servers=dict(type='list'),
        search_domain=dict(type='list')
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['cluster_name', 'esxi_hostname']
        ],
        mutually_exclusive=[
            ['cluster_name', 'host_name'],
            ['dhcp', 'dns_servers']
        ]
    )

    vmware_dns_config = VmwareDNSConfig(module)
    vmware_dns_config.check_host_state()


if __name__ == '__main__':
    main()
