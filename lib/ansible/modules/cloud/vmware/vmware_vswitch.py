#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2018, Ansible Project
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

DOCUMENTATION = '''
---
module: vmware_vswitch
short_description: Manage a VMware Standard Switch to an ESXi host.
description:
- This module can be used to add, remove and update a VMware Standard Switch (vSS) to an ESXi host.
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
- Russell Teague (@mtnbikenc)
- Abhijeet Kasurde (@Akasurde)
- Christian Kotte (@ckotte)
notes:
- Tested on vSphere 5.5 and 6.5
- Complete configuration only tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  switch:
    description:
    - vSwitch name to add.
    - Alias C(switch) was added in version 2.4.
    - Alias C(vswitch) was added in version 2.8.
    type: str
    required: yes
    aliases: [ 'switch_name', 'vswitch' ]
  nics:
    description:
    - A list of vmnic names or vmnic name to attach to the vSwitch.
    - Alias C(nics) was added in version 2.4.
    aliases: [ 'nic_name', 'adapters' ]
    type: dict
    default: []
  num_ports:
    description:
    - Number of ports to configure on vSwitch.
    - The vSphere Client shows the value for the number of ports as elastic from vSphere 5.5 and above.
    - Other tools like esxcli might show the number of ports as 1536 or 5632.
    - See U(https://kb.vmware.com/s/article/2064511) for more details.
    - Preconfigured switches and switches created via GUI use 64, 128, or 5632 ports by default.
    - Alias C(ports) was added in version 2.8.
    type: int
    default: 128
    aliases: [ 'number_of_ports', 'ports' ]
  mtu:
    description:
    - MTU to configure on the vSwitch.
    type: int
    default: 1500
  security:
    description:
    - Network policy specifies layer 2 security settings for a
      switch such as promiscuous mode, where guest adapter listens
      to all the packets, MAC address changes and forged transmits.
    - Dictionary which configures the different security values for a switch.
    - 'Valid attributes are:'
    - '- C(promiscuous_mode) (bool): indicates whether promiscuous mode is allowed. (default: false)'
    - '- C(forged_transmits) (bool): indicates whether forged transmits are allowed. (default: true)'
    - '- C(mac_changes) (bool): indicates whether mac changes are allowed. (default: true)'
    required: False
    version_added: "2.8"
    type: dict
    default: {
        mac_changes: true,
        promiscuous_mode: false,
        forged_transmits: true,
    }
    aliases: [ 'security_policy' ]
  teaming:
    description:
    - Dictionary which configures teaming for the switch.
    - 'Valid attributes are:'
    - '- C(load_balancing) (string): Network adapter teaming policy. (default: loadbalance_srcid)'
    - '   - choices: [ loadbalance_ip, loadbalance_srcmac, loadbalance_srcid, failover_explicit ]'
    - '- C(network_failure_detection) (string): Network failure detection. (default: link_status_only)'
    - '   - choices: [ link_status_only, beacon_probing ]'
    - '- C(notify_switches) (bool): Indicate whether or not to notify the physical switch if a link fails. (default: True)'
    - '- C(failback) (bool): Indicate whether or not to use a failback when restoring links. (default: True)'
    - '- C(active_adapters) (list): List of active adapters used for load balancing.'
    - '- C(standby_adapters) (list): List of standby adapters used for failover.'
    - '- All vmnics are used as active adapters if C(active_adapters) and C(standby_adapters) are not defined.'
    required: False
    version_added: '2.8'
    type: dict
    default: {
        'load_balancing': 'loadbalance_srcid',
        'notify_switches': True,
        'failback': True,
    }
    aliases: [ 'teaming_policy' ]
  traffic_shaping:
    description:
    - Dictionary which configures traffic shaping for the switch.
    - 'Valid attributes are:'
    - '- C(enabled) (bool): Status of Traffic Shaping Policy. (default: False)'
    - '- C(average_bandwidth) (int): Average bandwidth (kbit/s). (default: None)'
    - '- C(peak_bandwidth) (int): Peak bandwidth (kbit/s). (default: None)'
    - '- C(burst_size) (int): Burst size (KB). (default: None)'
    required: False
    version_added: '2.8'
    type: dict
    default: {
        'enabled': False,
        'average_bandwidth': 100000,
        'peak_bandwidth': 100000,
        'burst_size': 102400,
    }
  state:
    description:
    - Add or remove the switch.
    type: str
    default: present
    choices: [ absent, present ]
  esxi_hostname:
    description:
    - Manage the vSwitch using this ESXi host system.
    type: str
    version_added: "2.5"
    aliases: [ 'host' ]
extends_documentation_fragment:
- vmware.documentation
'''

EXAMPLES = '''
- name: Add a Standard vSwitch
  vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    switch: vswitch_name
    adapters: vmnic_name
    mtu: 9000
  delegate_to: localhost

- name: Add a Standard vSwitch without any physical NIC attached
  vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    switch: vswitch_0001
    mtu: 9000
  delegate_to: localhost

- name: Add a Standard vSwitch with multiple NICs
  vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    switch: vmware_vswitch_0004
    adapters:
      - vmnic1
      - vmnic2
    mtu: 9000
  delegate_to: localhost

- name: Add a Standard vSwitch to a specific host system
  vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    esxi_hostname: DC0_H0
    switch_name: vswitch_001
    adapters:
      - vmnic0
    mtu: 9000
  delegate_to: localhost

- name: Configure all settings of a Standard vSwitch
  vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    esxi_hostname: DC0_H0
    switch: vSwitch3
    adapters:
      - vmnic6
      - vmnic7
    mtu: 9000
    security:
      promiscuous_mode: False
      forged_transmits: False
      mac_changes: False
    traffic_shaping:
      enabled: True
      average_bandwidth: 100000
      peak_bandwidth: 100000
      burst_size: 102400
    teaming:
      load_balancing: loadbalance_srcid
      network_failure_detection: link_status_only
      notify_switches: True
      failback: True
      active_adapters:
        - vmnic6
      standby_adapters:
        - vmnic7
  delegate_to: localhost
'''

RETURN = """
result:
    description: information about performed operation
    returned: always
    type: string
    sample: {
        "changed": false,
        "failback": true,
        "failover_active": ["vmnic0", "vmnic1"],
        "failover_standby": [],
        "failure_detection": "link_status_only",
        "load_balancing": "loadbalance_srcid",
        "mtu": 64,
        "notify_switches": true,
        "num_ports": 64,
        "pnics": ["vmnic0", "vmnic1"],
        "result": "vSwitch already configured properly",
        "sec_forged_transmits": false,
        "sec_mac_changes": false,
        "sec_promiscuous_mode": false,
        "traffic_shaping": false,
        "vswitch": "vSwitch0"
    }
"""

try:
    from pyVmomi import vim, vmodl
    from textwrap import dedent
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native


class VMwareHostVirtualSwitch(PyVmomi):
    """Manage virtual switch"""

    def __init__(self, module):
        super(VMwareHostVirtualSwitch, self).__init__(module)
        self.host_system = None
        self.switch_object = None
        self.switch = module.params['switch']
        self.number_of_ports = module.params['num_ports']
        if module.params['nics'] is None:
            self.nics = []
        else:
            self.nics = module.params['nics']
        self.nics = module.params['nics']
        self.mtu = module.params['mtu']
        self.sec_promiscuous_mode = self.params['security'].get('promiscuous_mode')
        self.sec_forged_transmits = self.params['security'].get('forged_transmits')
        self.sec_mac_changes = self.params['security'].get('mac_changes')
        self.ts_enabled = self.params['traffic_shaping'].get('enabled')
        self.ts_average_bandwidth = self.params['traffic_shaping'].get('average_bandwidth')
        self.ts_peak_bandwidth = self.params['traffic_shaping'].get('peak_bandwidth')
        self.ts_burst_size = self.params['traffic_shaping'].get('burst_size')
        self.teaming_load_balancing = self.params['teaming'].get('load_balancing')
        self.teaming_failure_detection = self.params['teaming'].get('network_failure_detection')
        self.teaming_notify_switches = self.params['teaming'].get('notify_switches')
        self.teaming_failback = self.params['teaming'].get('failback')
        self.teaming_failover_order_active = self.params['teaming'].get('active_adapters')
        self.teaming_failover_order_standby = self.params['teaming'].get('standby_adapters')
        if self.teaming_failover_order_active or self.teaming_failover_order_standby:
            if self.teaming_failover_order_active is None:
                # set all nics to active by default
                self.teaming_failover_order_active = module.params['nics']
            if self.teaming_failover_order_standby is None:
                self.teaming_failover_order_standby = []
        else:
            # set all nics to active by default
            self.teaming_failover_order_active = module.params['nics']
            self.teaming_failover_order_standby = []
        self.state = module.params['state']
        esxi_hostname = module.params['esxi_hostname']

        hosts = self.get_all_host_objs(esxi_host_name=esxi_hostname)
        if hosts:
            self.host_system = hosts[0]
        else:
            self.module.fail_json(msg="Failed to get details of ESXi server. Please specify esxi_hostname.")

        if self.params.get('state') == 'present':
            # Gather information about all vSwitches
            network_manager = self.host_system.configManager.networkSystem
            available_pnic = [pnic.device for pnic in network_manager.networkInfo.pnic]
            self.available_vswitches = dict()
            for available_vswitch in network_manager.networkInfo.vswitch:
                vswitch_security = dict(
                    allowPromiscuous=available_vswitch.spec.policy.security.allowPromiscuous,
                    macChanges=available_vswitch.spec.policy.security.macChanges,
                    forgedTransmits=available_vswitch.spec.policy.security.forgedTransmits,
                )
                vswitch_teaming = dict(
                    policy=available_vswitch.spec.policy.nicTeaming.policy,
                    notifySwitches=available_vswitch.spec.policy.nicTeaming.notifySwitches,
                    rollingOrder=available_vswitch.spec.policy.nicTeaming.rollingOrder,
                    reversePolicy=available_vswitch.spec.policy.nicTeaming.reversePolicy,
                    failover_order_active_adapters=available_vswitch.spec.policy.nicTeaming.nicOrder.activeNic,
                    failover_order_standby_adapters=available_vswitch.spec.policy.nicTeaming.nicOrder.standbyNic,
                )
                vswitch_failure = dict(
                    checkSpeed=available_vswitch.spec.policy.nicTeaming.failureCriteria.checkSpeed,
                    speed=available_vswitch.spec.policy.nicTeaming.failureCriteria.speed,
                    checkDuplex=available_vswitch.spec.policy.nicTeaming.failureCriteria.checkDuplex,
                    fullDuplex=available_vswitch.spec.policy.nicTeaming.failureCriteria.fullDuplex,
                    checkErrorPercent=available_vswitch.spec.policy.nicTeaming.failureCriteria.checkErrorPercent,
                    percentage=available_vswitch.spec.policy.nicTeaming.failureCriteria.percentage,
                    checkBeacon=available_vswitch.spec.policy.nicTeaming.failureCriteria.checkBeacon,
                )
                vswitch_ts = dict(
                    enabled=available_vswitch.spec.policy.shapingPolicy.enabled,
                    averageBandwidth=available_vswitch.spec.policy.shapingPolicy.averageBandwidth,
                    peakBandwidth=available_vswitch.spec.policy.shapingPolicy.peakBandwidth,
                    burstSize=available_vswitch.spec.policy.shapingPolicy.burstSize,
                )
                vswitch_offload = dict(
                    csumOffload=available_vswitch.spec.policy.offloadPolicy.csumOffload,
                    tcpSegmentation=available_vswitch.spec.policy.offloadPolicy.tcpSegmentation,
                    zeroCopyXmit=available_vswitch.spec.policy.offloadPolicy.zeroCopyXmit,
                )
                used_pnic = []
                for pnic in available_vswitch.pnic:
                    # vSwitch contains all PNICs as string in format of 'key-vim.host.PhysicalNic-vmnic0'
                    m_pnic = pnic.split("-", 3)[-1]
                    used_pnic.append(m_pnic)
                self.available_vswitches[available_vswitch.name] = dict(
                    pnic=used_pnic,
                    mtu=available_vswitch.mtu,
                    num_ports=available_vswitch.spec.numPorts,
                    security=vswitch_security,
                    teaming=vswitch_teaming,
                    teaming_failure=vswitch_failure,
                    traffic_shaping=vswitch_ts,
                    offload=vswitch_offload,
                )
            if self.nics:
                for desired_pnic in self.nics:
                    if desired_pnic not in available_pnic:
                        # Check if pnic does not exists
                        self.module.fail_json(
                            msg="Specified Physical NIC '%s' does not exists on given ESXi '%s'." %
                            (desired_pnic, self.host_system.name)
                        )
                    for vswitch in self.available_vswitches:
                        if desired_pnic in self.available_vswitches[vswitch]['pnic'] and vswitch != self.switch:
                            # Check if pnic is already part of some other vSwitch
                            self.module.fail_json(
                                msg="Specified Physical NIC '%s' is already used by vSwitch '%s'." % (desired_pnic, vswitch)
                            )

    def process_state(self):
        """Manage internal state of vSwitch"""
        vswitch_states = {
            'absent': {
                'present': self.state_destroy_vswitch,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'present': self.state_update_vswitch,
                'absent': self.state_create_vswitch,
            }
        }

        try:
            vswitch_states[self.state][self.check_vswitch_configuration()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))

    def state_create_vswitch(self):
        """Create vSwitch"""
        results = dict(changed=False, result="")
        results['vswitch'] = self.switch

        vss_spec = vim.host.VirtualSwitch.Specification()
        vss_spec.numPorts = self.number_of_ports
        results['num_ports'] = self.number_of_ports
        vss_spec.mtu = self.mtu
        results['mtu'] = self.mtu
        if self.nics:
            vss_spec.bridge = vim.host.VirtualSwitch.BondBridge()
            vss_spec.bridge.nicDevice = self.nics
            results['pnics'] = self.nics
        # doesn't need to be set; default values (maybe useful in the future)
        # vss_spec.bridge.beacon = vim.host.VirtualSwitch.BeaconConfig()
        # vss_spec.bridge.beacon.interval = 1
        # vss_spec.bridge.linkDiscoveryProtocolConfig = vim.host.LinkDiscoveryProtocolConfig()
        # vss_spec.bridge.linkDiscoveryProtocolConfig.protocol = 'cdp'
        # vss_spec.bridge.linkDiscoveryProtocolConfig.operation = 'listen'
        vss_spec.policy = vim.host.NetworkPolicy()
        vss_spec.policy.security = vim.host.NetworkPolicy.SecurityPolicy()
        vss_spec.policy.security.allowPromiscuous = self.sec_promiscuous_mode
        vss_spec.policy.security.macChanges = self.sec_mac_changes
        vss_spec.policy.security.forgedTransmits = self.sec_forged_transmits
        results['sec_promiscuous_mode'] = self.sec_promiscuous_mode
        results['sec_mac_changes'] = self.sec_mac_changes
        results['sec_forged_transmits'] = self.sec_forged_transmits
        vss_spec.policy.offloadPolicy = vim.host.NetOffloadCapabilities()
        # The offload policy is deprecated since VI API 4.0. The system defaults will be used.
        vss_spec.policy.offloadPolicy.tcpSegmentation = True
        vss_spec.policy.offloadPolicy.zeroCopyXmit = True
        vss_spec.policy.offloadPolicy.csumOffload = True
        vss_spec.policy.shapingPolicy = vim.host.NetworkPolicy.TrafficShapingPolicy()
        vss_spec.policy.shapingPolicy.enabled = self.ts_enabled
        if self.ts_enabled:
            vss_spec.policy.shapingPolicy.averageBandwidth = self.ts_average_bandwidth * 1000
            vss_spec.policy.shapingPolicy.peakBandwidth = self.ts_peak_bandwidth * 1000
            vss_spec.policy.shapingPolicy.burstSize = self.ts_burst_size * 1024
            results['traffic_shaping'] = self.ts_enabled
        vss_spec.policy.nicTeaming = vim.host.NetworkPolicy.NicTeamingPolicy()
        vss_spec.policy.nicTeaming.policy = self.teaming_load_balancing
        results['load_balancing'] = self.teaming_load_balancing
        # Deprecated since VI API 5.1. The system default (true) will be used
        vss_spec.policy.nicTeaming.reversePolicy = True
        vss_spec.policy.nicTeaming.notifySwitches = self.teaming_notify_switches
        results['notify_switches'] = self.teaming_notify_switches
        # this option is called 'failback' in the vSphere Client
        # rollingOrder also uses the opposite value displayed in the client
        vss_spec.policy.nicTeaming.rollingOrder = not self.teaming_failback
        results['failback'] = self.teaming_failback
        vss_spec.policy.nicTeaming.nicOrder = vim.host.NetworkPolicy.NicOrderPolicy()
        vss_spec.policy.nicTeaming.nicOrder.activeNic = self.teaming_failover_order_active
        vss_spec.policy.nicTeaming.nicOrder.standbyNic = self.teaming_failover_order_standby
        results['failover_active'] = self.teaming_failover_order_active
        results['failover_standby'] = self.teaming_failover_order_standby
        vss_spec.policy.nicTeaming.failureCriteria = vim.host.NetworkPolicy.NicFailureCriteria()
        if self.teaming_failure_detection == "link_status_only":
            vss_spec.policy.nicTeaming.failureCriteria.checkBeacon = False
        elif self.teaming_failure_detection == "beacon_probing":
            vss_spec.policy.nicTeaming.failureCriteria.checkBeacon = True
        results['failure_detection'] = self.teaming_failure_detection
        # The following properties are deprecated since VI API 5.1. Default values are used
        vss_spec.policy.nicTeaming.failureCriteria.fullDuplex = False
        vss_spec.policy.nicTeaming.failureCriteria.percentage = 0
        vss_spec.policy.nicTeaming.failureCriteria.checkErrorPercent = False
        vss_spec.policy.nicTeaming.failureCriteria.checkDuplex = False
        vss_spec.policy.nicTeaming.failureCriteria.speed = 10
        vss_spec.policy.nicTeaming.failureCriteria.checkSpeed = 'minimum'
        if self.module.check_mode:
            results['changed'] = True
            results['result'] = "vSwitch would be created"
        else:
            try:
                network_mgr = self.host_system.configManager.networkSystem
                if network_mgr:
                    network_mgr.AddVirtualSwitch(
                        vswitchName=self.switch,
                        spec=vss_spec
                    )
                    results['changed'] = True
                    results['result'] = "vSwitch was created successfully"
                else:
                    self.module.fail_json(msg="Failed to find network manager for ESXi system")
            except vim.fault.AlreadyExists as already_exists:
                results['result'] = "vSwitch with name %s already exists: %s" % (
                    self.switch,
                    to_native(already_exists.msg)
                )
            except vim.fault.ResourceInUse as resource_used:
                self.module.fail_json(
                    msg="Failed to add vSwitch '%s' as physical network adapter being bridged is already in use: %s" %
                    (self.switch, to_native(resource_used.msg))
                )
            except vim.fault.HostConfigFault as host_config_fault:
                self.module.fail_json(
                    msg="Failed to add vSwitch '%s' due to host configuration fault : %s" %
                    (self.switch, to_native(host_config_fault.msg))
                )
            except vmodl.fault.InvalidArgument as invalid_argument:
                self.module.fail_json(msg=dedent("""
                    Failed to add vSwitch '%s', this can be due to either of following:
                     1. vSwitch Name exceeds the maximum allowed length,
                     2. Number of ports specified falls out of valid range,
                     3. Network policy is invalid,
                     4. Beacon configuration is invalid : %s
                    """) % (self.switch, to_native(invalid_argument.msg)))
            except vmodl.fault.SystemError as system_error:
                self.module.fail_json(
                    msg="Failed to add vSwitch '%s' due to : %s" % (self.switch, to_native(system_error.msg))
                )
        self.module.exit_json(**results)

    def state_exit_unchanged(self):
        """Declare exit without unchanged"""
        self.module.exit_json(changed=False)

    def state_destroy_vswitch(self):
        """Remove vSwitch from configuration"""
        results = dict(changed=False, result="")
        results['vswitch'] = self.switch_object.name
        if self.module.check_mode:
            results['changed'] = True
            results['result'] = "vSwitch would be removed"
        else:
            try:
                self.host_system.configManager.networkSystem.RemoveVirtualSwitch(self.switch_object.name)
                results['changed'] = True
                results['result'] = "vSwitch removed"
            except vim.fault.NotFound as vswitch_not_found:
                results['result'] = "vSwitch '%s' not available. %s" % (self.switch, to_native(vswitch_not_found.msg))
            except vim.fault.ResourceInUse as vswitch_in_use:
                self.module.fail_json(
                    msg="Failed to remove vSwitch '%s' as vSwitch is used by several virtual network adapters: %s" %
                    (self.switch, to_native(vswitch_in_use.msg))
                )
            except vim.fault.HostConfigFault as host_config_fault:
                self.module.fail_json(
                    msg="Failed to remove vSwitch '%s' due to host configuration fault : %s" %
                    (self.switch, to_native(host_config_fault.msg))
                )

        self.module.exit_json(**results)

    def state_update_vswitch(self):
        """Update vSwitch"""
        changed = changed_nics = changed_mtu = changed_ports = changed_security = \
            changed_traffic_shaping = changed_teaming = changed_teaming_failure = False
        changed_list = []
        results = dict(changed=changed)
        results['vswitch'] = self.switch
        vswitch_info = self.available_vswitches[self.switch]

        # Check pnics
        results['pnics'] = self.nics
        pnic_add = []
        # Check if pnics need to be added
        for desired_pnic in self.nics:
            if desired_pnic not in vswitch_info['pnic']:
                pnic_add.append(desired_pnic)
        # Check if pnics need to be removed
        pnic_remove = []
        for configured_pnic in vswitch_info['pnic']:
            if configured_pnic not in self.nics:
                pnic_remove.append(configured_pnic)
        # Check pnics - Update pnics
        desired_pnics = []
        if pnic_add or pnic_remove:
            changed = changed_nics = True
            results['pnics_previous'] = vswitch_info['pnic']
            desired_pnics = vswitch_info['pnic']
            if pnic_add:
                desired_pnics += pnic_add
            elif pnic_remove:
                for pnic in pnic_remove:
                    desired_pnics.remove(pnic)

        # Check ports
        results['num_ports'] = self.number_of_ports
        if vswitch_info['num_ports'] != self.number_of_ports:
            changed = changed_ports = True
            changed_list.append("Number of ports")
            results['num_ports_previous'] = vswitch_info['num_ports']

        # Check MTU
        results['mtu'] = self.number_of_ports
        if vswitch_info['mtu'] != self.mtu:
            changed = changed_mtu = True
            changed_list.append("MTU")
            results['mtu_previous'] = vswitch_info['mtu']

        # Check security settings
        results['sec_promiscuous_mode'] = self.sec_promiscuous_mode
        results['sec_mac_changes'] = self.sec_mac_changes
        results['sec_forged_transmits'] = self.sec_forged_transmits
        if vswitch_info['security']['allowPromiscuous'] != self.sec_promiscuous_mode:
            changed = changed_security = True
            changed_list.append("Promiscuous mode")
        if vswitch_info['security']['macChanges'] != self.sec_mac_changes:
            changed = changed_security = True
            changed_list.append("MAC address changes")
        if vswitch_info['security']['forgedTransmits'] != self.sec_forged_transmits:
            changed = changed_security = True
            changed_list.append("Forged transmits")
        if changed_security:
            results['sec_promiscuous_mode_previous'] = vswitch_info['security']['allowPromiscuous']
            results['sec_mac_changes_previous'] = vswitch_info['security']['macChanges']
            results['sec_forged_transmits_previous'] = vswitch_info['security']['forgedTransmits']

        # Check traffic shaping
        results['traffic_shaping'] = self.ts_enabled
        if vswitch_info['traffic_shaping']['enabled'] is not self.ts_enabled:
            changed = changed_traffic_shaping = True
            changed_list.append("Traffic shaping")
            results['traffic_shaping_previous'] = vswitch_info['traffic_shaping']['enabled']
        if self.ts_enabled:
            ts_average_bandwidth = self.ts_average_bandwidth * 1000
            ts_peak_bandwidth = self.ts_peak_bandwidth * 1000
            ts_burst_size = self.ts_burst_size * 1024
            results['traffic_shaping_avg_bandw'] = ts_average_bandwidth
            results['traffic_shaping_peak_bandw'] = ts_peak_bandwidth
            results['traffic_shaping_burst'] = ts_burst_size
            if vswitch_info['traffic_shaping']['averageBandwidth'] != self.ts_average_bandwidth:
                changed = changed_traffic_shaping = True
                changed_list.append("Average bandwidth")
                results['traffic_shaping_avg_bandw_previous'] = vswitch_info['traffic_shaping']['averageBandwidth']
            if vswitch_info['traffic_shaping']['peakBandwidth'] != self.ts_peak_bandwidth:
                changed = changed_traffic_shaping = True
                changed_list.append("Peak bandwidth")
                results['traffic_shaping_peak_bandw'] = vswitch_info['traffic_shaping']['peakBandwidth']
            if vswitch_info['traffic_previous']['burstSize'] != self.ts_burst_size:
                changed = changed_traffic_shaping = True
                changed_list.append("Burst size")
                results['traffic_shaping_burst_previous'] = vswitch_info['traffic_shaping']['burstSize']

        # Check teaming policy
        results['load_balancing'] = self.teaming_load_balancing
        if vswitch_info['teaming']['policy'] != self.teaming_load_balancing:
            changed = changed_teaming = True
            changed_list.append("Load balancing")
            results['load_balancing_previous'] = vswitch_info['teaming']['policy']

        # Check teaming notify switches
        results['notify_switches'] = self.teaming_notify_switches
        if vswitch_info['teaming']['notifySwitches'] != self.teaming_notify_switches:
            changed = changed_teaming = True
            changed_list.append("Notify switches")
            results['notify_switches_previous'] = vswitch_info['teaming']['notifySwitches']

        # Check failback
        # this option is called 'failback' in the vSphere Client
        # rollingOrder also uses the opposite value displayed in the client
        results['failback'] = self.teaming_failback
        if vswitch_info['teaming']['rollingOrder'] is self.teaming_failback:
            changed = changed_teaming = True
            changed_list.append("Failback")
            results['failback_previous'] = not vswitch_info['teaming']['rollingOrder']

        # Check teaming failover order (active NICs)
        results['failover_active'] = self.teaming_failover_order_active
        if vswitch_info['teaming']['failover_order_active_adapters'] != self.teaming_failover_order_active:
            changed = changed_teaming = True
            changed_list.append("Failover order active")
            results['failover_active_previous'] = vswitch_info['teaming']['failover_order_active_adapters']

        # Check teaming failover order (standby NICs)
        results['failover_standby'] = self.teaming_failover_order_standby
        if vswitch_info['teaming']['failover_order_standby_adapters'] != self.teaming_failover_order_standby:
            changed = changed_teaming = True
            changed_list.append("Failover order standby")
            results['failover_standby_previous'] = vswitch_info['teaming']['failover_order_standby_adapters']

        # Check teaming failure detection
        results['failure_detection'] = self.teaming_failure_detection
        if self.teaming_failure_detection == "link_status_only":
            if vswitch_info['teaming_failure']['checkBeacon'] is True:
                changed = changed_teaming_failure = True
                changed_list.append("Network failure detection")
                results['failure_detection_previous'] = "beacon_probing"
        elif self.teaming_failure_detection == "beacon_probing":
            if vswitch_info['teaming_failure']['checkBeacon'] is False:
                changed = changed_teaming_failure = True
                changed_list.append("Network failure detection")
                results['failure_detection_previous'] = "link_status_only"

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
                # We need to include all parameters if we want to configure the network policy to avoid InvalidArgument error
                vss_spec = vim.host.VirtualSwitch.Specification()
                if changed_ports:
                    vss_spec.numPorts = self.number_of_ports
                else:
                    vss_spec.numPorts = vswitch_info['num_ports']
                if changed_mtu:
                    vss_spec.mtu = self.mtu
                else:
                    vss_spec.mtu = vswitch_info['mtu']
                # update pnics with desired pnics
                if changed_nics and desired_pnics:
                    vss_spec.bridge = vim.host.VirtualSwitch.BondBridge()
                    # doesn't need to be set; default values (maybe useful in the future)
                    # vss_spec.bridge.beacon = vim.host.VirtualSwitch.BeaconConfig()
                    # vss_spec.bridge.beacon.interval = 1
                    # vss_spec.bridge.linkDiscoveryProtocolConfig = vim.host.LinkDiscoveryProtocolConfig()
                    # vss_spec.bridge.linkDiscoveryProtocolConfig.protocol = 'cdp'
                    # vss_spec.bridge.linkDiscoveryProtocolConfig.operation = 'listen'
                    vss_spec.bridge.nicDevice = desired_pnics
                # remove all pnics
                elif changed_nics and not desired_pnics:
                    # don't configure BondBridge and nicDevice
                    pass
                # use configured pnics
                elif changed_nics is False and not desired_pnics:
                    vss_spec.bridge = vim.host.VirtualSwitch.BondBridge()
                    vss_spec.bridge.nicDevice = vswitch_info['pnic']
                vss_spec.policy = vim.host.NetworkPolicy()
                vss_spec.policy.security = vim.host.NetworkPolicy.SecurityPolicy()
                if changed_security:
                    vss_spec.policy.security.allowPromiscuous = self.sec_promiscuous_mode
                    vss_spec.policy.security.macChanges = self.sec_mac_changes
                    vss_spec.policy.security.forgedTransmits = self.sec_forged_transmits
                else:
                    vss_spec.policy.security.allowPromiscuous = vswitch_info['security']['allowPromiscuous']
                    vss_spec.policy.security.macChanges = vswitch_info['security']['macChanges']
                    vss_spec.policy.security.forgedTransmits = vswitch_info['security']['forgedTransmits']
                vss_spec.policy.offloadPolicy = vim.host.NetOffloadCapabilities()
                # use existing values by default
                vss_spec.policy.offloadPolicy.tcpSegmentation = vswitch_info['offload']['tcpSegmentation']
                vss_spec.policy.offloadPolicy.zeroCopyXmit = vswitch_info['offload']['zeroCopyXmit']
                vss_spec.policy.offloadPolicy.csumOffload = vswitch_info['offload']['csumOffload']
                vss_spec.policy.shapingPolicy = vim.host.NetworkPolicy.TrafficShapingPolicy()
                if changed_traffic_shaping:
                    vss_spec.policy.shapingPolicy.enabled = self.ts_enabled
                    if self.ts_enabled:
                        vss_spec.policy.shapingPolicy.averageBandwidth = ts_average_bandwidth
                        vss_spec.policy.shapingPolicy.peakBandwidth = ts_peak_bandwidth
                        vss_spec.policy.shapingPolicy.burstSize = ts_burst_size
                else:
                    vss_spec.policy.shapingPolicy.enabled = vswitch_info['traffic_shaping']['enabled']
                    if vswitch_info['traffic_shaping']['enabled']:
                        vss_spec.policy.shapingPolicy.averageBandwidth = \
                            vswitch_info['traffic_shaping']['averageBandwidth'] * 1000
                        vss_spec.policy.shapingPolicy.peakBandwidth = \
                            vswitch_info['traffic_shaping']['peakBandwidth'] * 1000
                        vss_spec.policy.shapingPolicy.burstSize = \
                            vswitch_info['traffic_shaping']['burstSize'] * 1024
                vss_spec.policy.nicTeaming = vim.host.NetworkPolicy.NicTeamingPolicy()
                vss_spec.policy.nicTeaming.nicOrder = vim.host.NetworkPolicy.NicOrderPolicy()
                if changed_teaming:
                    vss_spec.policy.nicTeaming.policy = self.teaming_load_balancing
                    # Deprecated since VI API 5.1. The system default (true) will be used
                    vss_spec.policy.nicTeaming.reversePolicy = True
                    vss_spec.policy.nicTeaming.notifySwitches = self.teaming_notify_switches
                    # this option is called 'failback' in the vSphere Client
                    # rollingOrder also uses the opposite value displayed in the client
                    vss_spec.policy.nicTeaming.rollingOrder = not self.teaming_failback
                    vss_spec.policy.nicTeaming.nicOrder.activeNic = self.teaming_failover_order_active
                    vss_spec.policy.nicTeaming.nicOrder.standbyNic = self.teaming_failover_order_standby
                else:
                    vss_spec.policy.nicTeaming.policy = vswitch_info['teaming']['policy']
                    vss_spec.policy.nicTeaming.reversePolicy = vswitch_info['teaming']['reversePolicy']
                    vss_spec.policy.nicTeaming.notifySwitches = vswitch_info['teaming']['notifySwitches']
                    vss_spec.policy.nicTeaming.rollingOrder = vswitch_info['teaming']['rollingOrder']
                    vss_spec.policy.nicTeaming.nicOrder.activeNic = \
                        vswitch_info['teaming']['failover_order_active_adapters']
                    vss_spec.policy.nicTeaming.nicOrder.standbyNic = \
                        vswitch_info['teaming']['failover_order_standby_adapters']
                vss_spec.policy.nicTeaming.failureCriteria = vim.host.NetworkPolicy.NicFailureCriteria()
                if changed_teaming_failure:
                    if self.teaming_failure_detection == "link_status_only":
                        vss_spec.policy.nicTeaming.failureCriteria.checkBeacon = False
                    elif self.teaming_failure_detection == "beacon_probing":
                        vss_spec.policy.nicTeaming.failureCriteria.checkBeacon = True
                else:
                    vss_spec.policy.nicTeaming.failureCriteria.checkBeacon = \
                        vswitch_info['teaming_failure']['checkBeacon']
                # use existing values by default
                vss_spec.policy.nicTeaming.failureCriteria.fullDuplex = \
                    vswitch_info['teaming_failure']['fullDuplex']
                vss_spec.policy.nicTeaming.failureCriteria.percentage = \
                    vswitch_info['teaming_failure']['percentage']
                vss_spec.policy.nicTeaming.failureCriteria.checkErrorPercent = \
                    vswitch_info['teaming_failure']['checkErrorPercent']
                vss_spec.policy.nicTeaming.failureCriteria.checkDuplex = \
                    vswitch_info['teaming_failure']['checkDuplex']
                vss_spec.policy.nicTeaming.failureCriteria.speed = \
                    vswitch_info['teaming_failure']['speed']
                vss_spec.policy.nicTeaming.failureCriteria.checkSpeed = \
                    vswitch_info['teaming_failure']['checkSpeed']
                try:
                    network_mgr = self.host_system.configManager.networkSystem
                    if network_mgr:
                        network_mgr.UpdateVirtualSwitch(vswitchName=self.switch, spec=vss_spec)
                    else:
                        self.module.fail_json(msg="Failed to find network manager for ESXi system.")
                except vim.fault.ResourceInUse as resource_used:
                    self.module.fail_json(
                        msg="Failed to update vSwitch '%s' as physical network adapter being bridged "
                        "is already in use: %s" % (self.switch, to_native(resource_used.msg))
                    )
                except vim.fault.NotFound as not_found:
                    self.module.fail_json(
                        msg="Failed to update vSwitch with name '%s' as it does not exists: %s" %
                        (self.switch, to_native(not_found.msg))
                    )
                except vim.fault.HostConfigFault as host_config_fault:
                    self.module.fail_json(
                        msg="Failed to update vSwitch '%s' due to host configuration fault : %s" %
                        (self.switch, to_native(host_config_fault.msg))
                    )
                except vmodl.fault.InvalidArgument as invalid_argument:
                    self.module.fail_json(msg=dedent("""
                        Failed to update vSwitch '%s', this can be due to either of following :"
                         1. vSwitch Name exceeds the maximum allowed length,
                         2. Number of ports specified falls out of valid range,
                         3. Network policy is invalid,
                         4. Beacon configuration is invalid : %s
                        """) % (self.switch, to_native(invalid_argument.msg)))
                except vmodl.fault.NotSupported as not_supported:
                    self.module.fail_json(
                        msg="Failed to update vSwitch '%s' as network adapter teaming policy"
                        " is set but is not supported : %s" % (self.switch, to_native(not_supported.msg))
                    )
                except vmodl.fault.SystemError as system_error:
                    self.module.fail_json(
                        msg="Failed to update vSwitch '%s' due to : %s" % (self.switch, to_native(system_error.msg))
                    )
        else:
            message = "vSwitch already configured properly"
        results['changed'] = changed
        results['result'] = message

        self.module.exit_json(**results)

    def check_vswitch_configuration(self):
        """
        Check if vSwitch exists
        Returns: 'present' if vSwitch exists or 'absent' if not
        """
        self.switch_object = self.find_vswitch_by_name(self.host_system, self.switch)
        if self.switch_object is None:
            return 'absent'
        return 'present'

    @staticmethod
    def find_vswitch_by_name(host, vswitch_name):
        """
        Find and return vSwitch managed object
        Args:
            host: Host system managed object
            vswitch_name: Name of vSwitch to find

        Returns: vSwitch managed object if found, else None
        """
        for vss in host.configManager.networkSystem.networkInfo.vswitch:
            if vss.name == vswitch_name:
                return vss
        return None


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        switch=dict(type='str', required=True, aliases=['switch_name', 'vswitch']),
        nics=dict(type='list', default=[], aliases=['adapters', 'nic_name']),
        num_ports=dict(type='int', default=128, aliases=['number_of_ports', 'ports']),
        mtu=dict(type='int', default=1500),
        security=dict(
            type='dict',
            options=dict(
                promiscuous_mode=dict(type='bool'),
                forged_transmits=dict(type='bool'),
                mac_changes=dict(type='bool'),
            ),
            default=dict(
                promiscuous_mode=False,
                forged_transmits=True,
                mac_changes=True,
            ),
            aliases=['security_policy']
        ),
        traffic_shaping=dict(
            type='dict',
            options=dict(
                enabled=dict(type='bool'),
                average_bandwidth=dict(type='int'),
                peak_bandwidth=dict(type='int'),
                burst_size=dict(type='int'),
            ),
            default=dict(
                enabled=False,
                average_bandwidth=100000,
                peak_bandwidth=100000,
                burst_size=102400,
            ),
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
                        'failover_explicit',
                    ],
                ),
                network_failure_detection=dict(
                    type='str',
                    default='link_status_only',
                    choices=['link_status_only', 'beacon_probing']
                ),
                notify_switches=dict(type='bool', default=True),
                failback=dict(type='bool', default=True),
                active_adapters=dict(type='list'),
                standby_adapters=dict(type='list'),
            ),
            default=dict(
                load_balancing='loadbalance_srcid',
                notify_switches=True,
                failback=True,
            ),
            aliases=['teaming_policy']
        ),
        state=dict(
            type='str',
            default='present',
            choices=['absent', 'present']
        ),
        esxi_hostname=dict(type='str', aliases=['host']),
    ))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    host_virtual_switch = VMwareHostVirtualSwitch(module)
    host_virtual_switch.process_state()


if __name__ == '__main__':
    main()
