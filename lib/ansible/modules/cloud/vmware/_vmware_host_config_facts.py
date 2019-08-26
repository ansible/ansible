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
module: vmware_host_config_facts
deprecated:
  removed_in: '2.13'
  why: Deprecated in favour of C(_info) module.
  alternative: Use M(vmware_host_config_info) instead.
short_description: Gathers facts about an ESXi host's advance configuration information
description:
- This module can be used to gather facts about an ESXi host's advance configuration information when ESXi hostname or Cluster name is given.
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
    - Name of the cluster from which the ESXi host belong to.
    - If C(esxi_hostname) is not given, this parameter is required.
    type: str
  esxi_hostname:
    description:
    - ESXi hostname to gather facts from.
    - If C(cluster_name) is not given, this parameter is required.
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather facts about all ESXi Host in given Cluster
  vmware_host_config_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
  delegate_to: localhost

- name: Gather facts about ESXi Host
  vmware_host_config_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
  delegate_to: localhost
'''

RETURN = r'''
hosts_facts:
    description:
    - dict with hostname as key and dict with host config facts
    returned: always
    type: dict
    sample: {
        "10.76.33.226": {
            "Annotations.WelcomeMessage": "",
            "BufferCache.FlushInterval": 30000,
            "BufferCache.HardMaxDirty": 95,
            "BufferCache.PerFileHardMaxDirty": 50,
            "BufferCache.SoftMaxDirty": 15,
        }
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi


class VmwareConfigFactsManager(PyVmomi):
    def __init__(self, module):
        super(VmwareConfigFactsManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)

    def gather_host_facts(self):
        hosts_facts = {}
        for host in self.hosts:
            host_facts = {}
            for option in host.configManager.advancedOption.QueryOptions():
                host_facts[option.key] = option.value
            hosts_facts[host.name] = host_facts
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
        supports_check_mode=True
    )

    vmware_host_config = VmwareConfigFactsManager(module)
    module.exit_json(changed=False, hosts_facts=vmware_host_config.gather_host_facts())


if __name__ == "__main__":
    main()
