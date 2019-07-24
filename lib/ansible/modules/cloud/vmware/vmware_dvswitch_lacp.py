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
module: vmware_dvswitch_lacp
short_description: Manage LACP configuration on a Distributed Switch
description:
    - This module can be used to configure Link Aggregation Control Protocol (LACP) support mode and Link Aggregation Groups (LAGs).
version_added: 2.8
author:
- Christian Kotte (@ckotte)
notes:
    - Tested on vSphere 6.7
    - You need to run the task two times if you want to remove all LAGs and change the support mode to 'basic'
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    switch:
        description:
            - The name of the Distributed Switch to manage.
        required: True
        aliases: ['dvswitch']
        type: str
    support_mode:
        description:
            - The LACP support mode.
            - 'C(basic): One Link Aggregation Control Protocol group in the switch (singleLag).'
            - 'C(enhanced): Multiple Link Aggregation Control Protocol groups in the switch (multipleLag).'
        type: str
        default: 'basic'
        choices: ['basic', 'enhanced']
    link_aggregation_groups:
        description:
            - Can only be used if C(lacp_support) is set to C(enhanced).
            - 'The following parameters are required:'
            - '- C(name) (string): Name of the LAG.'
            - '- C(uplink_number) (int): Number of uplinks. Can 1 to 30.'
            - '- C(mode) (string): The negotiating state of the uplinks/ports.'
            - '   - choices: [ active, passive ]'
            - '- C(load_balancing_mode) (string): Load balancing algorithm.'
            - '   - Valid attributes are:'
            - '   - srcTcpUdpPort: Source TCP/UDP port number.'
            - '   - srcDestIpTcpUdpPortVlan: Source and destination IP, source and destination TCP/UDP port number and VLAN.'
            - '   - srcIpVlan: Source IP and VLAN.'
            - '   - srcDestTcpUdpPort: Source and destination TCP/UDP port number.'
            - '   - srcMac: Source MAC address.'
            - '   - destIp: Destination IP.'
            - '   - destMac: Destination MAC address.'
            - '   - vlan: VLAN only.'
            - '   - srcDestIp: Source and Destination IP.'
            - '   - srcIpTcpUdpPortVlan: Source IP, TCP/UDP port number and VLAN.'
            - '   - srcDestIpTcpUdpPort: Source and destination IP and TCP/UDP port number.'
            - '   - srcDestMac: Source and destination MAC address.'
            - '   - destIpTcpUdpPort: Destination IP and TCP/UDP port number.'
            - '   - srcPortId: Source Virtual Port Id.'
            - '   - srcIp: Source IP.'
            - '   - srcIpTcpUdpPort: Source IP and TCP/UDP port number.'
            - '   - destIpTcpUdpPortVlan: Destination IP, TCP/UDP port number and VLAN.'
            - '   - destTcpUdpPort: Destination TCP/UDP port number.'
            - '   - destIpVlan: Destination IP and VLAN.'
            - '   - srcDestIpVlan: Source and destination IP and VLAN.'
            - '   - The default load balancing mode in the vSphere Client is srcDestIpTcpUdpPortVlan.'
            - Please see examples for more information.
        type: list
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Enable enhanced mode on a Distributed Switch
  vmware_dvswitch_lacp:
    hostname: '{{ inventory_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    switch: dvSwitch
    support_mode: enhanced
    validate_certs: "{{ validate_vcenter_certs }}"
  delegate_to: localhost
  loop_control:
    label: "{{ item.name }}"
  with_items: "{{ vcenter_distributed_switches }}"

- name: Enable enhanced mode and create two LAGs on a Distributed Switch
  vmware_dvswitch_lacp:
    hostname: '{{ inventory_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    switch: dvSwitch
    support_mode: enhanced
    link_aggregation_groups:
        - name: lag1
          uplink_number: 2
          mode: active
          load_balancing_mode: srcDestIpTcpUdpPortVlan
        - name: lag2
          uplink_number: 2
          mode: passive
          load_balancing_mode: srcDestIp
    validate_certs: "{{ validate_vcenter_certs }}"
  delegate_to: localhost
  loop_control:
    label: "{{ item.name }}"
  with_items: "{{ vcenter_distributed_switches }}"
'''

RETURN = """
result:
    description: information about performed operation
    returned: always
    type: str
    sample: {
        "changed": true,
        "dvswitch": "dvSwitch",
        "link_aggregation_groups": [
            {"load_balancing_mode": "srcDestIpTcpUdpPortVlan", "mode": "active", "name": "lag1", "uplink_number": 2},
            {"load_balancing_mode": "srcDestIp", "mode": "active", "name": "lag2", "uplink_number": 2}
        ],
        "link_aggregation_groups_previous": [],
        "support_mode": "enhanced",
        "result": "lacp lags changed"
    }
"""

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (
    PyVmomi, TaskError, find_dvs_by_name, vmware_argument_spec, wait_for_task
)


class VMwareDvSwitchLacp(PyVmomi):
    """Class to manage a LACP on a Distributed Virtual Switch"""
    def __init__(self, module):
        super(VMwareDvSwitchLacp, self).__init__(module)
        self.switch_name = self.module.params['switch']
        self.support_mode = self.module.params['support_mode']
        self.link_aggregation_groups = self.module.params['link_aggregation_groups']
        if self.support_mode == 'basic' and (
                self.link_aggregation_groups and not (
                    len(self.link_aggregation_groups) == 1 and self.link_aggregation_groups[0] == '')):
            self.module.fail_json(
                msg="LAGs can only be configured if 'support_mode' is set to 'enhanced'!"
            )
        self.dvs = find_dvs_by_name(self.content, self.switch_name)
        if self.dvs is None:
            self.module.fail_json(msg="Failed to find DVS %s" % self.switch_name)

    def ensure(self):
        """Manage LACP configuration"""
        changed = changed_support_mode = changed_lags = False
        results = dict(changed=changed)
        results['dvswitch'] = self.switch_name
        changed_list = []

        spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec()
        spec.configVersion = self.dvs.config.configVersion

        # Check support mode
        results['support_mode'] = self.support_mode
        lacp_support_mode = self.get_lacp_support_mode(self.support_mode)
        if self.dvs.config.lacpApiVersion != lacp_support_mode:
            changed = changed_support_mode = True
            changed_list.append("support mode")
            results['support_mode_previous'] = self.get_lacp_support_mode(self.dvs.config.lacpApiVersion)
            spec.lacpApiVersion = lacp_support_mode

        # Check LAGs
        results['link_aggregation_groups'] = self.link_aggregation_groups
        if self.link_aggregation_groups and not (
                len(self.link_aggregation_groups) == 1 and self.link_aggregation_groups[0] == ''):
            if self.dvs.config.lacpGroupConfig:
                lacp_lag_list = []
                # Check if desired LAGs are configured
                for lag in self.link_aggregation_groups:
                    lag_name, lag_mode, lag_uplink_number, lag_load_balancing_mode = self.get_lacp_lag_options(lag)
                    lag_found = False
                    for lacp_group in self.dvs.config.lacpGroupConfig:
                        if lacp_group.name == lag_name:
                            lag_found = True
                            if (lag_mode != lacp_group.mode or
                                    lag_uplink_number != lacp_group.uplinkNum or
                                    lag_load_balancing_mode != lacp_group.loadbalanceAlgorithm):
                                changed = changed_lags = True
                                lacp_lag_list.append(
                                    self.create_lacp_group_spec(
                                        'edit',
                                        lacp_group.key, lag_name, lag_uplink_number, lag_mode, lag_load_balancing_mode
                                    )
                                )
                            break
                    if lag_found is False:
                        changed = changed_lags = True
                        lacp_lag_list.append(
                            self.create_lacp_group_spec(
                                'add', None, lag_name, lag_uplink_number, lag_mode, lag_load_balancing_mode
                            )
                        )
                # Check if LAGs need to be removed
                for lacp_group in self.dvs.config.lacpGroupConfig:
                    lag_found = False
                    for lag in self.link_aggregation_groups:
                        result = self.get_lacp_lag_options(lag)
                        if lacp_group.name == result[0]:
                            lag_found = True
                            break
                    if lag_found is False:
                        changed = changed_lags = True
                        lacp_lag_list.append(
                            self.create_lacp_group_spec('remove', lacp_group.key, lacp_group.name, None, None, None)
                        )
            else:
                changed = changed_lags = True
                lacp_lag_list = []
                for lag in self.link_aggregation_groups:
                    lag_name, lag_mode, lag_uplink_number, lag_load_balancing_mode = self.get_lacp_lag_options(lag)
                    lacp_lag_list.append(
                        self.create_lacp_group_spec(
                            'add', None, lag_name, lag_uplink_number, lag_mode, lag_load_balancing_mode
                        )
                    )
        else:
            if self.dvs.config.lacpGroupConfig:
                changed = changed_lags = True
                lacp_lag_list = []
                for lacp_group in self.dvs.config.lacpGroupConfig:
                    lacp_lag_list.append(
                        self.create_lacp_group_spec('remove', lacp_group.key, lacp_group.name, None, None, None)
                    )
        if changed_lags:
            changed_list.append("link aggregation groups")
            current_lags_list = []
            for lacp_group in self.dvs.config.lacpGroupConfig:
                temp_lag = dict()
                temp_lag['name'] = lacp_group.name
                temp_lag['uplink_number'] = lacp_group.uplinkNum
                temp_lag['mode'] = lacp_group.mode
                temp_lag['load_balancing_mode'] = lacp_group.loadbalanceAlgorithm
                current_lags_list.append(temp_lag)
            results['link_aggregation_groups_previous'] = current_lags_list

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
                if changed_support_mode and self.support_mode == 'basic' and changed_lags:
                    self.update_lacp_group_config(self.dvs, lacp_lag_list)
                    # NOTE: You need to run the task again to change the support mode to 'basic' as well
                    # No matter how long you sleep, you will always get the following error in vCenter:
                    # 'Cannot complete operation due to concurrent modification by another operation.'
                    # self.update_dvs_config(self.dvs, spec)
                else:
                    if changed_support_mode:
                        self.update_dvs_config(self.dvs, spec)
                    if changed_lags:
                        self.update_lacp_group_config(self.dvs, lacp_lag_list)
        else:
            message = "LACP already configured properly"
        results['changed'] = changed
        results['result'] = message

        self.module.exit_json(**results)

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

    def get_lacp_lag_options(self, lag):
        """Get and check LACP LAG options"""
        lag_name = lag.get('name', None)
        if lag_name is None:
            self.module.fail_json(msg="Please specify name in lag options as it's a required parameter")
        lag_mode = lag.get('mode', None)
        if lag_mode is None:
            self.module.fail_json(msg="Please specify mode in lag options as it's a required parameter")
        lag_uplink_number = lag.get('uplink_number', None)
        if lag_uplink_number is None:
            self.module.fail_json(msg="Please specify uplink_number in lag options as it's a required parameter")
        elif lag_uplink_number > 30:
            self.module.fail_json(msg="More than 30 uplinks are not supported in a single LAG!")
        lag_load_balancing_mode = lag.get('load_balancing_mode', None)
        supported_lb_modes = ['srcTcpUdpPort', 'srcDestIpTcpUdpPortVlan', 'srcIpVlan', 'srcDestTcpUdpPort',
                              'srcMac', 'destIp', 'destMac', 'vlan', 'srcDestIp', 'srcIpTcpUdpPortVlan',
                              'srcDestIpTcpUdpPort', 'srcDestMac', 'destIpTcpUdpPort', 'srcPortId', 'srcIp',
                              'srcIpTcpUdpPort', 'destIpTcpUdpPortVlan', 'destTcpUdpPort', 'destIpVlan', 'srcDestIpVlan']
        if lag_load_balancing_mode is None:
            self.module.fail_json(msg="Please specify load_balancing_mode in lag options as it's a required parameter")
        elif lag_load_balancing_mode not in supported_lb_modes:
            self.module.fail_json(msg="The specified load balancing mode '%s' isn't supported!" % lag_load_balancing_mode)
        return lag_name, lag_mode, lag_uplink_number, lag_load_balancing_mode

    @staticmethod
    def create_lacp_group_spec(operation, key, name, uplink_number, mode, load_balancing_mode):
        """
            Create LACP group spec
            operation: add, edit, or remove
            Returns: LACP group spec
        """
        lacp_spec = vim.dvs.VmwareDistributedVirtualSwitch.LacpGroupSpec()
        lacp_spec.operation = operation
        lacp_spec.lacpGroupConfig = vim.dvs.VmwareDistributedVirtualSwitch.LacpGroupConfig()
        lacp_spec.lacpGroupConfig.name = name
        if operation in ('edit', 'remove'):
            lacp_spec.lacpGroupConfig.key = key
        if not operation == 'remove':
            lacp_spec.lacpGroupConfig.uplinkNum = uplink_number
            lacp_spec.lacpGroupConfig.mode = mode
            lacp_spec.lacpGroupConfig.loadbalanceAlgorithm = load_balancing_mode
        # greyed out in vSphere Client!?
        # lacp_spec.vlan = vim.dvs.VmwareDistributedVirtualSwitch.LagVlanConfig()
        # lacp_spec.vlan.vlanId = [vim.NumericRange(...)]
        # lacp_spec.ipfix = vim.dvs.VmwareDistributedVirtualSwitch.LagIpfixConfig()
        # lacp_spec.ipfix.ipfixEnabled = True/False
        return lacp_spec

    def update_dvs_config(self, switch_object, spec):
        """Update DVS config"""
        try:
            task = switch_object.ReconfigureDvs_Task(spec)
            result = wait_for_task(task)
        except TaskError as invalid_argument:
            self.module.fail_json(
                msg="Failed to update DVS : %s" % to_native(invalid_argument)
            )
        return result

    def update_lacp_group_config(self, switch_object, lacp_group_spec):
        """Update LACP group config"""
        try:
            task = switch_object.UpdateDVSLacpGroupConfig_Task(lacpGroupSpec=lacp_group_spec)
            result = wait_for_task(task)
        except vim.fault.DvsFault as dvs_fault:
            self.module.fail_json(msg="Update failed due to DVS fault : %s" % to_native(dvs_fault))
        except vmodl.fault.NotSupported as not_supported:
            self.module.fail_json(
                msg="Multiple Link Aggregation Control Protocol groups not supported on the switch : %s" %
                to_native(not_supported)
            )
        except TaskError as invalid_argument:
            self.module.fail_json(
                msg="Failed to update Link Aggregation Group : %s" % to_native(invalid_argument)
            )
        return result


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            switch=dict(required=True, aliases=['dvswitch']),
            support_mode=dict(default='basic', choices=['basic', 'enhanced']),
            link_aggregation_groups=dict(default=[], type='list'),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vmware_dvswitch_lacp = VMwareDvSwitchLacp(module)
    vmware_dvswitch_lacp.ensure()


if __name__ == '__main__':
    main()
