#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_host_ssl_facts
short_description: Gather facts of ESXi host system about SSL
description:
- This module can be used to gather facts of the SSL thumbprint information for a host.
version_added: 2.7
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  cluster_name:
    description:
    - Name of the cluster.
    - SSL thumbprint information about all ESXi host system in the given cluster will be reported.
    - If C(esxi_hostname) is not given, this parameter is required.
  esxi_hostname:
    description:
    - ESXi hostname.
    - SSL thumbprint information of this ESXi host system will be reported.
    - If C(cluster_name) is not given, this parameter is required.
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather SSL thumbprint information about all ESXi Hosts in given Cluster
  vmware_host_ssl_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ cluster_name }}'
  delegate_to: localhost
  register: all_host_ssl_facts

- name: Get SSL Thumbprint info about "{{ esxi_hostname }}"
  vmware_host_ssl_facts:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    esxi_hostname: '{{ esxi_hostname }}'
  register: ssl_facts
- set_fact:
    ssl_thumbprint: "{{ ssl_facts['host_ssl_facts'][esxi_hostname]['ssl_thumbprints'][0] }}"
- debug:
    msg: "{{ ssl_thumbprint }}"
- name: Add ESXi Host to vCenter
  vmware_host:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter_name }}'
    cluster_name: '{{ cluster_name }}'
    esxi_hostname: '{{ esxi_hostname }}'
    esxi_username: '{{ esxi_username }}'
    esxi_password: '{{ esxi_password }}'
    esxi_ssl_thumbprint: '{{ ssl_thumbprint }}'
    state: present
'''

RETURN = r'''
host_ssl_facts:
    description:
    - dict with hostname as key and dict with SSL thumbprint related facts
    returned: facts
    type: dict
    sample:
        {
            "10.76.33.215": {
                "owner_tag": "",
                "principal": "vpxuser",
                "ssl_thumbprints": [
                    "E3:E8:A9:20:8D:32:AE:59:C6:8D:A5:91:B0:20:EF:00:A2:7C:27:EE",
                    "F1:AC:DA:6E:D8:1E:37:36:4A:5C:07:E5:04:0B:87:C8:75:FB:42:01"
                ]
            }
        }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi


class VMwareHostSslManager(PyVmomi):
    def __init__(self, module):
        super(VMwareHostSslManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        self.hosts_facts = {}

    def gather_ssl_facts(self):
        for host in self.hosts:
            self.hosts_facts[host.name] = dict(principal='',
                                               owner_tag='',
                                               ssl_thumbprints=[])

            host_ssl_info_mgr = host.config.sslThumbprintInfo
            if host_ssl_info_mgr:
                self.hosts_facts[host.name]['principal'] = host_ssl_info_mgr.principal
                self.hosts_facts[host.name]['owner_tag'] = host_ssl_info_mgr.ownerTag
                self.hosts_facts[host.name]['ssl_thumbprints'] = [i for i in host_ssl_info_mgr.sslThumbprints]

        self.module.exit_json(changed=False, host_ssl_facts=self.hosts_facts)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str'),
        esxi_hostname=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ],
        supports_check_mode=True,
    )

    vmware_host_accept_config = VMwareHostSslManager(module)
    vmware_host_accept_config.gather_ssl_facts()


if __name__ == "__main__":
    main()
