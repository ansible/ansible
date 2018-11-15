#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2017-2018, Ansible Project
# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
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
    - Philippe Dellaert (@pdellaert)
    - Christian Kotte (@ckotte)
notes:
    - Tested on vSphere 5.5
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    portgroup:
        description:
            - The name of the portgroup that is to be created or deleted.
        required: True
        aliases: ['portgroup_name']
    switch:
        description:
            - The name of the distributed vSwitch the port group should be created on.
        required: True
        aliases: ['switch_name']
    description:
        description:
            - The description of the portgroup.
        type: str
        aliases: ['portgroup_description']
        version_added: 2.8
    num_ports:
        description:
            - The number of ports the portgroup should contain.
            - The number of ports for a new portgroup will be 0 if not specified.
            - The vSphere Client uses 8 by default.
            - This option will be ignored if C(port_binding) is set to 'ephemeral'.
        aliases: ['ports']
    portgroup_type:
        description:
            - See VMware KB 1022312 regarding portgroup types.
            - Deprecated. Will be removed in 2.11.
        choices: ['earlyBinding', 'lateBinding', 'ephemeral']
    port_binding:
        description:
            - The type of port binding determines when ports in a port group are assigned to virtual machines.
            - Valid attributes are static, dynamic, or ephemeral.
            - See VMware KB 1022312 U(https://kb.vmware.com/s/article/1022312) for more details.
        choices: ['static', 'dynamic', 'ephemeral']
        default: 'static'
        version_added: 2.8
    port_allocation:
        description:
            - Elastic port groups automatically increase or decrease the number of ports as needed.
            - Only valid if C(port_binding) is set to 'static'.
            - Will be 'elastic' if not specified and C(port_binding) is set to 'static'.
        required: True
        choices: ['fixed', 'elastic']
        version_added: 2.8
    network_resource_pool:
        description:
            - The Network Resource Pool the portgroup should be assigned to.
        default: 'default'
        version_added: 2.8
    state:
        description:
            - Determines if the portgroup should be present or not.
        type: bool
        choices: ['present', 'absent']
        default: 'present'
        version_added: '2.5'
    vlan_id:
        description:
            - The VLAN ID that should be configured with the portgroup, use 0 for no VLAN.
        type: int
        default: 0
        required: False
    private_vlan_id:
        description:
            - The secondary private VLAN ID.
            - The secondary private VLAN ID need to be configured on the dvSwitch first.'
        type: int
        version_added: '2.8'
    vlan_trunk_range:
        description:
            - The VLAN trunk range that should be configured with the portgroup.
            - 'This can be a combination of multiple ranges and numbers, example: [ 1-200, 205, 400-4094 ].'
            - The default VLAN trunk range in the vSphere Client is [ 0-4094 ].
        type: list
        version_added: 2.8
    vlan_trunk:
        description:
            - Indicates whether this is a VLAN trunk or not.
            - Deprecated. Will be removed in 2.11.
        required: False
        default: False
        type: bool
        version_added: '2.5'
    security:
        description:
            - Dictionary which configures the different security values for portgroup.
            - 'Valid attributes are:'
            - '- C(promiscuous_mode) (bool): indicates whether promiscuous mode is allowed. (default: false)'
            - '   - aliases: [ promiscuous ]'
            - '- C(forged_transmits) (bool): indicates whether forged transmits are allowed. (default: false)'
            - '- C(mac_changes) (bool): indicates whether mac changes are allowed. (default: false)'
        required: False
        version_added: '2.5'
        default: {
            promiscuous_mode: False,
            forged_transmits: False,
            mac_changes: False,
        }
        aliases: ['network_policy', 'security_policy']
    teaming:
        description:
            - Dictionary which configures the different teaming values for portgroup.
            - 'Valid attributes are:'
            - '- C(load_balancing) (string): Network adapter teaming policy. (default: loadbalance_srcid)'
            - '   - choices: [ loadbalance_ip, loadbalance_srcmac, loadbalance_srcid, loadbalance_loadbased, failover_explicit]'
            - '   - aliases: [ load_balancing_policy ]'
            - '   - "loadbalance_loadbased" is available from version 2.6 and onwards'
            - '- C(network_failure_detection) (string): Network failure detection. (default: link_status_only)'
            - '   - choices: [ link_status_only, beacon_probing ]'
            - '- C(notify_switches) (bool): Indicate whether or not to notify the physical switch if a link fails. (default: True)'
            - '- C(failback) (bool): Indicate whether or not to use a failback when restoring links. (default: True)'
            - '   - aliases: [ rolling_order ]'
            - '- C(failover_order) (dict): Define uplink failover order. Default uplinks are used for active uplinks if not defined.'
            - '- C(active_uplinks) (list): List of active uplinks used for load balancing.'
            - '- C(standby_uplinks) (list): List of standby uplinks used for failover.'
            - '- All uplinks are used as active uplinks if C(active_uplinks) and C(standby_uplinks) are not defined.'
        required: False
        version_added: '2.5'
        default: {
            'load_balancing': 'loadbalance_srcid',
            'network_failure_detection': 'link_status_only',
            'notify_switches': True,
            'failback': True
        }
        aliases: ['teaming_policy']
    advanced:
        description:
            - Dictionary which configures the advanced policy settings for the portgroup.
            - 'Valid attributes are:'
            - '- C(block_override) (bool): indicates if the block policy can be changed per port. (default: true)'
            - '- C(netflow_override) (bool): indicates if the NetFlow policy can be changed per port. (default: false)'
            - '   - aliases: [ ipfix_override ]'
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
            'security_override': False,
            'vendor_config_override': False,
            'port_config_reset_at_disconnect': True,
            'uplink_teaming_override': False,
            'block_override': True,
            'shaping_override': False,
            'vlan_override': False,
            'netflow_override': False
        }
        aliases: ['port_policy']
    netflow_enabled:
        description:
            - Indicates if NetFlow is enabled on the uplink portgroup.
        type: bool
        default: False
        version_added: 2.8
    block_all_ports:
        description:
            - Indicates if all ports are blocked on the uplink portgroup.
        type: bool
        default: False
        version_added: 2.8
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Create vlan portgroup
  vmware_dvs_portgroup:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    portgroup: vlan-123-portrgoup
    switch: dvSwitch
    vlan_id: 123
    num_ports: 120
    state: present
  delegate_to: localhost

- name: Create vlan trunk portgroup
  vmware_dvs_portgroup:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    portgroup: vlan-trunk-portgroup
    switch: dvSwitch
    vlan_trunk_range:
      - 1-1000
      - 1005
      - 1100-1200
    num_ports: 120
    state: present
  delegate_to: localhost

- name: Create pvlan portgroup
  vmware_dvs_portgroup:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    portgroup: vlan-123-portgroup
    switch: dvSwitch
    private_vlan_id: 123
    num_ports: 120
    state: present
  delegate_to: localhost

- name: Create no-vlan portgroup with no uplinks
  vmware_dvs_portgroup:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    portgroup: no-vlan-portgroup
    switch: dvSwitch
    num_ports: 120
    teaming:
      active_uplinks: []
      standby_uplinks: []
    state: present
  delegate_to: localhost

- name: Create vlan portgroup with all settings
  vmware_dvs_portgroup:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    portgroup: vlan-123-portgroup
    switch: dvSwitch
    vlan_id: 123
    num_ports: 120
    port_binding: static
    port_allocation: elastic
    security:
      promiscuous_mode: no
      mac_changes: no
      forged_transmits: no
    teaming:
      load_balancing: loadbalance_srcid
      network_failure_detection: link_status_only
      notify_switches: True
      failback: True
      active_uplinks: [ 'Uplink 1' ]
      standby_uplinks: [ 'Uplink 2' ]
    advanced:
      port_config_reset_at_disconnect: yes
      block_override: yes
      netflow_override: yes
      network_rp_override: yes
      security_override: yes
      shaping_override: yes
      traffic_filter_override: yes
      uplink_teaming_override: yes
      vendor_config_override: yes
      vlan_override: yes
    state: present
  delegate_to: localhost
'''

RETURN = """
result:
    description: information about performed operation
    returned: always
    type: string
    sample: {
        "adv_block_ports": true,
        "adv_netflow": false,
        "adv_network_rp": false,
        "adv_reset_at_disconnect": true,
        "adv_security": false,
        "adv_traffic_filtering": false,
        "adv_traffic_shaping": false,
        "adv_uplink_teaming": false,
        "adv_vendor_conf": false,
        "adv_vlan": false,
        "block_all_ports": false,
        "changed": false,
        "description": null,
        "dvswitch": "dvSwitch",
        "failback": true,
        "failover_active": [
            "Uplink 1"
        ],
        "failover_standby": [
            "Uplink 2"
        ],
        "failure_detection": "link_status_only",
        "load_balancing": "loadbalance_srcid",
        "netflow_enabled": false,
        "network_rp": "default",
        "notify": true,
        "num_ports": null,
        "port_allocation": "elastic",
        "port_binding": "static",
        "portgroup": "Test",
        "result": "Portgroup already configured properly",
        "sec_forged_transmits": false,
        "sec_mac_changes": false,
        "sec_promiscuous_mode": false,
        "vlan_trunk_range": [
            "1-1000",
            1005,
            "1100-1200"
        ]
    }
"""

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (
    PyVmomi, TaskError, find_dvs_by_name, find_dvspg_by_name, vmware_argument_spec, wait_for_task
)


class VMwareDvsPortgroup(PyVmomi):
    """Class to manage a DVS portgroup"""

    def __init__(self, module):
        super(VMwareDvsPortgroup, self).__init__(module)
        self.dvs_portgroup = None
        self.dv_switch = None

        self.switch_name = self.module.params['switch']
        self.portgroup_name = self.module.params['portgroup']
        self.description = self.module.params['description']
        self.num_ports = self.module.params['num_ports']
        self.network_resource_pool = self.module.params['network_resource_pool']
        self.port_binding = self.module.params['port_binding']
        self.port_allocation = self.module.params['port_allocation']
        # Port binding sanity checks
        if self.port_binding == 'ephemeral' and self.num_ports:
            self.module.fail_json(
                msg="The number of ports cannot be configured when port binding is set to 'ephemeral'."
            )
        if self.port_binding != 'static' and self.port_allocation == 'elastic':
            self.module.fail_json(
                msg="Port allocation of type 'elastic' cannot be configured when port binding isn't set to 'static'."
            )
        self.pp_reset = self.module.params['advanced']['port_config_reset_at_disconnect']
        self.pp_block_ports = self.module.params['advanced']['block_override']
        self.pp_shaping = self.module.params['advanced']['shaping_override']
        self.pp_vendor_conf = self.module.params['advanced']['vendor_config_override']
        self.pp_vlan = self.module.params['advanced']['vlan_override']
        self.pp_uplink_teaming = self.module.params['advanced']['uplink_teaming_override']
        self.pp_network_rp = self.module.params['advanced']['network_rp_override']
        self.pp_security = self.module.params['advanced']['security_override']
        self.pp_netflow = self.module.params['advanced']['netflow_override']
        self.pp_traffic_filter = self.module.params['advanced']['traffic_filter_override']
        self.sec_promiscuous_mode = self.params['security'].get('promiscuous_mode')
        self.sec_forged_transmits = self.params['security'].get('forged_transmits')
        self.sec_mac_changes = self.params['security'].get('mac_changes')
        self.vlan_id = self.module.params['vlan_id']
        self.vlan_trunk_range = self.module.params['vlan_trunk_range']
        self.private_vlan_id = self.module.params['private_vlan_id']
        self.teaming_load_balancing = self.params['teaming'].get('load_balancing')
        self.teaming_failure_detection = self.params['teaming'].get('network_failure_detection')
        self.teaming_notify_switches = self.params['teaming'].get('notify_switches')
        self.teaming_failback = self.params['teaming'].get('failback')
        self.teaming_failover_order_active = self.params['teaming'].get('active_uplinks')
        self.teaming_failover_order_standby = self.params['teaming'].get('standby_uplinks')
        # set other uplinks list to an empty array instead of 'None' if only one list is defined
        # this avoids update issues since the API changes accepts 'None', but it changes it to '[]'
        if self.teaming_failover_order_active or self.teaming_failover_order_standby:
            if self.teaming_failover_order_active is None:
                self.teaming_failover_order_active = []
            if self.teaming_failover_order_standby is None:
                self.teaming_failover_order_standby = []
        self.netflow_enabled = self.module.params['netflow_enabled']
        self.block_all_ports = self.module.params['block_all_ports']

        # NOTE: Deprecated options. Will be removed in 2.11
        self.portgroup_type = self.module.params['portgroup_type']
        self.vlan_trunk = self.module.params['vlan_trunk']

    def process_state(self):
        """Process the current state of the portgroup"""
        dvspg_states = {
            'absent': {
                'present': self.destroy_port_group,
                'absent': self.exit_unchanged,
            },
            'present': {
                'present': self.update_port_group,
                'absent': self.create_port_group,
            }
        }
        try:
            dvspg_states[self.module.params['state']][self.check_port_group_state()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def check_port_group_state(self):
        """Check if DVS portgroup exists"""
        self.dv_switch = find_dvs_by_name(self.content, self.switch_name)

        if self.dv_switch is None:
            self.module.fail_json(
                msg="A distributed virtual switch with name %s does not exist" % self.switch_name
            )
        self.dvs_portgroup = find_dvspg_by_name(self.dv_switch, self.portgroup_name)
        if self.dvs_portgroup:
            return 'present'
        return 'absent'

    def create_port_group(self):
        """Create DVS portgroup"""
        changed = True
        results = dict(changed=changed)

        pg_spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()

        # Name
        results['portgroup'] = self.portgroup_name
        pg_spec.name = self.portgroup_name
        # Description
        results['description'] = self.description
        pg_spec.description = self.description
        # Number of ports
        results['num_ports'] = self.num_ports
        pg_spec.numPorts = self.num_ports
        # Port binding
        # NOTE: 'self.portgroup_type' is deprecated. Will be removed in 2.11
        if self.portgroup_type:
            results['portgroup_type'] = self.portgroup_type
            pg_spec.type = self.portgroup_type
        else:
            results['port_binding'] = self.port_binding
            pg_spec.type = self.get_api_port_binding_mode(self.port_binding)
        # Port allocation
        if not self.port_allocation:
            if self.port_binding == 'dynamic' or self.port_binding == 'ephemeral':
                results['port_allocation'] = 'n/a'
            else:
                results['port_allocation'] = 'elastic'
                pg_spec.autoExpand = True
        else:
            results['port_allocation'] = self.port_allocation
            if self.port_allocation == 'elastic':
                pg_spec.autoExpand = True
            elif self.port_allocation == 'fixed':
                pg_spec.autoExpand = False

        # Advanced / Port policies
        results['adv_reset_at_disconnect'] = self.pp_reset
        results['adv_block_ports'] = self.pp_block_ports
        results['adv_traffic_shaping'] = self.pp_shaping
        results['adv_vendor_conf'] = self.pp_vendor_conf
        results['adv_vlan'] = self.pp_vlan
        results['adv_uplink_teaming'] = self.pp_uplink_teaming
        results['adv_network_rp'] = self.pp_network_rp
        results['adv_security'] = self.pp_security
        results['adv_netflow'] = self.pp_netflow
        results['adv_traffic_filtering'] = self.pp_traffic_filter
        result = self.check_port_policy_config(pg_config=None)
        pg_spec.policy = result[0]

        pg_spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()

        # Network resource pool
        results['network_rp'] = self.network_resource_pool
        if self.network_resource_pool == 'default':
            pg_spec.defaultPortConfig.networkResourcePoolKey = vim.StringPolicy(inherited=False, value='-1')
        else:
            network_resource_pool = self.find_network_rp_by_name(self.network_resource_pool)
            if network_resource_pool is None:
                self.module.fail_json(msg="Network resource pool '%s' was not found" % self.network_resource_pool)
            pg_spec.defaultPortConfig.networkResourcePoolKey = vim.StringPolicy(
                inherited=False, value=network_resource_pool.key
            )

        # Security
        results['sec_promiscuous_mode'] = self.sec_promiscuous_mode
        results['sec_mac_changes'] = self.sec_mac_changes
        results['sec_forged_transmits'] = self.sec_forged_transmits
        result = self.check_security_config(pg_config=None)
        pg_spec.defaultPortConfig.securityPolicy = result[0]

        # TODO: Traffic shaping

        if self.vlan_id == 0:
            results['vlan_id'] = 0
            pg_spec.defaultPortConfig.vlan = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec()
            pg_spec.defaultPortConfig.vlan.vlanId = 0
        # NOTE: 'vlan_trunk' option is deprecated. Will be removed in 2.11
        elif self.vlan_trunk or self.vlan_trunk_range:
            results['vlan_trunk_range'] = self.vlan_trunk_range
            result = self.check_trunk_vlan_config(pg_config=None)
            pg_spec.defaultPortConfig.vlan = result[0]
        elif self.private_vlan_id:
            if self.dv_switch.config.pvlanConfig:
                results['private_vlan_id'] = self.private_vlan_id
                pg_spec.defaultPortConfig.vlan = vim.dvs.VmwareDistributedVirtualSwitch.PvlanSpec()
                pg_spec.defaultPortConfig.vlan.pvlanId = int(self.private_vlan_id)
            else:
                self.module.fail_json(msg="Private VLAN is not configured for this distributed switch!")
        elif self.vlan_id:
            results['vlan_id'] = self.vlan_id
            pg_spec.defaultPortConfig.vlan = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec()
            pg_spec.defaultPortConfig.vlan.vlanId = int(self.vlan_id)
        pg_spec.defaultPortConfig.vlan.inherited = False

        # Teaming and failover
        teaming_policy = vim.dvs.VmwareDistributedVirtualSwitch.UplinkPortTeamingPolicy()
        results['load_balancing'] = self.teaming_load_balancing
        teaming_policy.policy = vim.StringPolicy(inherited=False, value=self.teaming_load_balancing)
        teaming_policy.failureCriteria = vim.dvs.VmwareDistributedVirtualSwitch.FailureCriteria()
        results['failure_detection'] = self.teaming_failure_detection
        if self.teaming_failure_detection == "link_status_only":
            teaming_policy.failureCriteria.checkBeacon = vim.BoolPolicy(inherited=False, value=False)
        elif self.teaming_failure_detection == "beacon_probing":
            teaming_policy.failureCriteria.checkBeacon = vim.BoolPolicy(inherited=False, value=True)
        # Deprecated since VI API 5.1. The system default (true) will be used
        teaming_policy.reversePolicy = vim.BoolPolicy(inherited=False, value=True)
        results['notify'] = self.teaming_notify_switches
        teaming_policy.notifySwitches = vim.BoolPolicy(inherited=False, value=self.teaming_notify_switches)
        # this option is called 'failback' in the vSphere Client
        # rollingOrder also uses the opposite value displayed in the client
        results['failback'] = self.teaming_failback
        teaming_policy.rollingOrder = vim.BoolPolicy(inherited=False, value=not self.teaming_failback)
        if self.teaming_failover_order_active or self.teaming_failover_order_standby:
            teaming_policy.uplinkPortOrder = vim.dvs.VmwareDistributedVirtualSwitch.UplinkPortOrderPolicy()
            teaming_policy.uplinkPortOrder.activeUplinkPort = self.teaming_failover_order_active
            teaming_policy.uplinkPortOrder.standbyUplinkPort = self.teaming_failover_order_standby
            results['failover_active'] = self.teaming_failover_order_active
            results['failover_standby'] = self.teaming_failover_order_standby
        pg_spec.defaultPortConfig.uplinkTeamingPolicy = teaming_policy

        # Monitoring - NetFlow
        results['netflow_enabled'] = self.netflow_enabled
        result = self.check_netflow_policy_config(pg_config=None)
        pg_spec.defaultPortConfig.ipfixEnabled = result[0]

        # TODO: Traffic filtering and marking

        # Misc. - Block all ports
        results['block_all_ports'] = self.block_all_ports
        result = self.check_blocked_policy_config(pg_config=None)
        pg_spec.defaultPortConfig.blocked = result[0]

        if self.module.check_mode:
            results['result'] = "Portgroup would be created"
        else:
            task = self.dv_switch.AddDVPortgroup_Task([pg_spec])
            try:
                wait_for_task(task)
            except TaskError as invalid_argument:
                self.module.fail_json(
                    msg="Failed to create portgroup : %s" % to_native(invalid_argument)
                )
            results['result'] = "Portgroup created"

        self.module.exit_json(**results)

    @staticmethod
    def get_api_port_binding_mode(mode):
        """Get port binding mode"""
        port_binding_mode = None
        if mode == 'earlyBinding':
            port_binding_mode = 'static'
        elif mode == 'lateBinding':
            port_binding_mode = 'dynamic'
        elif mode == 'static':
            port_binding_mode = 'earlyBinding'
        elif mode == 'dynamic':
            port_binding_mode = 'lateBinding'
        # ephemeral stays the same
        elif mode == 'ephemeral':
            port_binding_mode = 'ephemeral'
        return port_binding_mode

    def check_port_policy_config(self, pg_config):
        """Check port policies config"""
        changed = reset_at_disconnect = block_override = shaping_override = vendor_config_override = \
            vlan_override = uplink_teaming_override = network_rp_override = security_override = \
            netflow_override = traffic_filter_override = False
        pg_policy_spec = vim.dvs.VmwareDistributedVirtualSwitch.VMwarePortgroupPolicy()
        pg_policy_spec.portConfigResetAtDisconnect = self.pp_reset
        pg_policy_spec.blockOverrideAllowed = self.pp_block_ports
        pg_policy_spec.shapingOverrideAllowed = self.pp_shaping
        pg_policy_spec.vendorConfigOverrideAllowed = self.pp_vendor_conf
        pg_policy_spec.vlanOverrideAllowed = self.pp_vlan
        pg_policy_spec.uplinkTeamingOverrideAllowed = self.pp_uplink_teaming
        pg_policy_spec.networkResourcePoolOverrideAllowed = self.pp_network_rp
        pg_policy_spec.securityPolicyOverrideAllowed = self.pp_security
        pg_policy_spec.ipfixOverrideAllowed = self.pp_netflow
        pg_policy_spec.trafficFilterOverrideAllowed = self.pp_traffic_filter
        # There's no information available if this option is deprecated, but it isn't visible in the vSphere Client
        pg_policy_spec.livePortMovingAllowed = False
        # Check policies
        if pg_config:
            if pg_config.policy.portConfigResetAtDisconnect != self.pp_reset:
                changed = reset_at_disconnect = True
            if pg_config.policy.blockOverrideAllowed != self.pp_block_ports:
                changed = block_override = True
            if pg_config.policy.shapingOverrideAllowed != self.pp_shaping:
                changed = shaping_override = True
            if pg_config.policy.vendorConfigOverrideAllowed != self.pp_vendor_conf:
                changed = vendor_config_override = True
            if pg_config.policy.vlanOverrideAllowed != self.pp_vlan:
                changed = vlan_override = True
            if pg_config.policy.uplinkTeamingOverrideAllowed != self.pp_uplink_teaming:
                changed = uplink_teaming_override = True
            if pg_config.policy.networkResourcePoolOverrideAllowed != self.pp_network_rp:
                changed = network_rp_override = True
            if pg_config.policy.securityPolicyOverrideAllowed != self.pp_security:
                changed = security_override = True
            if pg_config.policy.ipfixOverrideAllowed != self.pp_netflow:
                changed = netflow_override = True
            if pg_config.policy.trafficFilterOverrideAllowed != self.pp_traffic_filter:
                changed = traffic_filter_override = True
        return (pg_policy_spec, changed, reset_at_disconnect, block_override, shaping_override,
                vendor_config_override, vlan_override, uplink_teaming_override, network_rp_override,
                security_override, netflow_override, traffic_filter_override)

    def find_network_rp_by_name(self, resource_name):
        """Find network resource pool by name"""
        config = None
        if self.dv_switch.config.networkResourceControlVersion == "version3":
            config = self.dv_switch.config.infrastructureTrafficResourceConfig
        elif self.dv_switch.config.networkResourceControlVersion == "version2":
            config = self.dv_switch.networkResourcePool
        for obj in config:
            if obj.name == resource_name:
                return obj
        return None

    def find_network_rp_by_key(self, resource_key):
        """Find network resource pool by key"""
        config = None
        if self.dv_switch.config.networkResourceControlVersion == "version3":
            config = self.dv_switch.config.infrastructureTrafficResourceConfig
        elif self.dv_switch.config.networkResourceControlVersion == "version2":
            config = self.dv_switch.networkResourcePool
        for obj in config:
            if obj.key == resource_key:
                return obj
        return None

    def check_security_config(self, pg_config):
        """Check security config"""
        changed = False
        promiscuous_mode_previous = mac_changes_previous = forged_transmits_previous = None
        sec_spec = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy()
        sec_spec.allowPromiscuous = vim.BoolPolicy(inherited=False, value=self.sec_promiscuous_mode)
        sec_spec.macChanges = vim.BoolPolicy(inherited=False, value=self.sec_mac_changes)
        sec_spec.forgedTransmits = vim.BoolPolicy(inherited=False, value=self.sec_forged_transmits)
        if pg_config:
            promiscuous_mode_previous = pg_config.defaultPortConfig.securityPolicy.allowPromiscuous.value
            mac_changes_previous = pg_config.defaultPortConfig.securityPolicy.macChanges.value
            forged_transmits_previous = pg_config.defaultPortConfig.securityPolicy.forgedTransmits.value
            if promiscuous_mode_previous != self.sec_promiscuous_mode:
                changed = True
            if mac_changes_previous != self.sec_mac_changes:
                changed = True
            if forged_transmits_previous != self.sec_forged_transmits:
                changed = True
        return sec_spec, changed, promiscuous_mode_previous, mac_changes_previous, forged_transmits_previous

    def check_trunk_vlan_config(self, pg_config):
        """Check trunk VLAN config"""
        changed_vlan_trunk_range = False
        # NOTE: the following code is for backward compatibility only. Will be removed in 2.11
        if self.vlan_trunk:
            trunk_vlan_spec = vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec()
            vlan_id_start, vlan_id_end = self.vlan_id.split('-')
            trunk_vlan_spec.vlanId = [vim.NumericRange(start=int(vlan_id_start.strip()), end=int(vlan_id_end.strip()))]
            # Do not check if range is already configured; just classify it as changed
            changed_vlan_trunk_range = True
        else:
            vlan_id_ranges = self.vlan_trunk_range
            trunk_vlan_spec = vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec()
            vlan_id_list = []
            for vlan_id_range in vlan_id_ranges:
                vlan_id_range_found = False
                vlan_id_start, vlan_id_end = self.get_vlan_ids_from_range(vlan_id_range)
                if pg_config:
                    # Check if range is already configured
                    for current_vlan_id_range in pg_config.defaultPortConfig.vlan.vlanId:
                        if (current_vlan_id_range.start == int(vlan_id_start) and
                                current_vlan_id_range.end == int(vlan_id_end)):
                            vlan_id_range_found = True
                            break
                    if vlan_id_range_found is False:
                        changed_vlan_trunk_range = True
                vlan_id_list.append(vim.NumericRange(start=int(vlan_id_start), end=int(vlan_id_end)))
            if pg_config:
                # Check if range needs to be removed
                for current_vlan_id_range in pg_config.defaultPortConfig.vlan.vlanId:
                    vlan_id_range_found = False
                    for vlan_id_range in vlan_id_ranges:
                        vlan_id_start, vlan_id_end = self.get_vlan_ids_from_range(vlan_id_range)
                        if (current_vlan_id_range.start == int(vlan_id_start) and
                                current_vlan_id_range.end == int(vlan_id_end)):
                            vlan_id_range_found = True
                            break
                    if vlan_id_range_found is False:
                        changed_vlan_trunk_range = True
            trunk_vlan_spec.vlanId = vlan_id_list
        return trunk_vlan_spec, changed_vlan_trunk_range

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
    def get_current_trunk_vlan_range(pg_config):
        """Get current VLAN trunk range as string"""
        current_vlan_id_list = []
        for current_vlan_id_range in pg_config.defaultPortConfig.vlan.vlanId:
            if current_vlan_id_range.start == current_vlan_id_range.end:
                current_vlan_id_range_string = current_vlan_id_range.start
            else:
                current_vlan_id_range_string = '-'.join(
                    [str(current_vlan_id_range.start), str(current_vlan_id_range.end)]
                )
            current_vlan_id_list.append(current_vlan_id_range_string)
        return current_vlan_id_list

    def check_netflow_policy_config(self, pg_config):
        """Check NetFlow policy config"""
        changed = False
        netflow_enabled_previous = None
        netflow_enabled_spec = vim.BoolPolicy()
        netflow_enabled_spec.inherited = False
        netflow_enabled_spec.value = self.netflow_enabled
        if pg_config and pg_config.defaultPortConfig.ipfixEnabled.value != self.netflow_enabled:
            changed = True
            netflow_enabled_previous = pg_config.defaultPortConfig.ipfixEnabled.value
        return netflow_enabled_spec, changed, netflow_enabled_previous

    def check_blocked_policy_config(self, pg_config):
        """Check block all ports policy config"""
        changed = False
        block_all_ports_previous = None
        block_all_ports_spec = vim.BoolPolicy()
        block_all_ports_spec.inherited = False
        block_all_ports_spec.value = self.block_all_ports
        if pg_config and pg_config.defaultPortConfig.blocked.value != self.block_all_ports:
            changed = True
            block_all_ports_previous = pg_config.defaultPortConfig.blocked.value
        return block_all_ports_spec, changed, block_all_ports_previous

    def destroy_port_group(self):
        """Delete a DVS portgroup"""
        changed = True
        results = dict(changed=changed)
        results['dvswitch'] = self.switch_name
        results['portgroup'] = self.portgroup_name
        if self.module.check_mode:
            results['result'] = "Portgroup would be deleted"
        else:
            try:
                task = self.dvs_portgroup.Destroy_Task()
            except vim.fault.VimFault as vim_fault:
                self.module.fail_json(msg="Failed to deleted portgroup : %s" % to_native(vim_fault))
            wait_for_task(task)
            results['result'] = "Portgroup deleted"
        self.module.exit_json(**results)

    def exit_unchanged(self):
        """Exit with status message"""
        changed = False
        results = dict(changed=changed)
        results['dvswitch'] = self.switch_name
        results['portgroup'] = self.portgroup_name
        results['result'] = "Portgroup not present"
        self.module.exit_json(**results)

    def update_port_group(self):
        """Check and update DVS portgroup"""
        changed = changed_policy = changed_vlan = changed_vlan_trunk_range = \
            changed_security = changed_teaming = changed_failover_order = False
        results = dict(changed=changed)
        results['dvswitch'] = self.switch_name
        results['portgroup'] = self.portgroup_name
        changed_list = []

        pg_spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
        # Use the same version in the new spec; The version will be increased by one by the API automatically
        pg_spec.configVersion = self.dvs_portgroup.config.configVersion
        pg_config = self.dvs_portgroup.config

        # Check number of ports (only if option is specified)
        # NOTE: 'self.portgroup_type' is deprecated. Will be removed in 2.11
        if self.port_binding == 'ephemeral' or self.portgroup_type == 'ephemeral':
            results['num_ports'] = 'n/a'
        else:
            results['num_ports'] = self.num_ports
            if self.num_ports and pg_config.numPorts != self.num_ports:
                changed = True
                changed_list.append("num ports")
                results['num_ports_previous'] = pg_config.description
                pg_spec.numPorts = self.num_ports

        # Check port binding
        # NOTE: 'self.portgroup_type' is deprecated. Will be removed in 2.11
        if self.portgroup_type:
            results['portgroup_type'] = self.portgroup_type
            if pg_config.type != self.portgroup_type:
                changed = True
                changed_list.append("portgroup type")
                results['portgroup_type_previous'] = self.portgroup_type
                pg_spec.type = self.portgroup_type
        else:
            results['port_binding'] = self.port_binding
            if pg_config.type != self.get_api_port_binding_mode(self.port_binding):
                changed = True
                changed_list.append("port binding")
                results['port_binding_previous'] = self.get_api_port_binding_mode(pg_config.type)
                pg_spec.type = self.get_api_port_binding_mode(self.port_binding)

        # Check port allocation
        if not self.port_allocation:
            if self.port_binding == 'dynamic' or self.port_binding == 'ephemeral':
                results['port_allocation'] = 'n/a'
            elif self.port_binding == 'static':
                if pg_config.autoExpand:
                    results['port_allocation'] = 'elastic'
                else:
                    results['port_allocation'] = 'fixed'
        else:
            results['port_allocation'] = self.port_allocation
        if self.port_binding == 'static':
            if self.port_allocation is None or self.port_allocation == 'elastic':
                auto_expand = True
            elif self.port_allocation == 'fixed':
                auto_expand = False
            if pg_config.autoExpand != auto_expand:
                changed = True
                changed_list.append("port allocation")
                if pg_config.autoExpand:
                    results['port_allocation_previous'] = 'elastic'
                else:
                    results['port_allocation_previous'] = 'fixed'
                pg_spec.autoExpand = auto_expand

        # Check description
        results['description'] = self.description
        if pg_config.description != self.description:
            changed = True
            changed_list.append("description")
            results['description_previous'] = pg_config.description
            if self.description is None:
                # need to use empty string; will be set to None by API
                pg_spec.description = ''
            else:
                pg_spec.description = self.description

        # Check port policies
        results['adv_reset_at_disconnect'] = self.pp_reset
        results['adv_block_ports'] = self.pp_block_ports
        results['adv_traffic_shaping'] = self.pp_shaping
        results['adv_vendor_conf'] = self.pp_vendor_conf
        results['adv_vlan'] = self.pp_vlan
        results['adv_uplink_teaming'] = self.pp_uplink_teaming
        results['adv_network_rp'] = self.pp_network_rp
        results['adv_security'] = self.pp_security
        results['adv_netflow'] = self.pp_netflow
        results['adv_traffic_filtering'] = self.pp_traffic_filter
        (pg_policy_spec, changed_policy, reset_at_disconnect, block_override, shaping_override,
         vendor_config_override, vlan_override, uplink_teaming_override, network_rp_override,
         security_override, netflow_override, traffic_filter_override) = self.check_port_policy_config(pg_config)
        if changed_policy:
            changed = True
            changed_list.append("port policies")
            if reset_at_disconnect:
                results['adv_reset_at_disconnect_previous'] = pg_config.policy.portConfigResetAtDisconnect
            if block_override:
                results['adv_block_ports_previous'] = pg_config.policy.blockOverrideAllowed
            if shaping_override:
                results['adv_traffic_shaping_previous'] = pg_config.policy.shapingOverrideAllowed
            if vendor_config_override:
                results['adv_vendor_conf_previous'] = pg_config.policy.vendorConfigOverrideAllowed
            if vlan_override:
                results['adv_vlan_previous'] = pg_config.policy.vlanOverrideAllowed
            if uplink_teaming_override:
                results['adv_uplink_teaming_previous'] = pg_config.policy.uplinkTeamingOverrideAllowed
            if network_rp_override:
                results['adv_network_rp_previous'] = pg_config.policy.networkResourcePoolOverrideAllowed
            if security_override:
                results['adv_security_previous'] = pg_config.policy.securityPolicyOverrideAllowed
            if netflow_override:
                results['adv_netflow_previous'] = pg_config.policy.ipfixOverrideAllowed
            if traffic_filter_override:
                results['adv_traffic_filtering_previous'] = pg_config.policy.trafficFilterOverrideAllowed
            pg_spec.policy = pg_policy_spec

        pg_spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()

        # TODO: Check Traffic shaping

        # Check VLAN
        if self.vlan_id == 0:
            results['vlan_id'] = 0
            if isinstance(pg_config.defaultPortConfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec):
                if pg_config.defaultPortConfig.vlan.vlanId != 0:
                    changed_vlan = True
            elif isinstance(pg_config.defaultPortConfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec):
                changed_vlan = True
                results['vlan_trunk_range_previous'] = self.get_current_trunk_vlan_range(pg_config)
            elif isinstance(pg_config.defaultPortConfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.PvlanSpec):
                changed_vlan = True
                results['private_vlan_id_previous'] = pg_config.defaultPortConfig.vlan.pvlanId
            if changed_vlan:
                changed = True
                changed_list.append("vlan")
                pg_spec.defaultPortConfig.vlan = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec()
                pg_spec.defaultPortConfig.vlan.vlanId = 0
        # NOTE: 'vlan_trunk' option is deprecated. Will be removed in 2.11
        elif self.vlan_trunk or self.vlan_trunk_range:
            results['vlan_trunk_range'] = self.vlan_trunk_range
            if isinstance(pg_config.defaultPortConfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec):
                changed_vlan = True
                results['vlan_id_previous'] = pg_config.defaultPortConfig.vlan.vlanId
            elif isinstance(pg_config.defaultPortConfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec):
                trunk_vlan_spec, changed_vlan_trunk_range = self.check_trunk_vlan_config(pg_config)
                if changed_vlan_trunk_range:
                    results['vlan_trunk_range_previous'] = self.get_current_trunk_vlan_range(pg_config)
                    pg_spec.defaultPortConfig.vlan = trunk_vlan_spec
            elif isinstance(pg_config.defaultPortConfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.PvlanSpec):
                changed_vlan = True
                results['private_vlan_id_previous'] = pg_config.defaultPortConfig.vlan.pvlanId
            if changed_vlan or changed_vlan_trunk_range:
                changed = True
                changed_list.append("vlan")
                if not changed_vlan_trunk_range:
                    result = self.check_trunk_vlan_config(pg_config=None)
                    pg_spec.defaultPortConfig.vlan = result[0]
        elif self.private_vlan_id:
            if self.dv_switch.config.pvlanConfig:
                results['private_vlan_id'] = self.private_vlan_id
                if isinstance(pg_config.defaultPortConfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec):
                    changed_vlan = True
                    results['vlan_id_previous'] = pg_config.defaultPortConfig.vlan.vlanId
                elif isinstance(pg_config.defaultPortConfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec):
                    changed_vlan = True
                    results['vlan_trunk_range_previous'] = self.get_current_trunk_vlan_range(pg_config)
                elif isinstance(pg_config.defaultPortConfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.PvlanSpec):
                    if pg_config.defaultPortConfig.vlan.pvlanId != int(self.private_vlan_id):
                        changed_vlan = True
                        results['private_vlan_id_previous'] = pg_config.defaultPortConfig.vlan.pvlanId
                if changed_vlan:
                    changed = True
                    changed_list.append("vlan")
                    pg_spec.defaultPortConfig.vlan = vim.dvs.VmwareDistributedVirtualSwitch.PvlanSpec()
                    pg_spec.defaultPortConfig.vlan.pvlanId = int(self.private_vlan_id)
            else:
                self.module.fail_json(msg="Private VLAN is not configured for this distributed switch!")
        elif self.vlan_id:
            results['vlan_id'] = self.vlan_id
            if isinstance(pg_config.defaultPortConfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec):
                if pg_config.defaultPortConfig.vlan.vlanId != int(self.vlan_id):
                    changed_vlan = True
                    results['vlan_id_previous'] = pg_config.defaultPortConfig.vlan.vlanId
            elif isinstance(pg_config.defaultPortConfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec):
                changed_vlan = True
                results['vlan_trunk_range_previous'] = self.get_current_trunk_vlan_range(pg_config)
            elif isinstance(pg_config.defaultPortConfig.vlan, vim.dvs.VmwareDistributedVirtualSwitch.PvlanSpec):
                changed_vlan = True
                results['private_vlan_id_previous'] = pg_config.defaultPortConfig.vlan.pvlanId
            if changed_vlan:
                changed = True
                changed_list.append("vlan")
                pg_spec.defaultPortConfig.vlan = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec()
                pg_spec.defaultPortConfig.vlan.vlanId = int(self.vlan_id)
        if changed_vlan:
            pg_spec.defaultPortConfig.vlan.inherited = False

        # Check security
        results['sec_promiscuous_mode'] = self.sec_promiscuous_mode
        results['sec_mac_changes'] = self.sec_mac_changes
        results['sec_forged_transmits'] = self.sec_forged_transmits
        sec_spec, changed_security, promiscuous_mode_previous, mac_changes_previous, forged_transmits_previous = \
            self.check_security_config(pg_config=pg_config)
        pg_spec.defaultPortConfig.securityPolicy = sec_spec
        if changed_security:
            changed = True
            changed_list.append("security")
            results['sec_promiscuous_mode_previous'] = promiscuous_mode_previous
            results['sec_mac_changes_previous'] = mac_changes_previous
            results['sec_forged_transmits_previous'] = forged_transmits_previous

        # Check network resource pool
        results['network_rp'] = self.network_resource_pool
        current_network_rp_key = pg_config.defaultPortConfig.networkResourcePoolKey.value
        if self.network_resource_pool == 'default':
            if current_network_rp_key != '-1':
                changed = True
                changed_list.append("network resource pool")
                if current_network_rp_key == '-1':
                    results['network_rp_previous'] = 'default'
                else:
                    results['network_rp_previous'] = self.find_network_rp_by_key(current_network_rp_key).name
                pg_spec.defaultPortConfig.networkResourcePoolKey = vim.StringPolicy(inherited=False, value='-1')
        else:
            network_resource_pool = self.find_network_rp_by_name(self.network_resource_pool)
            if network_resource_pool is None:
                self.module.fail_json(msg="Network resource pool '%s' was not found" % self.network_resource_pool)
            if current_network_rp_key != network_resource_pool.key:
                changed = True
                changed_list.append("network resource pool")
                if current_network_rp_key == '-1':
                    results['network_rp_previous'] = 'default'
                else:
                    results['network_rp_previous'] = self.find_network_rp_by_key(current_network_rp_key).name
                pg_spec.defaultPortConfig.networkResourcePoolKey = vim.StringPolicy(
                    inherited=False, value=network_resource_pool.key
                )

        # Check teaming policy
        results['load_balancing'] = self.teaming_load_balancing
        if pg_config.defaultPortConfig.uplinkTeamingPolicy.policy.value != self.teaming_load_balancing:
            changed_teaming = True
            changed_list.append("load balancing")
            results['load_balancing_previous'] = pg_config.defaultPortConfig.uplinkTeamingPolicy.policy.value
        # Check teaming notify switches
        results['notify'] = self.teaming_notify_switches
        if pg_config.defaultPortConfig.uplinkTeamingPolicy.notifySwitches.value != self.teaming_notify_switches:
            changed_teaming = True
            changed_list.append("notify switches")
            results['notify_previous'] = pg_config.defaultPortConfig.uplinkTeamingPolicy.notifySwitches.value
        # Check failback
        results['failback'] = self.teaming_failback
        # this option is called 'failback' in the vSphere Client
        # rollingOrder also uses the opposite value displayed in the client
        if pg_config.defaultPortConfig.uplinkTeamingPolicy.rollingOrder.value is self.teaming_failback:
            changed_teaming = True
            changed_list.append("failback")
            results['failback_previous'] = not pg_config.defaultPortConfig.uplinkTeamingPolicy.rollingOrder.value
        # Check teaming failover order
        active_uplinks = pg_config.defaultPortConfig.uplinkTeamingPolicy.uplinkPortOrder.activeUplinkPort
        standby_uplinks = pg_config.defaultPortConfig.uplinkTeamingPolicy.uplinkPortOrder.standbyUplinkPort
        if self.teaming_failover_order_active is None and self.teaming_failover_order_standby is None:
            # Set failover order to default
            self.teaming_failover_order_active = \
                self.dv_switch.config.defaultPortConfig.uplinkTeamingPolicy.uplinkPortOrder.activeUplinkPort
            self.teaming_failover_order_standby = \
                self.dv_switch.config.defaultPortConfig.uplinkTeamingPolicy.uplinkPortOrder.standbyUplinkPort
        # active uplinks
        results['failover_active'] = self.teaming_failover_order_active
        if active_uplinks != self.teaming_failover_order_active:
            changed_teaming = changed_failover_order = True
            changed_list.append("failover order active")
            results['failover_active_previous'] = active_uplinks
        # standby uplinks
        results['failover_standby'] = self.teaming_failover_order_standby
        if standby_uplinks != self.teaming_failover_order_standby:
            changed_teaming = changed_failover_order = True
            changed_list.append("failover order standby")
            results['failover_standby_previous'] = standby_uplinks
        # Check teaming failure detection
        results['failure_detection'] = self.teaming_failure_detection
        if self.teaming_failure_detection == "link_status_only":
            if pg_config.defaultPortConfig.uplinkTeamingPolicy.failureCriteria.checkBeacon.value is True:
                changed_teaming = True
                changed_list.append("network failure detection")
                results['failure_detection_previous'] = "beacon_probing"
        elif self.teaming_failure_detection == "beacon_probing":
            if pg_config.defaultPortConfig.uplinkTeamingPolicy.failureCriteria.checkBeacon.value is False:
                changed_teaming = True
                changed_list.append("network failure detection")
                results['failure_detection_previous'] = "link_status_only"

        if changed_teaming:
            changed = True
            teaming_policy = vim.dvs.VmwareDistributedVirtualSwitch.UplinkPortTeamingPolicy()
            teaming_policy.policy = vim.StringPolicy(inherited=False, value=self.teaming_load_balancing)
            teaming_policy.failureCriteria = vim.dvs.VmwareDistributedVirtualSwitch.FailureCriteria()
            if self.teaming_failure_detection == "link_status_only":
                teaming_policy.failureCriteria.checkBeacon = vim.BoolPolicy(inherited=False, value=False)
            elif self.teaming_failure_detection == "beacon_probing":
                teaming_policy.failureCriteria.checkBeacon = vim.BoolPolicy(inherited=False, value=True)
            # Deprecated since VI API 5.1. The system default (true) will be used
            teaming_policy.reversePolicy = vim.BoolPolicy(inherited=False, value=True)
            teaming_policy.notifySwitches = vim.BoolPolicy(inherited=False, value=self.teaming_notify_switches)
            # this option is called 'failback' in the vSphere Client
            # rollingOrder also uses the opposite value displayed in the client
            teaming_policy.rollingOrder = vim.BoolPolicy(inherited=False, value=not self.teaming_failback)
            teaming_policy.uplinkPortOrder = vim.dvs.VmwareDistributedVirtualSwitch.UplinkPortOrderPolicy()
            if changed_failover_order:
                teaming_policy.uplinkPortOrder.activeUplinkPort = self.teaming_failover_order_active
                teaming_policy.uplinkPortOrder.standbyUplinkPort = self.teaming_failover_order_standby
            else:
                teaming_policy.uplinkPortOrder.activeUplinkPort = active_uplinks
                teaming_policy.uplinkPortOrder.standbyUplinkPort = standby_uplinks
            pg_spec.defaultPortConfig.uplinkTeamingPolicy = teaming_policy

        # Check Monitoring - NetFlow
        results['netflow_enabled'] = self.netflow_enabled
        netflow_spec, changed_netflow, netflow_previous = self.check_netflow_policy_config(pg_config)
        if changed_netflow:
            changed = True
            changed_list.append("netflow")
            results['netflow_enabled_previous'] = netflow_previous
            pg_spec.defaultPortConfig.ipfixEnabled = netflow_spec

        # TODO: Check Traffic filtering and marking

        # Check Misc. - Block all ports
        results['block_all_ports'] = self.block_all_ports
        blocked_spec, changed_blocked, blocked_previous = self.check_blocked_policy_config(pg_config)
        if changed_blocked:
            changed = True
            changed_list.append("block all ports")
            results['block_all_ports_previous'] = blocked_previous
            pg_spec.defaultPortConfig.blocked = blocked_spec

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
                    task = self.dvs_portgroup.ReconfigureDVPortgroup_Task(pg_spec)
                    wait_for_task(task)
                except TaskError as invalid_argument:
                    self.module.fail_json(msg="Failed to update portgroup : %s" % to_native(invalid_argument))
        else:
            message = "Portgroup already configured properly"
        results['changed'] = changed
        results['result'] = message

        self.module.exit_json(**results)


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            switch=dict(type='str', required=True, aliases=['switch_name']),
            portgroup=dict(type='str', required=True, aliases=['portgroup_name']),
            description=dict(type='str', aliases=['portgroup_description']),
            vlan_id=dict(type='int', default=0),
            vlan_trunk_range=dict(type='list'),
            private_vlan_id=dict(type='int'),
            num_ports=dict(type='int', aliases=['ports']),
            network_resource_pool=dict(type='str', default='default'),
            port_binding=dict(type='str', default='static', choices=['static', 'dynamic', 'ephemeral']),
            port_allocation=dict(type='str', choices=['fixed', 'elastic']),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            security=dict(
                type='dict',
                options=dict(
                    promiscuous_mode=dict(type='bool', default=False, aliases=['promiscuous']),
                    forged_transmits=dict(type='bool', default=False),
                    mac_changes=dict(type='bool', default=False)
                ),
                default=dict(
                    promiscuous_mode=False,
                    forged_transmits=False,
                    mac_changes=False
                ),
                aliases=['network_policy', 'security_policy']
            ),
            teaming=dict(
                type='dict',
                options=dict(
                    load_balancing=dict(
                        type='str',
                        default='loadbalance_srcid',
                        choices=[
                            'loadbalance_ip',
                            'loadbalance_srcmac',
                            'loadbalance_srcid',
                            'loadbalance_loadbased',
                            'failover_explicit',
                        ],
                        aliases=['load_balancing_policy'],
                    ),
                    network_failure_detection=dict(
                        type='str',
                        choices=['link_status_only', 'beacon_probing']
                    ),
                    notify_switches=dict(type='bool', default=True),
                    failback=dict(type='bool', default=True, aliases=['rolling_order']),
                    active_uplinks=dict(type='list'),
                    standby_uplinks=dict(type='list'),
                ),
                default=dict(
                    network_failure_detection='link_status_only',
                    notify_switches=True,
                    failback=True,
                    load_balancing='loadbalance_srcid',
                ),
                aliases=['teaming_policy']
            ),
            advanced=dict(
                type='dict',
                options=dict(
                    block_override=dict(type='bool', default=True),
                    netflow_override=dict(type='bool', default=False, aliases=['ipfix_override']),
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
                    netflow_override=False,
                    network_rp_override=False,
                    port_config_reset_at_disconnect=True,
                    security_override=False,
                    shaping_override=False,
                    traffic_filter_override=False,
                    uplink_teaming_override=False,
                    vendor_config_override=False,
                    vlan_override=False
                ),
                aliases=['port_policy']
            ),
            netflow_enabled=dict(type='bool', default=False),
            block_all_ports=dict(type='bool', default=False),
            # TODO: traffic shaping
            # TODO: traffic filtering and marking
            # NOTE: The below parameters are deprecated starting from Ansible v2.11
            vlan_trunk=dict(type='bool', default=False, removed_in_version=2.11),
            portgroup_type=dict(
                type='str', choices=['earlyBinding', 'lateBinding', 'ephemeral'], removed_in_version=2.11
            ),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['vlan_id', 'vlan_trunk_range', 'private_vlan_id']
        ],
        supports_check_mode=True
    )

    vmware_dvs_portgroup = VMwareDvsPortgroup(module)
    vmware_dvs_portgroup.process_state()


if __name__ == '__main__':
    main()
