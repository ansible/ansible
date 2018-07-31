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
module: vmware_host_vmnic_facts
short_description: Gathers facts about vmnics available on the given ESXi host
description:
- This module can be used to gather facts about vmnics available on the given ESXi host.
- If C(cluster_name) is provided, then vmnic facts about all hosts from given cluster will be returned.
- If C(esxi_hostname) is provided, then vmnic facts about given host system will be returned.
- Additional details about vswitch and dvswitch with respective vmnic is also provided which is added in 2.7 version.
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
    - Vmnic facts about each ESXi server will be returned for the given cluster.
    - If C(esxi_hostname) is not given, this parameter is required.
  esxi_hostname:
    description:
    - ESXi hostname.
    - Vmnic facts about this ESXi server will be returned.
    - If C(cluster_name) is not given, this parameter is required.
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather facts about vmnics of all ESXi Host in the given Cluster
  vmware_host_vmnic_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
  register: cluster_host_vmnics

- name: Gather facts about vmnics of an ESXi Host
  vmware_host_vmnic_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
  register: host_vmnics
'''

RETURN = r'''
hosts_vmnics_facts:
    description:
    - dict with hostname as key and dict with vmnics facts as value.
    - details about vswitch and dvswitch is added in version 2.7.
    returned: hosts_vmnics_facts
    type: dict
    sample:
        {
            "10.76.33.204": {
                "all": [
                    "vmnic0",
                    "vmnic1"
                ],
                "available": [],
                "dvswitch": {
                    "dvs_0002": [
                        "vmnic1"
                    ]
                },
                "used": [
                    "vmnic1",
                    "vmnic0"
                ],
                "vswitch": {
                    "vSwitch0": [
                        "vmnic0"
                    ]
                }
            }
        }
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi, get_all_objs


class HostVmnicMgr(PyVmomi):
    def __init__(self, module):
        super(HostVmnicMgr, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)

    def find_dvs_by_uuid(self, uuid=None):
        dvs_obj = None
        if uuid is None:
            return dvs_obj

        dvswitches = get_all_objs(self.content, [vim.DistributedVirtualSwitch])
        for dvs in dvswitches:
            if dvs.uuid == uuid:
                dvs_obj = dvs
                break

        return dvs_obj

    def gather_host_vmnic_facts(self):
        hosts_vmnic_facts = {}
        for host in self.hosts:
            host_vmnic_facts = dict(all=[], available=[], used=[], vswitch=dict(), dvswitch=dict())
            host_nw_system = host.configManager.networkSystem
            if host_nw_system:
                nw_config = host_nw_system.networkConfig
                host_vmnic_facts['all'] = [pnic.device for pnic in nw_config.pnic]

                vswitch_vmnics = []
                proxy_switch_vmnics = []
                if nw_config.vswitch:
                    for vswitch in nw_config.vswitch:
                        host_vmnic_facts['vswitch'][vswitch.name] = []
                        for vnic in vswitch.spec.bridge.nicDevice:
                            vswitch_vmnics.append(vnic)
                            host_vmnic_facts['vswitch'][vswitch.name].append(vnic)

                if nw_config.proxySwitch:
                    for proxy_config in nw_config.proxySwitch:
                        dvs_obj = self.find_dvs_by_uuid(uuid=proxy_config.uuid)
                        if dvs_obj:
                            host_vmnic_facts['dvswitch'][dvs_obj.name] = []
                        for proxy_nic in proxy_config.spec.backing.pnicSpec:
                            proxy_switch_vmnics.append(proxy_nic.pnicDevice)
                            if dvs_obj:
                                host_vmnic_facts['dvswitch'][dvs_obj.name].append(proxy_nic.pnicDevice)

                used_vmics = proxy_switch_vmnics + vswitch_vmnics
                host_vmnic_facts['used'] = used_vmics
                host_vmnic_facts['available'] = [pnic.device for pnic in nw_config.pnic if pnic.device not in used_vmics]

            hosts_vmnic_facts[host.name] = host_vmnic_facts
        return hosts_vmnic_facts


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

    host_vmnic_mgr = HostVmnicMgr(module)
    module.exit_json(changed=False, hosts_vmnics_facts=host_vmnic_mgr.gather_host_vmnic_facts())


if __name__ == "__main__":
    main()
