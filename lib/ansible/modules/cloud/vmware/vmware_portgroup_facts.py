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
module: vmware_portgroup_facts
short_description: Gathers facts about an ESXi host's portgroup configuration
description:
- This module can be used to gather facts about an ESXi host's portgroup configuration when ESXi hostname or Cluster name is given.
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
    - Facts will be returned for all hostsystem belonging to this cluster name.
    - If C(esxi_hostname) is not given, this parameter is required.
  esxi_hostname:
    description:
    - ESXi hostname to gather facts from.
    - If C(cluster_name) is not given, this parameter is required.
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather portgroup facts about all ESXi Host in given Cluster
  vmware_portgroup_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name

- name: Gather portgroup facts about ESXi Host system
  vmware_portgroup_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
'''

RETURN = r'''
hosts_firewall_facts:
    description: metadata about host's portgroup configuration
    returned: on success
    type: dict
    sample: {
        "10.76.33.208": [
            {
                "forged_transmits": false,
                "mac_changes": false,
                "name": "VM Network",
                "promiscuous_mode": false,
                "vlan_id": 0,
                "vswitch_name": "vSwitch0"
            },
            {
                "forged_transmits": false,
                "mac_changes": false,
                "name": "Management Network",
                "promiscuous_mode": false,
                "vlan_id": 0,
                "vswitch_name": "vSwitch0"
            },
            {
                "forged_transmits": false,
                "mac_changes": false,
                "name": "pg0001",
                "promiscuous_mode": false,
                "vlan_id": 0,
                "vswitch_name": "vSwitch001"
            },
        ]
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi


class PortgroupFactsManager(PyVmomi):
    def __init__(self, module):
        super(PortgroupFactsManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)

    @staticmethod
    def normalize_pg_info(portgroup_obj):
        pg_info_dict = dict()
        pg_info_dict['name'] = portgroup_obj.spec.name
        vlan_id = 'N/A'
        if portgroup_obj.spec.vlanId:
            vlan_id = portgroup_obj.spec.vlanId
        pg_info_dict['vlan_id'] = vlan_id
        switch_name = 'N/A'
        if portgroup_obj.spec.vswitchName:
            switch_name = portgroup_obj.spec.vswitchName
        pg_info_dict['vswitch_name'] = switch_name

        # Network Policy related facts
        pg_info_dict['promiscuous_mode'] = bool(portgroup_obj.spec.policy.security.allowPromiscuous)
        pg_info_dict['mac_changes'] = bool(portgroup_obj.spec.policy.security.macChanges)
        pg_info_dict['forged_transmits'] = bool(portgroup_obj.spec.policy.security.forgedTransmits)

        return pg_info_dict

    def gather_host_portgroup_facts(self):
        hosts_pg_facts = dict()
        for host in self.hosts:
            pgs = host.config.network.portgroup
            hosts_pg_facts[host.name] = []
            for pg in pgs:
                hosts_pg_facts[host.name].append(self.normalize_pg_info(portgroup_obj=pg))
        return hosts_pg_facts


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

    host_pg_mgr = PortgroupFactsManager(module)
    module.exit_json(changed=False, hosts_portgroup_facts=host_pg_mgr.gather_host_portgroup_facts())


if __name__ == "__main__":
    main()
