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
module: vmware_vswitch_facts
deprecated:
  removed_in: '2.13'
  why: Deprecated in favour of C(_info) module.
  alternative: Use M(vmware_vswitch_info) instead.
short_description: Gathers facts about an ESXi host's vswitch configurations
description:
- This module can be used to gather facts about an ESXi host's vswitch configurations when ESXi hostname or Cluster name is given.
- The vSphere Client shows the value for the number of ports as elastic from vSphere 5.5 and above.
- Other tools like esxcli might show the number of ports as 1536 or 5632.
- See U(https://kb.vmware.com/s/article/2064511) for more details.
version_added: '2.6'
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
    - Facts about vswitch belonging to every ESXi host systems under this cluster will be returned.
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
- name: Gather vswitch facts about all ESXi Host in given Cluster
  vmware_vswitch_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ cluster_name }}'
    delegate_to: localhost
  register: all_hosts_vswitch_facts

- name: Gather firewall facts about ESXi Host
  vmware_vswitch_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    delegate_to: localhost
  register: all_vswitch_facts
'''

RETURN = r'''
hosts_vswitch_facts:
    description: metadata about host's vswitch configuration
    returned: on success
    type: dict
    sample: {
        "10.76.33.218": {
            "vSwitch0": {
                "mtu": 1500,
                "num_ports": 128,
                "pnics": [
                    "vmnic0"
                ]
            },
            "vSwitch_0011": {
                "mtu": 1500,
                "num_ports": 128,
                "pnics": [
                    "vmnic2",
                    "vmnic1"
                    ]
            },
        },
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi


class VswitchFactsManager(PyVmomi):
    """Class to gather vSwitch facts"""
    def __init__(self, module):
        super(VswitchFactsManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        if not self.hosts:
            self.module.fail_json(msg="Failed to find host system.")

    @staticmethod
    def serialize_pnics(vswitch_obj):
        """Get pnic names"""
        pnics = []
        for pnic in vswitch_obj.pnic:
            # vSwitch contains all PNICs as string in format of 'key-vim.host.PhysicalNic-vmnic0'
            pnics.append(pnic.split("-", 3)[-1])
        return pnics

    def gather_vswitch_facts(self):
        """Gather vSwitch facts"""
        hosts_vswitch_facts = dict()
        for host in self.hosts:
            network_manager = host.configManager.networkSystem
            if network_manager:
                temp_switch_dict = dict()
                for available_vswitch in network_manager.networkInfo.vswitch:
                    temp_switch_dict[available_vswitch.name] = dict(
                        pnics=self.serialize_pnics(available_vswitch),
                        mtu=available_vswitch.mtu,
                        # we need to use the spec to get the ports
                        # otherwise, the output might be different compared to the vswitch config module
                        # (e.g. 5632 ports instead of 128)
                        num_ports=available_vswitch.spec.numPorts
                    )
                hosts_vswitch_facts[host.name] = temp_switch_dict
        return hosts_vswitch_facts


def main():
    """Main"""
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

    vmware_vswitch_mgr = VswitchFactsManager(module)
    module.exit_json(changed=False, hosts_vswitch_facts=vmware_vswitch_mgr.gather_vswitch_facts())


if __name__ == "__main__":
    main()
