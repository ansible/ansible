#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['deprecated'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_host_service_facts
deprecated:
  removed_in: '2.13'
  why: Deprecated in favour of C(_info) module.
  alternative: Use M(vmware_host_service_info) instead.
short_description: Gathers facts about an ESXi host's services
description:
- This module can be used to gather facts about an ESXi host's services.
version_added: '2.5'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
- If source package name is not available then fact is populated as null.
requirements:
- python >= 2.6
- PyVmomi
options:
  cluster_name:
    description:
    - Name of the cluster.
    - Service facts about each ESXi server will be returned for given cluster.
    - If C(esxi_hostname) is not given, this parameter is required.
    type: str
  esxi_hostname:
    description:
    - ESXi hostname.
    - Service facts about this ESXi server will be returned.
    - If C(cluster_name) is not given, this parameter is required.
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather facts about all ESXi Host in given Cluster
  vmware_host_service_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
  delegate_to: localhost
  register: cluster_host_services

- name: Gather facts about ESXi Host
  vmware_host_service_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
  delegate_to: localhost
  register: host_services
'''

RETURN = r'''
host_service_facts:
    description:
    - dict with hostname as key and dict with host service config facts
    returned: always
    type: dict
    sample: {
        "10.76.33.226": [
            {
                "key": "DCUI",
                "label": "Direct Console UI",
                "policy": "on",
                "required": false,
                "running": true,
                "uninstallable": false,
                "source_package_name": "esx-base",
                "source_package_desc": "This VIB contains all of the base functionality of vSphere ESXi."
            },
            {
                "key": "TSM",
                "label": "ESXi Shell",
                "policy": "off",
                "required": false,
                "running": false,
                "uninstallable": false,
                "source_package_name": "esx-base",
                "source_package_desc": "This VIB contains all of the base functionality of vSphere ESXi."
            },
        ]
    }
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
                    host_service_facts.append(
                        dict(
                            key=service.key,
                            label=service.label,
                            required=service.required,
                            uninstallable=service.uninstallable,
                            running=service.running,
                            policy=service.policy,
                            source_package_name=service.sourcePackage.sourcePackageName if service.sourcePackage else None,
                            source_package_desc=service.sourcePackage.description if service.sourcePackage else None,
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
        ],
        supports_check_mode=True,
    )

    vmware_host_service_config = VmwareServiceManager(module)
    module.exit_json(changed=False, host_service_facts=vmware_host_service_config.gather_host_facts())


if __name__ == "__main__":
    main()
