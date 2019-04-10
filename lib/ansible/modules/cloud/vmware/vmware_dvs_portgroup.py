#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2017-2018, Ansible Project
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
module: vmware_dvs_portgroup
short_description: Create or remove a Distributed vSwitch portgroup.
description:
    - Create or remove a Distributed vSwitch portgroup.
version_added: 2.0
author:
    - Joseph Callen (@jcpowermac)
    - Philippe Dellaert (@pdellaert) <philippe@dellaert.org>
notes:
    - Tested on vSphere 5.5
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    portgroup_name:
        description:
            - The name of the portgroup that is to be created or deleted.
        required: True
    switch_name:
        description:
            - The name of the distributed vSwitch the port group should be created on.
        required: True
    vlan_id:
        description:
            - The VLAN ID that should be configured with the portgroup, use 0 for no VLAN.
            - 'If C(vlan_trunk) is configured to be I(true), this can be a combination of multiple ranges and numbers, example: 1-200, 205, 400-4094.'
            - The valid C(vlan_id) range is from 0 to 4094. Overlapping ranges are allowed.
        required: True
    num_ports:
        description:
            - The number of ports the portgroup should contain.
        required: True
    portgroup_type:
        description:
            - See VMware KB 1022312 regarding portgroup types.
        required: True
        choices:
            - 'earlyBinding'
            - 'lateBinding'
            - 'ephemeral'
    state:
        description:
            - Determines if the portgroup should be present or not.
        required: True
        type: str
        choices:
            - 'present'
            - 'absent'
        version_added: '2.5'
    vlan_trunk:
        description:
            - Indicates whether this is a VLAN trunk or not.
        required: False
        default: False
        type: bool
        version_added: '2.5'
    network_policy:
        description:
            - Dictionary which configures the different security values for portgroup.
            - 'Valid attributes are:'
            - '- C(promiscuous) (bool): indicates whether promiscuous mode is allowed. (default: false)'
            - '- C(forged_transmits) (bool): indicates whether forged transmits are allowed. (default: false)'
            - '- C(mac_changes) (bool): indicates whether mac changes are allowed. (default: false)'
        required: False
        version_added: '2.5'
        default: {
            promiscuous: False,
            forged_transmits: False,
            mac_changes: False,
        }
    teaming_policy:
        description:
            - Dictionary which configures the different teaming values for portgroup.
            - 'Valid attributes are:'
            - '- C(load_balance_policy) (string): Network adapter teaming policy. (default: loadbalance_srcid)'
            - '   - choices: [ loadbalance_ip, loadbalance_srcmac, loadbalance_srcid, loadbalance_loadbased, failover_explicit]'
            - '   - "loadbalance_loadbased" is available from version 2.6 and onwards'
            - '- C(inbound_policy) (bool): Indicate whether or not the teaming policy is applied to inbound frames as well. (default: False)'
            - '- C(notify_switches) (bool): Indicate whether or not to notify the physical switch if a link fails. (default: True)'
            - '- C(rolling_order) (bool): Indicate whether or not to use a rolling policy when restoring links. (default: False)'
        required: False
        version_added: '2.5'
        default: {
            'notify_switches': True,
            'load_balance_policy': 'loadbalance_srcid',
            'inbound_policy': False,
            'rolling_order': False
        }
    port_policy:
        description:
            - Dictionary which configures the advanced policy settings for the portgroup.
            - 'Valid attributes are:'
            - '- C(block_override) (bool): indicates if the block policy can be changed per port. (default: true)'
            - '- C(ipfix_override) (bool): indicates if the ipfix policy can be changed per port. (default: false)'
            - '- C(live_port_move) (bool): indicates if a live port can be moved in or out of the portgroup. (default: false)'
            - '- C(network_rp_override) (bool): indicates if the network resource pool can be changed per port. (default: false)'
            - '- C(port_config_reset_at_disconnect) (bool): indicates if the configuration of a port is reset automatically after disconnect. (default: true)'
            - '- C(security_override) (bool): indicates if the security policy can be changed per port. (default: false)'
            - '- C(shaping_override) (bool): indicates if the shaping policy can be changed per port. (default: false)'
            - '- C(traffic_filter_override) (bool): indicates if the traffic filter can be changed per port. (default: false)'
            - '- C(uplink_teaming_override) (bool): indicates if the uplink teaming policy can be changed per port. (default: false)'
            - '- C(vendor_config_override) (bool): indicates if the vendor config can be changed per port. (default: false)'
            - '- C(vlan_override) (bool): indicates if the vlan can be changed per port. (default: false)'
        required: False
        version_added: '2.5'
        default: {
            'traffic_filter_override': False,
            'network_rp_override': False,
            'live_port_move': False,
            'security_override': False,
            'vendor_config_override': False,
            'port_config_reset_at_disconnect': True,
            'uplink_teaming_override': False,
            'block_override': True,
            'shaping_override': False,
            'vlan_override': False,
            'ipfix_override': False
        }

extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Create vlan portgroup
  vmware_dvs_portgroup:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    portgroup_name: vlan-123-portrgoup
    switch_name: dvSwitch
    vlan_id: 123
    num_ports: 120
    portgroup_type: earlyBinding
    state: present
  delegate_to: localhost

- name: Create vlan trunk portgroup
  vmware_dvs_portgroup:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    portgroup_name: vlan-trunk-portrgoup
    switch_name: dvSwitch
    vlan_id: 1-1000, 1005, 1100-1200
    vlan_trunk: True
    num_ports: 120
    portgroup_type: earlyBinding
    state: present
  delegate_to: localhost

- name: Create no-vlan portgroup
  vmware_dvs_portgroup:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    portgroup_name: no-vlan-portrgoup
    switch_name: dvSwitch
    vlan_id: 0
    num_ports: 120
    portgroup_type: earlyBinding
    state: present
  delegate_to: localhost

- name: Create vlan portgroup with all security and port policies
  vmware_dvs_portgroup:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    portgroup_name: vlan-123-portrgoup
    switch_name: dvSwitch
    vlan_id: 123
    num_ports: 120
    portgroup_type: earlyBinding
    state: present
    network_policy:
      promiscuous: yes
      forged_transmits: yes
      mac_changes: yes
    port_policy:
      block_override: yes
      ipfix_override: yes
      live_port_move: yes
      network_rp_override: yes
      port_config_reset_at_disconnect: yes
      security_override: yes
      shaping_override: yes
      traffic_filter_override: yes
      uplink_teaming_override: yes
      vendor_config_override: yes
      vlan_override: yes
  delegate_to: localhost
'''

try:
    from pyVmomi import vim, vmodl
except ImportError as e:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, find_dvs_by_name, find_dvspg_by_name,
                                         vmware_argument_spec, wait_for_task)


class VMwareDvsPortgroup(PyVmomi):
    def __init__(self, module):
        super(VMwareDvsPortgroup, self).__init__(module)
        self.dvs_portgroup = None
        self.dv_switch = None

    def process_state(self):
        dvspg_states = {
            'absent': {
                'present': self.state_destroy_dvspg,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'update': self.state_update_dvspg,
                'present': self.state_exit_unchanged,
                'absent': self.state_create_dvspg,
            }
        }
        try:
            dvspg_states[self.module.params['state']][self.check_dvspg_state()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def create_port_group(self):
        config = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()

        # Basic config
        config.name = self.module.params['portgroup_name']
        config.numPorts = self.module.params['num_ports']

        # Default port config
        config.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
        if self.module.params['vlan_trunk']:
            config.defaultPortConfig.vlan = vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec()
            vlan_id_list = []
            for vlan_id_splitted in self.module.params['vlan_id'].split(','):
                try:
                    vlan_id_start, vlan_id_end = map(int, vlan_id_splitted.split('-'))
                    if vlan_id_start not in range(0, 4095) or vlan_id_end not in range(0, 4095):
                        self.module.fail_json(msg="vlan_id range %s specified is incorrect. The valid vlan_id range is from 0 to 4094." % vlan_id_splitted)
                    vlan_id_list.append(vim.NumericRange(start=vlan_id_start, end=vlan_id_end))
                except ValueError:
                    vlan_id_list.append(vim.NumericRange(start=int(vlan_id_splitted.strip()), end=int(vlan_id_splitted.strip())))
            config.defaultPortConfig.vlan.vlanId = vlan_id_list
        else:
            config.defaultPortConfig.vlan = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec()
            config.defaultPortConfig.vlan.vlanId = int(self.module.params['vlan_id'])
        config.defaultPortConfig.vlan.inherited = False
        config.defaultPortConfig.securityPolicy = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy()
        config.defaultPortConfig.securityPolicy.allowPromiscuous = vim.BoolPolicy(value=self.module.params['network_policy']['promiscuous'])
        config.defaultPortConfig.securityPolicy.forgedTransmits = vim.BoolPolicy(value=self.module.params['network_policy']['forged_transmits'])
        config.defaultPortConfig.securityPolicy.macChanges = vim.BoolPolicy(value=self.module.params['network_policy']['mac_changes'])

        # Teaming Policy
        teamingPolicy = vim.dvs.VmwareDistributedVirtualSwitch.UplinkPortTeamingPolicy()
        teamingPolicy.policy = vim.StringPolicy(value=self.module.params['teaming_policy']['load_balance_policy'])
        teamingPolicy.reversePolicy = vim.BoolPolicy(value=self.module.params['teaming_policy']['inbound_policy'])
        teamingPolicy.notifySwitches = vim.BoolPolicy(value=self.module.params['teaming_policy']['notify_switches'])
        teamingPolicy.rollingOrder = vim.BoolPolicy(value=self.module.params['teaming_policy']['rolling_order'])
        config.defaultPortConfig.uplinkTeamingPolicy = teamingPolicy

        # PG policy (advanced_policy)
        config.policy = vim.dvs.VmwareDistributedVirtualSwitch.VMwarePortgroupPolicy()
        config.policy.blockOverrideAllowed = self.module.params['port_policy']['block_override']
        config.policy.ipfixOverrideAllowed = self.module.params['port_policy']['ipfix_override']
        config.policy.livePortMovingAllowed = self.module.params['port_policy']['live_port_move']
        config.policy.networkResourcePoolOverrideAllowed = self.module.params['port_policy']['network_rp_override']
        config.policy.portConfigResetAtDisconnect = self.module.params['port_policy']['port_config_reset_at_disconnect']
        config.policy.securityPolicyOverrideAllowed = self.module.params['port_policy']['security_override']
        config.policy.shapingOverrideAllowed = self.module.params['port_policy']['shaping_override']
        config.policy.trafficFilterOverrideAllowed = self.module.params['port_policy']['traffic_filter_override']
        config.policy.uplinkTeamingOverrideAllowed = self.module.params['port_policy']['uplink_teaming_override']
        config.policy.vendorConfigOverrideAllowed = self.module.params['port_policy']['vendor_config_override']
        config.policy.vlanOverrideAllowed = self.module.params['port_policy']['vlan_override']

        # PG Type
        config.type = self.module.params['portgroup_type']

        task = self.dv_switch.AddDVPortgroup_Task([config])
        changed, result = wait_for_task(task)
        return changed, result

    def state_destroy_dvspg(self):
        changed = True
        result = None

        if not self.module.check_mode:
            task = self.dvs_portgroup.Destroy_Task()
            changed, result = wait_for_task(task)
        self.module.exit_json(changed=changed, result=str(result))

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def state_update_dvspg(self):
        self.module.exit_json(changed=False, msg="Currently not implemented.")

    def state_create_dvspg(self):
        changed = True
        result = None

        if not self.module.check_mode:
            changed, result = self.create_port_group()
        self.module.exit_json(changed=changed, result=str(result))

    def check_dvspg_state(self):
        self.dv_switch = find_dvs_by_name(self.content, self.module.params['switch_name'])

        if self.dv_switch is None:
            self.module.fail_json(msg="A distributed virtual switch with name %s does not exist" % self.module.params['switch_name'])
        self.dvs_portgroup = find_dvspg_by_name(self.dv_switch, self.module.params['portgroup_name'])

        if self.dvs_portgroup is None:
            return 'absent'
        else:
            return 'present'


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            portgroup_name=dict(required=True, type='str'),
            switch_name=dict(required=True, type='str'),
            vlan_id=dict(required=True, type='str'),
            num_ports=dict(required=True, type='int'),
            portgroup_type=dict(required=True, choices=['earlyBinding', 'lateBinding', 'ephemeral'], type='str'),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            vlan_trunk=dict(type='bool', default=False),
            network_policy=dict(
                type='dict',
                options=dict(
                    promiscuous=dict(type='bool', default=False),
                    forged_transmits=dict(type='bool', default=False),
                    mac_changes=dict(type='bool', default=False)
                ),
                default=dict(
                    promiscuous=False,
                    forged_transmits=False,
                    mac_changes=False
                )
            ),
            teaming_policy=dict(
                type='dict',
                options=dict(
                    inbound_policy=dict(type='bool', default=False),
                    notify_switches=dict(type='bool', default=True),
                    rolling_order=dict(type='bool', default=False),
                    load_balance_policy=dict(type='str',
                                             default='loadbalance_srcid',
                                             choices=[
                                                 'loadbalance_ip',
                                                 'loadbalance_srcmac',
                                                 'loadbalance_srcid',
                                                 'loadbalance_loadbased',
                                                 'failover_explicit',
                                             ],
                                             )
                ),
                default=dict(
                    inbound_policy=False,
                    notify_switches=True,
                    rolling_order=False,
                    load_balance_policy='loadbalance_srcid',
                ),
            ),
            port_policy=dict(
                type='dict',
                options=dict(
                    block_override=dict(type='bool', default=True),
                    ipfix_override=dict(type='bool', default=False),
                    live_port_move=dict(type='bool', default=False),
                    network_rp_override=dict(type='bool', default=False),
                    port_config_reset_at_disconnect=dict(type='bool', default=True),
                    security_override=dict(type='bool', default=False),
                    shaping_override=dict(type='bool', default=False),
                    traffic_filter_override=dict(type='bool', default=False),
                    uplink_teaming_override=dict(type='bool', default=False),
                    vendor_config_override=dict(type='bool', default=False),
                    vlan_override=dict(type='bool', default=False)
                ),
                default=dict(
                    block_override=True,
                    ipfix_override=False,
                    live_port_move=False,
                    network_rp_override=False,
                    port_config_reset_at_disconnect=True,
                    security_override=False,
                    shaping_override=False,
                    traffic_filter_override=False,
                    uplink_teaming_override=False,
                    vendor_config_override=False,
                    vlan_override=False
                )
            )
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    vmware_dvs_portgroup = VMwareDvsPortgroup(module)
    vmware_dvs_portgroup.process_state()


if __name__ == '__main__':
    main()
