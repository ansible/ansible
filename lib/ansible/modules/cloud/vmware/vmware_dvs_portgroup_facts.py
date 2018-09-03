#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
module: vmware_dvs_portgroup_facts
short_description: Gathers facts DVS portgroup configurations
description:
- This module can be used to gather facts about DVS portgroup configurations.
version_added: 2.8
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  datacenter:
    description:
    - Name of the datacenter.
    required: true
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather DVS portgroup facts
  vmware_dvs_portgroup_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
  delegate_to: localhost
'''

RETURN = r'''
dvs_portgroup_facts:
    description: metadata about DVS portgroup configuration
    returned: on success
    type: dict
    sample: {
        "dvs_0": {
            "dvpg_01": {
                "description": null,
                "dvswitch_name": "dvs_0",
                "network_policy": {
                    "forged_transmits": false,
                    "mac_changes": false,
                    "promiscuous": false
                },
                "num_ports": 8,
                "port_policy": {
                    "block_override": true,
                    "ipfix_override": false,
                    "live_port_move": false,
                    "network_rp_override": false,
                    "port_config_reset_at_disconnect": true,
                    "security_override": false,
                    "shaping_override": false,
                    "traffic_filter_override": false,
                    "uplink_teaming_override": false,
                    "vendor_config_override": false,
                    "vlan_override": false
                },
                "teaming_policy": {
                    "inbound_policy": true,
                    "notify_switches": true,
                    "policy": "loadbalance_srcid",
                    "rolling_order": false
                },
                "type": "earlyBinding"
            }
        }
    }
'''

try:
    from pyVmomi import vim
except ImportError as e:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi, get_all_objs


class DVSPortgroupFactsManager(PyVmomi):
    def __init__(self, module):
        super(DVSPortgroupFactsManager, self).__init__(module)
        self.dc_name = self.params['datacenter']

    def gather_dvs_portgroup_facts(self):
        datacenter = self.find_datacenter_by_name(self.dc_name)
        if datacenter is None:
            self.module.fail_json(msg="Failed to find the datacenter %s" % self.dc_name)

        dvs_lists = get_all_objs(self.content, [vim.DistributedVirtualSwitch], folder=datacenter.networkFolder)

        result = dict()
        for dvs in dvs_lists:
            result[dvs.name] = dict()
            for dvs_pg in dvs.portgroup:
                network_policy = dict()
                if dvs_pg.config.defaultPortConfig.securityPolicy:
                    network_policy = dict(
                        forged_transmits=dvs_pg.config.defaultPortConfig.securityPolicy.forgedTransmits.value,
                        promiscuous=dvs_pg.config.defaultPortConfig.securityPolicy.allowPromiscuous.value,
                        mac_changes=dvs_pg.config.defaultPortConfig.securityPolicy.macChanges.value
                    )
                result[dvs.name][dvs_pg.name] = dict(
                    num_ports=dvs_pg.config.numPorts,
                    dvswitch_name=dvs_pg.config.distributedVirtualSwitch.name,
                    description=dvs_pg.config.description,
                    type=dvs_pg.config.type,
                    teaming_policy=dict(
                        policy=dvs_pg.config.defaultPortConfig.uplinkTeamingPolicy.policy.value,
                        inbound_policy=dvs_pg.config.defaultPortConfig.uplinkTeamingPolicy.reversePolicy.value,
                        notify_switches=dvs_pg.config.defaultPortConfig.uplinkTeamingPolicy.notifySwitches.value,
                        rolling_order=dvs_pg.config.defaultPortConfig.uplinkTeamingPolicy.rollingOrder.value,
                    ),
                    port_policy=dict(
                        block_override=dvs_pg.config.policy.blockOverrideAllowed,
                        ipfix_override=dvs_pg.config.policy.ipfixOverrideAllowed,
                        live_port_move=dvs_pg.config.policy.livePortMovingAllowed,
                        network_rp_override=dvs_pg.config.policy.networkResourcePoolOverrideAllowed,
                        port_config_reset_at_disconnect=dvs_pg.config.policy.portConfigResetAtDisconnect,
                        security_override=dvs_pg.config.policy.securityPolicyOverrideAllowed,
                        shaping_override=dvs_pg.config.policy.shapingOverrideAllowed,
                        traffic_filter_override=dvs_pg.config.policy.trafficFilterOverrideAllowed,
                        uplink_teaming_override=dvs_pg.config.policy.uplinkTeamingOverrideAllowed,
                        vendor_config_override=dvs_pg.config.policy.vendorConfigOverrideAllowed,
                        vlan_override=dvs_pg.config.policy.vlanOverrideAllowed
                    ),
                    network_policy=network_policy,
                )
        return result


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        datacenter=dict(type='str', required=True)
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    dvs_pg_mgr = DVSPortgroupFactsManager(module)
    module.exit_json(changed=False,
                     dvs_portgroup_facts=dvs_pg_mgr.gather_dvs_portgroup_facts())


if __name__ == "__main__":
    main()
