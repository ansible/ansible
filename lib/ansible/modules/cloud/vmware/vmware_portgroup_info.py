#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
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
module: vmware_portgroup_info
short_description: Gathers info about an ESXi host's Port Group configuration
description:
- This module can be used to gather information about an ESXi host's Port Group configuration when ESXi hostname or Cluster name is given.
version_added: '2.9'
author:
- Abhijeet Kasurde (@Akasurde)
- Christian Kotte (@ckotte)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  policies:
    description:
    - Gather information about Security, Traffic Shaping, as well as Teaming and failover.
    - The property C(ts) stands for Traffic Shaping and C(lb) for Load Balancing.
    type: bool
    default: false
  cluster_name:
    description:
    - Name of the cluster.
    - Info will be returned for all hostsystem belonging to this cluster name.
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
- name: Gather portgroup info about all ESXi Host in given Cluster
  vmware_portgroup_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ cluster_name }}'
  delegate_to: localhost

- name: Gather portgroup info about ESXi Host system
  vmware_portgroup_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
  delegate_to: localhost
'''

RETURN = r'''
hosts_portgroup_info:
    description: metadata about host's portgroup configuration
    returned: on success
    type: dict
    sample: {
        "esx01": [
            {
                "failback": true,
                "failover_active": ["vmnic0", "vmnic1"],
                "failover_standby": [],
                "failure_detection": "link_status_only",
                "lb": "loadbalance_srcid",
                "notify": true,
                "portgroup": "Management Network",
                "security": [false, false, false],
                "ts": "No override",
                "vlan_id": 0,
                "vswitch": "vSwitch0"
            },
            {
                "failback": true,
                "failover_active": ["vmnic2"],
                "failover_standby": ["vmnic3"],
                "failure_detection": "No override",
                "lb": "No override",
                "notify": true,
                "portgroup": "vMotion",
                "security": [false, false, false],
                "ts": "No override",
                "vlan_id": 33,
                "vswitch": "vSwitch1"
            }
        ]
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi


class PortgroupInfoManager(PyVmomi):
    """Class to manage Port Group info"""
    def __init__(self, module):
        super(PortgroupInfoManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        if not self.hosts:
            self.module.fail_json(msg="Failed to find host system.")
        self.policies = self.params.get('policies')

    @staticmethod
    def normalize_pg_info(portgroup_obj, policy_info):
        """Create Port Group information"""
        pg_info_dict = dict()
        spec = portgroup_obj.spec
        pg_info_dict['portgroup'] = spec.name
        pg_info_dict['vlan_id'] = spec.vlanId
        pg_info_dict['vswitch'] = spec.vswitchName

        if policy_info:
            # Security info
            if spec.policy.security:
                promiscuous_mode = spec.policy.security.allowPromiscuous
                mac_changes = spec.policy.security.macChanges
                forged_transmits = spec.policy.security.forgedTransmits
                pg_info_dict['security'] = (
                    ["No override" if promiscuous_mode is None else promiscuous_mode,
                     "No override" if mac_changes is None else mac_changes,
                     "No override" if forged_transmits is None else forged_transmits]
                )
            else:
                pg_info_dict['security'] = ["No override", "No override", "No override"]

            # Traffic Shaping info
            if spec.policy.shapingPolicy and spec.policy.shapingPolicy.enabled is not None:
                pg_info_dict['ts'] = portgroup_obj.spec.policy.shapingPolicy.enabled
            else:
                pg_info_dict['ts'] = "No override"

            # Teaming and failover info
            if spec.policy.nicTeaming:
                if spec.policy.nicTeaming.policy is None:
                    pg_info_dict['lb'] = "No override"
                else:
                    pg_info_dict['lb'] = spec.policy.nicTeaming.policy
                if spec.policy.nicTeaming.notifySwitches is None:
                    pg_info_dict['notify'] = "No override"
                else:
                    pg_info_dict['notify'] = spec.policy.nicTeaming.notifySwitches
                if spec.policy.nicTeaming.rollingOrder is None:
                    pg_info_dict['failback'] = "No override"
                else:
                    pg_info_dict['failback'] = not spec.policy.nicTeaming.rollingOrder
                if spec.policy.nicTeaming.nicOrder is None:
                    pg_info_dict['failover_active'] = "No override"
                    pg_info_dict['failover_standby'] = "No override"
                else:
                    pg_info_dict['failover_active'] = spec.policy.nicTeaming.nicOrder.activeNic
                    pg_info_dict['failover_standby'] = spec.policy.nicTeaming.nicOrder.standbyNic
                if spec.policy.nicTeaming.failureCriteria and spec.policy.nicTeaming.failureCriteria.checkBeacon is None:
                    pg_info_dict['failure_detection'] = "No override"
                else:
                    if spec.policy.nicTeaming.failureCriteria.checkBeacon:
                        pg_info_dict['failure_detection'] = "beacon_probing"
                    else:
                        pg_info_dict['failure_detection'] = "link_status_only"
            else:
                pg_info_dict['lb'] = "No override"
                pg_info_dict['notify'] = "No override"
                pg_info_dict['failback'] = "No override"
                pg_info_dict['failover_active'] = "No override"
                pg_info_dict['failover_standby'] = "No override"
                pg_info_dict['failure_detection'] = "No override"

        return pg_info_dict

    def gather_host_portgroup_info(self):
        """Gather Port Group info per ESXi host"""
        hosts_pg_info = dict()
        for host in self.hosts:
            pgs = host.config.network.portgroup
            hosts_pg_info[host.name] = []
            for portgroup in pgs:
                hosts_pg_info[host.name].append(
                    self.normalize_pg_info(portgroup_obj=portgroup, policy_info=self.policies)
                )
        return hosts_pg_info


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
        policies=dict(type='bool', required=False, default=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ],
        supports_check_mode=True
    )

    host_pg_mgr = PortgroupInfoManager(module)
    module.exit_json(changed=False, hosts_portgroup_info=host_pg_mgr.gather_host_portgroup_info())


if __name__ == "__main__":
    main()
