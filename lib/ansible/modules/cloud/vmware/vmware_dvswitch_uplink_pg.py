#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_dvswitch_uplink_pg
short_description: Manage uplink portproup configuration of a Distributed Switch
description:
    - This module can be used to configure the uplink portgroup of a Distributed Switch.
version_added: 2.8
author:
- Christian Kotte (@ckotte)
notes:
    - Tested on vSphere 6.5 and 6.7
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    switch:
        description:
            - The name of the Distributed Switch.
        type: str
        required: True
        aliases: ['dvswitch']
    name:
        description:
            - The name of the uplink portgroup.
            - The current name will be used if not specified.
        type: str
    description:
        description:
            - The description of the uplink portgroup.
        type: str
    advanced:
        description:
            - Dictionary which configures the advanced policy settings for the uplink portgroup.
            - 'Valid attributes are:'
            - '- C(port_config_reset_at_disconnect) (bool): indicates if the configuration of a port is reset automatically after disconnect. (default: true)'
            - '- C(block_override) (bool): indicates if the block policy can be changed per port. (default: true)'
            - '- C(netflow_override) (bool): indicates if the NetFlow policy can be changed per port. (default: false)'
            - '- C(traffic_filter_override) (bool): indicates if the traffic filter can be changed per port. (default: false)'
            - '- C(vendor_config_override) (bool): indicates if the vendor config can be changed per port. (default: false)'
            - '- C(vlan_override) (bool): indicates if the vlan can be changed per port. (default: false)'
        required: False
        default: {
            port_config_reset_at_disconnect: True,
            block_override: True,
            vendor_config_override: False,
            vlan_override: False,
            netflow_override: False,
            traffic_filter_override: False,
        }
        aliases: ['port_policy']
        type: dict
    vlan_trunk_range:
        description:
            - The VLAN trunk range that should be configured with the uplink portgroup.
            - 'This can be a combination of multiple ranges and numbers, example: [ 2-3967, 4049-4092 ].'
        type: list
        default: [ '0-4094' ]
    lacp:
        description:
            - Dictionary which configures the LACP settings for the uplink portgroup.
            - The options are only used if the LACP support mode is set to 'basic'.
            - 'The following parameters are required:'
            - '- C(status) (str): Indicates if LACP is enabled. (default: disabled)'
            - '- C(mode) (str): The negotiating state of the uplinks/ports. (default: passive)'
        required: False
        default: {
            status: 'disabled',
            mode: 'passive',
        }
        type: dict
    netflow_enabled:
        description:
            - Indicates if NetFlow is enabled on the uplink portgroup.
        type: bool
        default: False
    block_all_ports:
        description:
            - Indicates if all ports are blocked on the uplink portgroup.
        type: bool
        default: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Configure Uplink portgroup
  vmware_dvswitch_uplink_pg:
    hostname: '{{ inventory_hostname }}'
    username: '{{ vcsa_username }}'
    password: '{{ vcsa_password }}'
    switch: dvSwitch
    name: dvSwitch-DVUplinks
    advanced:
      port_config_reset_at_disconnect: True
      block_override: True
      vendor_config_override: False
      vlan_override: False
      netflow_override: False
      traffic_filter_override: False
    vlan_trunk_range:
      - '0-4094'
    netflow_enabled: False
    block_all_ports: False
  delegate_to: localhost

- name: Enabled LACP on Uplink portgroup
  vmware_dvswitch_uplink_pg:
    hostname: '{{ inventory_hostname }}'
    username: '{{ vcsa_username }}'
    password: '{{ vcsa_password }}'
    switch: dvSwitch
    lacp:
      status: enabled
      mode: active
  delegate_to: localhost
'''

RETURN = """
result:
    description: information about performed operation
    returned: always
    type: str
    sample: {
        "adv_block_ports": true,
        "adv_netflow": false,
        "adv_reset_at_disconnect": true,
        "adv_traffic_filtering": false,
        "adv_vendor_conf": false,
        "adv_vlan": false,
        "block_all_ports": false,
        "changed": false,
        "description": null,
        "dvswitch": "dvSwitch",
        "lacp_status": "disabled",
        "lacp_status_previous": "enabled",
        "name": "dvSwitch-DVUplinks",
        "netflow_enabled": false,
        "result": "Uplink portgroup already configured properly",
        "vlan_trunk_range": [
            "2-3967",
            "4049-4092"
        ]
    }
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (
    PyVmomi, TaskError, find_dvs_by_name, vmware_argument_spec, wait_for_task
)


class VMwareDvSwitchUplinkPortgroup(PyVmomi):
    """Class to manage a uplink portgroup on a Distributed Virtual Switch"""

    def __init__(self, module):
        super(VMwareDvSwitchUplinkPortgroup, self).__init__(module)
        self.switch_name = self.module.params['switch']
        self.uplink_pg_name = self.params['name']
        self.uplink_pg_description = self.params['description']
        self.uplink_pg_reset = self.params['advanced'].get('port_config_reset_at_disconnect')
        self.uplink_pg_block_ports = self.params['advanced'].get('block_override')
        self.uplink_pg_vendor_conf = self.params['advanced'].get('vendor_config_override')
        self.uplink_pg_vlan = self.params['advanced'].get('vlan_override')
        self.uplink_pg_netflow = self.params['advanced'].get('netflow_override')
        self.uplink_pg_tf = self.params['advanced'].get('traffic_filter_override')
        self.uplink_pg_vlan_trunk_range = self.params['vlan_trunk_range']
        self.uplink_pg_netflow_enabled = self.params['netflow_enabled']
        self.uplink_pg_block_all_ports = self.params['block_all_ports']
        self.lacp_status = self.params['lacp'].get('status')
        self.lacp_mode = self.params['lacp'].get('mode')
        self.dvs = find_dvs_by_name(self.content, self.switch_name)
        if self.dvs is None:
            self.module.fail_json(msg="Failed to find DVS %s" % self.switch_name)
        self.support_mode = self.dvs.config.lacpApiVersion

    def ensure(self):
        """Manage uplink portgroup"""
        changed = changed_uplink_pg_policy = changed_vlan_trunk_range = changed_lacp = False
        results = dict(changed=changed)
        results['dvswitch'] = self.switch_name
        changed_list = []

        uplink_pg_spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
        # Use the same version in the new spec; The version will be increased by one by the API automatically
        uplink_pg_spec.configVersion = self.dvs.config.uplinkPortgroup[0].config.configVersion
        uplink_pg_config = self.dvs.config.uplinkPortgroup[0].config

        # Check name
        if self.uplink_pg_name:
            results['name'] = self.uplink_pg_name
            if uplink_pg_config.name != self.uplink_pg_name:
                changed = True
                changed_list.append("name")
                results['name_previous'] = uplink_pg_config.name
                uplink_pg_spec.name = self.uplink_pg_name
        else:
            results['name'] = uplink_pg_config.name

        # Check description
        results['description'] = self.uplink_pg_description
        if uplink_pg_config.description != self.uplink_pg_description:
            changed = True
            changed_list.append("description")
            results['description_previous'] = uplink_pg_config.description
            uplink_pg_spec.description = self.uplink_pg_description

        # Check port policies
        results['adv_reset_at_disconnect'] = self.uplink_pg_reset
        results['adv_block_ports'] = self.uplink_pg_block_ports
        results['adv_vendor_conf'] = self.uplink_pg_vendor_conf
        results['adv_vlan'] = self.uplink_pg_vlan
        results['adv_netflow'] = self.uplink_pg_netflow
        results['adv_traffic_filtering'] = self.uplink_pg_tf
        uplink_pg_policy_spec = vim.dvs.VmwareDistributedVirtualSwitch.VMwarePortgroupPolicy()
        uplink_pg_policy_spec.portConfigResetAtDisconnect = self.uplink_pg_reset
        uplink_pg_policy_spec.blockOverrideAllowed = self.uplink_pg_block_ports
        uplink_pg_policy_spec.vendorConfigOverrideAllowed = self.uplink_pg_vendor_conf
        uplink_pg_policy_spec.vlanOverrideAllowed = self.uplink_pg_vlan
        uplink_pg_policy_spec.ipfixOverrideAllowed = self.uplink_pg_netflow
        uplink_pg_policy_spec.trafficFilterOverrideAllowed = self.uplink_pg_tf
        # There's no information available if the following option are deprecated, but
        # they aren't visible in the vSphere Client
        uplink_pg_policy_spec.shapingOverrideAllowed = False
        uplink_pg_policy_spec.livePortMovingAllowed = False
        uplink_pg_policy_spec.uplinkTeamingOverrideAllowed = False
        uplink_pg_policy_spec.securityPolicyOverrideAllowed = False
        uplink_pg_policy_spec.networkResourcePoolOverrideAllowed = False
        # Check policies
        if uplink_pg_config.policy.portConfigResetAtDisconnect != self.uplink_pg_reset:
            changed_uplink_pg_policy = True
            results['adv_reset_at_disconnect_previous'] = uplink_pg_config.policy.portConfigResetAtDisconnect
        if uplink_pg_config.policy.blockOverrideAllowed != self.uplink_pg_block_ports:
            changed_uplink_pg_policy = True
            results['adv_block_ports_previous'] = uplink_pg_config.policy.blockOverrideAllowed
        if uplink_pg_config.policy.vendorConfigOverrideAllowed != self.uplink_pg_vendor_conf:
            changed_uplink_pg_policy = True
            results['adv_vendor_conf_previous'] = uplink_pg_config.policy.vendorConfigOverrideAllowed
        if uplink_pg_config.policy.vlanOverrideAllowed != self.uplink_pg_vlan:
            changed_uplink_pg_policy = True
            results['adv_vlan_previous'] = uplink_pg_config.policy.vlanOverrideAllowed
        if uplink_pg_config.policy.ipfixOverrideAllowed != self.uplink_pg_netflow:
            changed_uplink_pg_policy = True
            results['adv_netflow_previous'] = uplink_pg_config.policy.ipfixOverrideAllowed
        if uplink_pg_config.policy.trafficFilterOverrideAllowed != self.uplink_pg_tf:
            changed_uplink_pg_policy = True
            results['adv_traffic_filtering_previous'] = uplink_pg_config.policy.trafficFilterOverrideAllowed
        if changed_uplink_pg_policy:
            changed = True
            changed_list.append("advanced")
            uplink_pg_spec.policy = uplink_pg_policy_spec

        uplink_pg_spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()

        # Check VLAN trunk
        results['vlan_trunk_range'] = self.uplink_pg_vlan_trunk_range
        vlan_id_ranges = self.uplink_pg_vlan_trunk_range
        trunk_vlan_spec = vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec()
        vlan_id_list = []
        for vlan_id_range in vlan_id_ranges:
            vlan_id_range_found = False
            vlan_id_start, vlan_id_end = self.get_vlan_ids_from_range(vlan_id_range)
            # Check if range is already configured
            for current_vlan_id_range in uplink_pg_config.defaultPortConfig.vlan.vlanId:
                if current_vlan_id_range.start == int(vlan_id_start) and current_vlan_id_range.end == int(vlan_id_end):
                    vlan_id_range_found = True
                    break
            if vlan_id_range_found is False:
                changed_vlan_trunk_range = True
            vlan_id_list.append(
                vim.NumericRange(start=int(vlan_id_start), end=int(vlan_id_end))
            )
        # Check if range needs to be removed
        for current_vlan_id_range in uplink_pg_config.defaultPortConfig.vlan.vlanId:
            vlan_id_range_found = False
            for vlan_id_range in vlan_id_ranges:
                vlan_id_start, vlan_id_end = self.get_vlan_ids_from_range(vlan_id_range)
                if (current_vlan_id_range.start == int(vlan_id_start)
                        and current_vlan_id_range.end == int(vlan_id_end)):
                    vlan_id_range_found = True
                    break
            if vlan_id_range_found is False:
                changed_vlan_trunk_range = True
        trunk_vlan_spec.vlanId = vlan_id_list
        if changed_vlan_trunk_range:
            changed = True
            changed_list.append("vlan trunk range")
            current_vlan_id_list = []
            for current_vlan_id_range in uplink_pg_config.defaultPortConfig.vlan.vlanId:
                if current_vlan_id_range.start == current_vlan_id_range.end:
                    current_vlan_id_range_string = current_vlan_id_range.start
                else:
                    current_vlan_id_range_string = '-'.join(
                        [str(current_vlan_id_range.start), str(current_vlan_id_range.end)]
                    )
                current_vlan_id_list.append(current_vlan_id_range_string)
            results['vlan_trunk_range_previous'] = current_vlan_id_list
            uplink_pg_spec.defaultPortConfig.vlan = trunk_vlan_spec

        # Check LACP
        lacp_support_mode = self.get_lacp_support_mode(self.support_mode)
        if lacp_support_mode == 'basic':
            results['lacp_status'] = self.lacp_status
            lacp_spec = vim.dvs.VmwareDistributedVirtualSwitch.UplinkLacpPolicy()
            lacp_enabled = False
            if self.lacp_status == 'enabled':
                lacp_enabled = True
            if uplink_pg_config.defaultPortConfig.lacpPolicy.enable.value != lacp_enabled:
                changed_lacp = True
                changed_list.append("lacp status")
                if uplink_pg_config.defaultPortConfig.lacpPolicy.enable.value:
                    results['lacp_status_previous'] = 'enabled'
                else:
                    results['lacp_status_previous'] = 'disabled'
                lacp_spec.enable = vim.BoolPolicy()
                lacp_spec.enable.inherited = False
                lacp_spec.enable.value = lacp_enabled
            if lacp_enabled and uplink_pg_config.defaultPortConfig.lacpPolicy.mode.value != self.lacp_mode:
                results['lacp_mode'] = self.lacp_mode
                changed_lacp = True
                changed_list.append("lacp mode")
                results['lacp_mode_previous'] = uplink_pg_config.defaultPortConfig.lacpPolicy.mode.value
                lacp_spec.mode = vim.StringPolicy()
                lacp_spec.mode.inherited = False
                lacp_spec.mode.value = self.lacp_mode
            if changed_lacp:
                changed = True
                uplink_pg_spec.defaultPortConfig.lacpPolicy = lacp_spec

        # Check NetFlow
        results['netflow_enabled'] = self.uplink_pg_netflow_enabled
        netflow_enabled_spec = vim.BoolPolicy()
        netflow_enabled_spec.inherited = False
        netflow_enabled_spec.value = self.uplink_pg_netflow_enabled
        if uplink_pg_config.defaultPortConfig.ipfixEnabled.value != self.uplink_pg_netflow_enabled:
            changed = True
            results['netflow_enabled_previous'] = uplink_pg_config.defaultPortConfig.ipfixEnabled.value
            changed_list.append("netflow")
            uplink_pg_spec.defaultPortConfig.ipfixEnabled = netflow_enabled_spec

        # TODO: Check Traffic filtering and marking

        # Check Block all ports
        results['block_all_ports'] = self.uplink_pg_block_all_ports
        block_all_ports_spec = vim.BoolPolicy()
        block_all_ports_spec.inherited = False
        block_all_ports_spec.value = self.uplink_pg_block_all_ports
        if uplink_pg_config.defaultPortConfig.blocked.value != self.uplink_pg_block_all_ports:
            changed = True
            changed_list.append("block all ports")
            results['block_all_ports_previous'] = uplink_pg_config.defaultPortConfig.blocked.value
            uplink_pg_spec.defaultPortConfig.blocked = block_all_ports_spec

        if changed:
            if self.module.check_mode:
                changed_suffix = ' would be changed'
            else:
                changed_suffix = ' changed'
            if len(changed_list) > 2:
                message = ', '.join(changed_list[:-1]) + ', and ' + str(changed_list[-1])
            elif len(changed_list) == 2:
                message = ' and '.join(changed_list)
            elif len(changed_list) == 1:
                message = changed_list[0]
            message += changed_suffix
            if not self.module.check_mode:
                try:
                    task = self.dvs.config.uplinkPortgroup[0].ReconfigureDVPortgroup_Task(uplink_pg_spec)
                    wait_for_task(task)
                except TaskError as invalid_argument:
                    self.module.fail_json(msg="Failed to update uplink portgroup : %s" % to_native(invalid_argument))
        else:
            message = "Uplink portgroup already configured properly"
        results['changed'] = changed
        results['result'] = message

        self.module.exit_json(**results)

    @staticmethod
    def get_vlan_ids_from_range(vlan_id_range):
        """Get start and end VLAN ID from VLAN ID range"""
        try:
            vlan_id_start, vlan_id_end = vlan_id_range.split('-')
        except (AttributeError, TypeError):
            vlan_id_start = vlan_id_end = vlan_id_range
        except ValueError:
            vlan_id_start = vlan_id_end = vlan_id_range.strip()
        return vlan_id_start, vlan_id_end

    @staticmethod
    def get_lacp_support_mode(mode):
        """Get LACP support mode"""
        return_mode = None
        if mode == 'basic':
            return_mode = 'singleLag'
        elif mode == 'enhanced':
            return_mode = 'multipleLag'
        elif mode == 'singleLag':
            return_mode = 'basic'
        elif mode == 'multipleLag':
            return_mode = 'enhanced'
        return return_mode


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            switch=dict(required=True, aliases=['dvswitch']),
            name=dict(type='str'),
            description=dict(type='str'),
            advanced=dict(
                type='dict',
                options=dict(
                    port_config_reset_at_disconnect=dict(type='bool', default=True),
                    block_override=dict(type='bool', default=True),
                    vendor_config_override=dict(type='bool', default=False),
                    vlan_override=dict(type='bool', default=False),
                    netflow_override=dict(type='bool', default=False),
                    traffic_filter_override=dict(type='bool', default=False),
                ),
                default=dict(
                    port_config_reset_at_disconnect=True,
                    block_override=True,
                    vendor_config_override=False,
                    vlan_override=False,
                    netflow_override=False,
                    traffic_filter_override=False,
                ),
                aliases=['port_policy'],
            ),
            lacp=dict(
                type='dict',
                options=dict(
                    status=dict(type='str', choices=['enabled', 'disabled'], default=['disabled']),
                    mode=dict(type='str', choices=['active', 'passive'], default=['passive']),
                ),
                default=dict(
                    status='disabled',
                    mode='passive',
                ),
            ),
            vlan_trunk_range=dict(type='list', default=['0-4094']),
            netflow_enabled=dict(type='bool', default=False),
            block_all_ports=dict(type='bool', default=False),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vmware_dvswitch_uplink_pg = VMwareDvSwitchUplinkPortgroup(module)
    vmware_dvswitch_uplink_pg.ensure()


if __name__ == '__main__':
    main()
