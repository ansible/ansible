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
module: vmware_host_service_facts
short_description: Gathers facts about an ESXi host's services
description:
- This module can be used to gather facts about an ESXi host's services.
version_added: '2.5'
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
    - Service facts about each ESXi server will be returned for given cluster.
    - If C(esxi_hostname) is not given, this parameter is required.
  esxi_hostname:
    description:
    - ESXi hostname.
    - Service facts about this ESXi server will be returned.
    - If C(cluster_name) is not given, this parameter is required.
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather facts about all ESXi Host in given Cluster
  vmware_host_service_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
  register: cluster_host_services

- name: Gather facts about ESXi Host
  vmware_host_service_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
  register: host_services
'''

RETURN = r'''#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi


class VmwareServiceManager(PyVmomi):
    def __init__(self, module):
        super(VmwareServiceManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)

    def gather_host_facts(self):
        hosts_facts = {}
        for host in self.hosts:
            host_service_facts = []
            host_service_system = host.configManager.serviceSystem
            if host_service_system:
                services = host_service_system.serviceInfo.service
                for service in services:
                    host_service_facts.append(dict(key=service.key,
                                                   label=service.label,
                                                   required=service.required,
                                                   uninstallable=service.uninstallable,
                                                   running=service.running,
                                                   policy=service.policy,
                                                   source_package_name=service.sourcePackage.sourcePackageName,
                                                   source_package_desc=service.sourcePackage.description,
                                                   )
                                              )
            hosts_facts[host.name] = host_service_facts
        return hosts_facts


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ]
    )

    vmware_host_service_config = VmwareServiceManager(module)
    module.exit_json(changed=False, host_service_facts=vmware_host_service_config.gather_host_facts())


if __name__ == "__main__":
    main()
