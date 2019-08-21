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
module: vmware_host_feature_info
short_description: Gathers info about an ESXi host's feature capability information
description:
- This module can be used to gather information about an ESXi host's feature capability information when ESXi hostname or Cluster name is given.
version_added: '2.9'
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
    - Name of the cluster from all host systems to be used for information gathering.
    - If C(esxi_hostname) is not given, this parameter is required.
    type: str
  esxi_hostname:
    description:
    - ESXi hostname to gather information from.
    - If C(cluster_name) is not given, this parameter is required.
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather feature capability info about all ESXi Hosts in given Cluster
  vmware_host_feature_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
  delegate_to: localhost
  register: all_cluster_hosts_info

- name: Check if ESXi is vulnerable for Speculative Store Bypass Disable (SSBD) vulnerability
  vmware_host_feature_info:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    validate_certs: no
    esxi_hostname: "{{ esxi_hostname }}"
  register: features_set
- set_fact:
    ssbd : "{{ item.value }}"
  loop: "{{ features_set.host_feature_info[esxi_hostname] |json_query(name) }}"
  vars:
    name: "[?key=='cpuid.SSBD']"
- assert:
    that:
      - ssbd|int == 1
  when: ssbd is defined
'''

RETURN = r'''
hosts_feature_info:
    description: metadata about host's feature capability information
    returned: always
    type: dict
    sample: {
        "10.76.33.226": [
            {
                "feature_name": "cpuid.3DNOW",
                "key": "cpuid.3DNOW",
                "value": "0"
            },
            {
                "feature_name": "cpuid.3DNOWPLUS",
                "key": "cpuid.3DNOWPLUS",
                "value": "0"
            },
        ]
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi


class FeatureCapabilityInfoManager(PyVmomi):
    def __init__(self, module):
        super(FeatureCapabilityInfoManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)

    def gather_host_feature_info(self):
        host_feature_info = dict()
        for host in self.hosts:
            host_feature_capabilities = host.config.featureCapability
            capability = []
            for fc in host_feature_capabilities:
                temp_dict = {
                    'key': fc.key,
                    'feature_name': fc.featureName,
                    'value': fc.value,
                }
                capability.append(temp_dict)

            host_feature_info[host.name] = capability

        return host_feature_info


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

    host_capability_manager = FeatureCapabilityInfoManager(module)
    module.exit_json(changed=False,
                     hosts_feature_info=host_capability_manager.gather_host_feature_info())


if __name__ == "__main__":
    main()
