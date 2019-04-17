#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2017-2018, Ansible Project
# Copyright: (c) 2019, VMware Inc.
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
    - Joseph Andreatta (@vmwjoseph)
notes:
    - Tested on vSphere 5.5
    - Tested on vSphere 6.5
    - Tested on vSphere 6.7
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    portgroup_name:
        description:
            - The name of the portgroup that is to be created or deleted.
        required: True
        type: str
    switch_name:
        description:
            - The name of the distributed vSwitch the port group should be created on.
        required: True
        type: str
    vlan_id:
        description:
            - The VLAN ID that should be configured with the portgroup, use 0 for no VLAN.
            - 'If C(vlan_trunk) is configured to be I(true), this can be a combination of multiple ranges and numbers, example: 1-200, 205, 400-4094.'
            - The valid C(vlan_id) range is from 0 to 4094. Overlapping ranges are allowed.
        required: True
        type: str
    num_ports:
        description:
            - The number of ports the portgroup should contain.
        required: True
        type: int
    auto_expand:
        description:
            - If set to true, the the distributed vSwitch will ignore the limit on the c(num_ports) in the portgroup.
        default: True
        version_added: '2.9'
    portgroup_type:
        description:
            - See VMware KB 1022312 regarding portgroup types.
        required: True
        choices:
            - 'earlyBinding'
            - 'lateBinding'
            - 'ephemeral'
        type: str
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
        version_added: '2.5'
        default: {
            promiscuous: False,
            forged_transmits: False,
            mac_changes: False,
        }
        type: dict
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
        type: dict
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
        type: dict
    mac_management_policy:
        description:
            - Dictionary which configures the MAC management policy settings for the portgroup (requires DVS version >= 6.6.0).
            - 'Valid attributes are:'
            - '- C(allow_promiscuous) (bool): indicates whether promiscuous mode is allowed. (default: None)'
            - '- C(forged_transmits) (bool): indicates whether forged transmits are allowed. (default: None)'
            - '- C(mac_changes) (bool): indicates whether mac changes are allowed. (default: None)'
            - '- C(mac_learning_policy): (dict): dictionary of MAC learning plicy settings. (Default: { enabled: False })'
            - '- Valid attributes are:'
            - '    - C(allow_unicast_flooding) (bool): indicates whether to allow flooding of unlearned MAC for ingress traffic (default: None)'
            - '    - C(enabled) (bool): indicates if source MAC address learning is allowed (default: False)'
            - '    - C(limit) (int): The maximum number of MAC addresses that can be learned.  (default: None)'
            - '    - C(limit_policy) (string): The default switching policy after MAC limit is exceeded. (default: None)'
            - '        - choices: [allow, drop, None]'
        required: False
        version_added: '2.9'
        default: {
            'allow_promiscuous':,
            'forged_transmits':,
            'mac_changes':,
            'mac_learning_policy': {
                'allow_unicast_flooding':,
                'enabled': False,
                'limit':,
                'limit_policy':
            }
        }
        type: dict

extends_documentation_fragment: vmware.documentation
'''

RETURN = r'''
result:
    description:
    - result of the changes
    returned: success
    type: str
updates:
    description:
    - dictionary of changes
    returned: on update
    type: dict
    sample: { "port_policy": "traffic_filter_override does not equal False" }
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

import re
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, find_dvs_by_name, find_dvspg_by_name,
                                         vmware_argument_spec, wait_for_task)


class VMwareDvsPortgroup(PyVmomi):

    def __init__(self, module):
        super(VMwareDvsPortgroup, self).__init__(module)
        self.dvs_portgroup = None
        self.dv_switch = None
        self.updates = dict()

        # Parse vlan_ids into an easily comparable data structure
        # For a single vlan it will look like
        #    { vlan_id: vlan_id }
        # For a trunk it will looke like:
        #    { vlan_range_1_start: vlan_range_1_end,
        #      vlan_range_2_start: vlan_range_2_end,
        #      ... }
        # Note that start and end will be equal for a single vlan
        self.vlan_ids = dict()
        try:
            for vlan_range in self.module.params['vlan_id'].split(','):
                rx = re.match(r'^\s*(?P<start>\d+)\s*(?:-\s*(?P<end>\d+))?\s*$', vlan_range)
                if not rx:
                    raise ValueError("Range {0} does not have valid format".format(vlan_range))

                start = end = int(rx.group('start'))
                if rx.group('end'):
                    end = int(rx.group('end'))

                if end < start:
                    raise ValueError("Range {0} start of range is greater than end".format(vlan_range))

                if start not in range(0, 4095) or end not in range(0, 4095):
                    self.module.fail_json(msg="vlan_id range {0} specified is incorrect. The valid vlan_id range is from 0 to 4094.".format(vlan_range))

                self.vlan_ids[start] = end
        except ValueError as e:
            self.module.fail_json(msg="ValueError parsing vlan_ids: {0}".format(to_native(e)))

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
            self.module.fail_json(msg=to_native(e))

    def create_port_group(self):
        config = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()

        # Basic config
        config.name = self.module.params['portgroup_name']
        config.numPorts = self.module.params['num_ports']
        config.autoExpand = self.module.params['auto_expand']

        # PG Type
        config.type = self.module.params['portgroup_type']

        # Default port config
        config.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()

        # vlan_id
        config.defaultPortConfig.vlan = self._vlan_spec()

        # network_policy
        config.defaultPortConfig.securityPolicy = self._security_policy_spec()

        # MAC management policy is only supported by cswitch (DVS 6.6+)
        if self.dv_switch.config.productInfo.forwardingClass == 'cswitch':
            config.defaultPortConfig.macManagementPolicy = self._mac_management_policy_spec()

        # Teaming Policy
        config.defaultPortConfig.uplinkTeamingPolicy = self._teaming_policy_spec()

        # PG policy (advanced_policy)
        config.policy = self._pg_policy_spec()

        task = self.dv_switch.AddDVPortgroup_Task([config])
        return wait_for_task(task)

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
        changed = True
        result = None

        if not self.module.check_mode:
            config = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
            config.configVersion = self.dvs_portgroup.config.configVersion
            config.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()

            if 'num_ports' in self.updates:
                config.numPorts = self.module.params['num_ports']
            if 'auto_expand' in self.updates:
                config.autoExpand = self.module.params['auto_expand']
                if not self.module.params['auto_expand']:
                    config.numPorts = self.module.params['num_ports']
            if 'portgroup_type' in self.updates:
                config.type = self.module.params['portgroup_type']
                if self.module.params['portgroup_type'] != 'ephemeral':
                    config.autoExpand = self.module.params['auto_expand']
                    if not self.module.params['auto_expand']:
                        config.numPorts = self.module.params['num_ports']
            if 'vlan_id' in self.updates or 'vlan_trunk' in self.updates:
                config.defaultPortConfig.vlan = self._vlan_spec()
            if 'network_policy' in self.updates:
                config.defaultPortConfig.securityPolicy = self._security_policy_spec()
            if 'mac_management_policy' in self.updates:
                config.defaultPortConfig.macManagementPolicy = self._mac_management_policy_spec()
            if 'teaming_policy' in self.updates:
                config.defaultPortConfig.uplinkTeamingPolicy = self._teaming_policy_spec()
            if 'port_policy' in self.updates:
                config.policy = self._pg_policy_spec()

            task = self.dvs_portgroup.ReconfigureDVPortgroup_Task(config)
            changed, result = wait_for_task(task)
        self.module.exit_json(changed=changed, result=str(result), updates=self.updates)

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
        if self.module.params['mac_management_policy']['mac_learning_policy']['enabled'] and self.dv_switch.config.productInfo.forwardingClass != 'cswitch':
            self.module.fail_json(
                msg="The distributed virtual switch does not support MAC management policy."
                + "Minimum DVS version is 6.6.0 (current version is {0})".format(self.dv_switch.config.productInfo.version)
            )

        self.dvs_portgroup = find_dvspg_by_name(self.dv_switch, self.module.params['portgroup_name'])

        if self.dvs_portgroup:
            return self.check_dvspg_settings()
        return 'absent'

    def check_dvspg_settings(self):
        state = 'present'
        config = self.dvs_portgroup.config
        pconfig = config.defaultPortConfig
        # Map config into something we can compare
        config_map = dict(
            portgroup_type=config.type,
            network_policy=dict(
                promiscuous=pconfig.securityPolicy.allowPromiscuous.value,
                forged_transmits=pconfig.securityPolicy.forgedTransmits.value,
                mac_changes=pconfig.securityPolicy.macChanges.value,
            ),
            teaming_policy=dict(
                inbound_policy=pconfig.uplinkTeamingPolicy.reversePolicy.value,
                notify_switches=pconfig.uplinkTeamingPolicy.notifySwitches.value,
                rolling_order=pconfig.uplinkTeamingPolicy.rollingOrder.value,
                load_balance_policy=pconfig.uplinkTeamingPolicy.policy.value,
            ),
            port_policy=dict(
                block_override=config.policy.blockOverrideAllowed,
                ipfix_override=config.policy.ipfixOverrideAllowed,
                live_port_move=config.policy.livePortMovingAllowed,
                network_rp_override=config.policy.networkResourcePoolOverrideAllowed,
                port_config_reset_at_disconnect=config.policy.portConfigResetAtDisconnect,
                security_override=config.policy.securityPolicyOverrideAllowed,
                shaping_override=config.policy.shapingOverrideAllowed,
                traffic_filter_override=config.policy.trafficFilterOverrideAllowed,
                uplink_teaming_override=config.policy.uplinkTeamingOverrideAllowed,
                vendor_config_override=config.policy.vendorConfigOverrideAllowed,
                vlan_override=config.policy.vlanOverrideAllowed,
            ),
        )

        # If the portgroup is ephemeral then auto_exand and num_ports are ignored
        if config_map['portgroup_type'] != 'ephemeral':
            config_map['auto_expand'] = config.autoExpand
            # If auto_exand is True, then num_ports is ignored
            if not config_map['auto_expand']:
                config_map['num_ports'] = config.numPorts

        # To gather the VLANs we need to check whether or not this is a VLAN trunk
        if isinstance(pconfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec):
            config_map['vlan_trunk'] = True
            config_map['vlan_id'] = dict()
            for vlan_range in pconfig.vlan.vlanId:
                config_map['vlan_id'][vlan_range.start] = vlan_range.end
        else:
            config_map['vlan_trunk'] = False
            config_map['vlan_id'] = {pconfig.vlan.vlanId: pconfig.vlan.vlanId}

        # The MAC Management Policy has been added to vSphere 6.7
        if hasattr(pconfig, 'macManagementPolicy') and pconfig.macManagementPolicy:
            config_map['mac_management_policy'] = dict(
                allow_promiscuous=pconfig.macManagementPolicy.allowPromiscuous,
                forged_transmits=pconfig.macManagementPolicy.forgedTransmits,
                mac_changes=pconfig.macManagementPolicy.macChanges,
                mac_learning_policy=dict(
                    allow_unicast_flooding=pconfig.macManagementPolicy.macLearningPolicy.allowUnicastFlooding,
                    enabled=pconfig.macManagementPolicy.macLearningPolicy.enabled,
                    limit=pconfig.macManagementPolicy.macLearningPolicy.limit,
                    limit_policy=pconfig.macManagementPolicy.macLearningPolicy.limitPolicy,
                ),
            )

        # Check desired state versus current state
        for k, v in config_map.items():
            desired = self.module.params[k]

            # For vlans we want to compare against the pre-computed vlan_ids instead of params
            if k == 'vlan_id':
                desired = self.vlan_ids

            if desired != v:
                state = 'update'
                self.updates[k] = "Desired '{0}' does not equal current '{1}'".format(desired, v)

        return state

    def _vlan_spec(self):
        vlan = None
        if self.module.params['vlan_trunk']:
            vlan_id_list = list()
            for range_start in self.vlan_ids:
                vlan_id_list.append(vim.NumericRange(start=range_start, end=self.vlan_ids[range_start]))
            vlan = vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec()
            vlan.vlanId = vlan_id_list
        else:
            vlan = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec()
            vlan.vlanId = int(self.module.params['vlan_id'])
        vlan.inherited = False

        return vlan

    def _security_policy_spec(self):
        security_policy = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy()
        security_policy.allowPromiscuous = vim.BoolPolicy(value=self.module.params['network_policy']['promiscuous'])
        security_policy.forgedTransmits = vim.BoolPolicy(value=self.module.params['network_policy']['forged_transmits'])
        security_policy.macChanges = vim.BoolPolicy(value=self.module.params['network_policy']['mac_changes'])

        return security_policy

    def _teaming_policy_spec(self):

        teaming_policy = vim.dvs.VmwareDistributedVirtualSwitch.UplinkPortTeamingPolicy()
        teaming_policy.policy = vim.StringPolicy(value=self.module.params['teaming_policy']['load_balance_policy'])
        teaming_policy.reversePolicy = vim.BoolPolicy(value=self.module.params['teaming_policy']['inbound_policy'])
        teaming_policy.notifySwitches = vim.BoolPolicy(value=self.module.params['teaming_policy']['notify_switches'])
        teaming_policy.rollingOrder = vim.BoolPolicy(value=self.module.params['teaming_policy']['rolling_order'])

        return teaming_policy

    def _pg_policy_spec(self):
        pg_policy = vim.dvs.VmwareDistributedVirtualSwitch.VMwarePortgroupPolicy()
        pg_policy.blockOverrideAllowed = self.module.params['port_policy']['block_override']
        pg_policy.ipfixOverrideAllowed = self.module.params['port_policy']['ipfix_override']
        pg_policy.livePortMovingAllowed = self.module.params['port_policy']['live_port_move']
        pg_policy.networkResourcePoolOverrideAllowed = self.module.params['port_policy']['network_rp_override']
        pg_policy.portConfigResetAtDisconnect = self.module.params['port_policy']['port_config_reset_at_disconnect']
        pg_policy.securityPolicyOverrideAllowed = self.module.params['port_policy']['security_override']
        pg_policy.shapingOverrideAllowed = self.module.params['port_policy']['shaping_override']
        pg_policy.trafficFilterOverrideAllowed = self.module.params['port_policy']['traffic_filter_override']
        pg_policy.uplinkTeamingOverrideAllowed = self.module.params['port_policy']['uplink_teaming_override']
        pg_policy.vendorConfigOverrideAllowed = self.module.params['port_policy']['vendor_config_override']
        pg_policy.vlanOverrideAllowed = self.module.params['port_policy']['vlan_override']

        return pg_policy

    def _mac_management_policy_spec(self):
        mm_policy = vim.dvs.VmwareDistributedVirtualSwitch.MacManagementPolicy()
        mm_policy.allowPromiscuous = self.module.params['mac_management_policy']['allow_promiscuous']
        mm_policy.forgedTransmits = self.module.params['mac_management_policy']['forged_transmits']
        mm_policy.macChanges = self.module.params['mac_management_policy']['mac_changes']
        mm_policy.macLearningPolicy = vim.dvs.VmwareDistributedVirtualSwitch.MacLearningPolicy()
        mm_policy.macLearningPolicy.enabled = self.module.params['mac_management_policy']['mac_learning_policy']['enabled']
        mm_policy.macLearningPolicy.allowUnicastFlooding = self.module.params['mac_management_policy']['mac_learning_policy']['allow_unicast_flooding']
        mm_policy.macLearningPolicy.limit = self.module.params['mac_management_policy']['mac_learning_policy']['limit']
        mm_policy.macLearningPolicy.limitPolicy = self.module.params['mac_management_policy']['mac_learning_policy']['limit_policy']

        return mm_policy


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            portgroup_name=dict(required=True, type='str'),
            switch_name=dict(required=True, type='str'),
            vlan_id=dict(required=True, type='str'),
            num_ports=dict(required=True, type='int'),
            auto_expand=dict(default=True, type='bool'),
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
            ),
            mac_management_policy=dict(
                type='dict',
                options=dict(
                    allow_promiscuous=dict(type='bool', default=None),
                    forged_transmits=dict(type='bool', default=None),
                    mac_changes=dict(type='bool', default=None),
                    mac_learning_policy=dict(
                        type='dict',
                        options=dict(
                            allow_unicast_flooding=dict(type='bool', default=None),
                            enabled=dict(type='bool', default=False),
                            limit=dict(type='int', default=None),
                            limit_policy=dict(type='str', choices=['allow', 'drop', None], default=None),
                        ),
                        default=dict(allow_unicast_flooding=None, enabled=False, limit=None, limit_policy=None),
                    ),
                ),
                default=dict(),
            ),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    vmware_dvs_portgroup = VMwareDvsPortgroup(module)
    vmware_dvs_portgroup.process_state()


if __name__ == '__main__':
    main()
