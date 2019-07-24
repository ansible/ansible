#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2017, Ansible Project
# Copyright: (c) 2017, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_portgroup
short_description: Create a VMware portgroup
description:
    - Create a VMware Port Group on a VMware Standard Switch (vSS) for given ESXi host(s) or hosts of given cluster.
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
- Russell Teague (@mtnbikenc)
- Abhijeet Kasurde (@Akasurde)
- Christian Kotte (@ckotte)
notes:
    - Tested on vSphere 5.5 and 6.5
    - Complete configuration only tested on vSphere 6.5
    - 'C(inbound_policy) and C(rolling_order) are deprecated and will be removed in 2.11'
    - Those two options are only used during portgroup creation. Updating isn't supported with those options.
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    switch:
        description:
            - vSwitch to modify.
        required: True
        aliases: [ 'switch_name', 'vswitch' ]
        type: str
    portgroup:
        description:
            - Portgroup name to add.
        required: True
        aliases: [ 'portgroup_name' ]
        type: str
    vlan_id:
        description:
            - VLAN ID to assign to portgroup.
            - Set to 0 (no VLAN tagging) by default.
        required: False
        default: 0
        aliases: [ 'vlan' ]
        type: int
    security:
        description:
            - Network policy specifies layer 2 security settings for a
              portgroup such as promiscuous mode, where guest adapter listens
              to all the packets, MAC address changes and forged transmits.
            - Dict which configures the different security values for portgroup.
            - 'Valid attributes are:'
            - '- C(promiscuous_mode) (bool): indicates whether promiscuous mode is allowed. (default: None)'
            - '- C(forged_transmits) (bool): indicates whether forged transmits are allowed. (default: None)'
            - '- C(mac_changes) (bool): indicates whether mac changes are allowed. (default: None)'
        required: False
        version_added: "2.2"
        aliases: [ 'security_policy', 'network_policy' ]
        type: dict
    teaming:
        description:
            - Dictionary which configures the different teaming values for portgroup.
            - 'Valid attributes are:'
            - '- C(load_balancing) (string): Network adapter teaming policy. C(load_balance_policy) is also alias to this option. (default: loadbalance_srcid)'
            - '   - choices: [ loadbalance_ip, loadbalance_srcmac, loadbalance_srcid, failover_explicit ]'
            - '- C(network_failure_detection) (string): Network failure detection. (default: link_status_only)'
            - '   - choices: [ link_status_only, beacon_probing ]'
            - '- C(notify_switches) (bool): Indicate whether or not to notify the physical switch if a link fails. (default: None)'
            - '- C(failback) (bool): Indicate whether or not to use a failback when restoring links. (default: None)'
            - '- C(active_adapters) (list): List of active adapters used for load balancing.'
            - '- C(standby_adapters) (list): List of standby adapters used for failover.'
            - '- All vmnics are used as active adapters if C(active_adapters) and C(standby_adapters) are not defined.'
            - '- C(inbound_policy) (bool): Indicate whether or not the teaming policy is applied to inbound frames as well. Deprecated. (default: False)'
            - '- C(rolling_order) (bool): Indicate whether or not to use a rolling policy when restoring links. Deprecated. (default: False)'
        required: False
        version_added: '2.6'
        aliases: [ 'teaming_policy' ]
        type: dict
    traffic_shaping:
        description:
            - Dictionary which configures traffic shaping for the switch.
            - 'Valid attributes are:'
            - '- C(enabled) (bool): Status of Traffic Shaping Policy. (default: None)'
            - '- C(average_bandwidth) (int): Average bandwidth (kbit/s). (default: None)'
            - '- C(peak_bandwidth) (int): Peak bandwidth (kbit/s). (default: None)'
            - '- C(burst_size) (int): Burst size (KB). (default: None)'
        required: False
        version_added: '2.9'
        type: dict
    cluster_name:
        description:
            - Name of cluster name for host membership.
            - Portgroup will be created on all hosts of the given cluster.
            - This option is required if C(hosts) is not specified.
        version_added: "2.5"
        aliases: [ 'cluster' ]
        type: str
    hosts:
        description:
            - List of name of host or hosts on which portgroup needs to be added.
            - This option is required if C(cluster_name) is not specified.
        aliases: [ esxi_hostname ]
        version_added: "2.5"
        type: list
    state:
        description:
            - Determines if the portgroup should be present or not.
        choices:
            - 'present'
            - 'absent'
        version_added: '2.5'
        default: present
        type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Add Management Network VM Portgroup
  vmware_portgroup:
    hostname: "{{ esxi_hostname }}"
    username: "{{ esxi_username }}"
    password: "{{ esxi_password }}"
    switch: "{{ vswitch_name }}"
    portgroup: "{{ portgroup_name }}"
    vlan_id: "{{ vlan_id }}"
  delegate_to: localhost

- name: Add Portgroup with Promiscuous Mode Enabled
  vmware_portgroup:
    hostname: "{{ esxi_hostname }}"
    username: "{{ esxi_username }}"
    password: "{{ esxi_password }}"
    switch: "{{ vswitch_name }}"
    portgroup: "{{ portgroup_name }}"
    security:
        promiscuous_mode: True
  delegate_to: localhost

- name: Add Management Network VM Portgroup to specific hosts
  vmware_portgroup:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    hosts: [esxi_hostname_one]
    switch: "{{ vswitch_name }}"
    portgroup: "{{ portgroup_name }}"
    vlan_id: "{{ vlan_id }}"
  delegate_to: localhost

- name: Add Management Network VM Portgroup to all hosts in a cluster
  vmware_portgroup:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    cluster_name: "{{ cluster_name }}"
    switch: "{{ vswitch_name }}"
    portgroup: "{{ portgroup_name }}"
    vlan_id: "{{ vlan_id }}"
  delegate_to: localhost

- name: Remove Management Network VM Portgroup to all hosts in a cluster
  vmware_portgroup:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    cluster_name: "{{ cluster_name }}"
    switch: "{{ vswitch_name }}"
    portgroup: "{{ portgroup_name }}"
    vlan_id: "{{ vlan_id }}"
    state: absent
  delegate_to: localhost

- name: Add Portgroup with all settings defined
  vmware_portgroup:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    esxi_hostname: "{{ inventory_hostname }}"
    switch: "{{ vswitch_name }}"
    portgroup: "{{ portgroup_name }}"
    vlan_id: 10
    security:
        promiscuous_mode: False
        mac_changes: False
        forged_transmits: False
    traffic_shaping:
        enabled: True
        average_bandwidth: 100000
        peak_bandwidth: 100000
        burst_size: 102400
    teaming:
        load_balancing: failover_explicit
        network_failure_detection: link_status_only
        notify_switches: true
        failback: true
        active_adapters:
            - vmnic0
        standby_adapters:
            - vmnic1
  delegate_to: localhost
  register: teaming_result
'''

RETURN = r'''
result:
    description: metadata about the portgroup
    returned: always
    type: dict
    sample: {
        "esxi01.example.com": {
            "changed": true,
            "failback": "No override",
            "failover_active": "No override",
            "failover_standby": "No override",
            "failure_detection": "No override",
            "load_balancing": "No override",
            "msg": "Port Group added",
            "notify_switches": "No override",
            "portgroup": "vMotion",
            "sec_forged_transmits": false,
            "sec_mac_changes": false,
            "sec_promiscuous_mode": false,
            "traffic_shaping": "No override",
            "vlan_id": 33,
            "vswitch": "vSwitch1"
        }
    }
'''


try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native


class VMwareHostPortGroup(PyVmomi):
    """Manage portgroup"""

    def __init__(self, module):
        super(VMwareHostPortGroup, self).__init__(module)
        self.switch_object = None
        self.portgroup_object = None
        hosts = self.params['hosts']
        cluster = self.params['cluster_name']
        self.portgroup = self.params['portgroup']
        self.switch = self.params['switch']
        self.vlan_id = self.params['vlan_id']
        if self.params['security']:
            self.sec_promiscuous_mode = self.params['security'].get('promiscuous_mode')
            self.sec_forged_transmits = self.params['security'].get('forged_transmits')
            self.sec_mac_changes = self.params['security'].get('mac_changes')
        else:
            self.sec_promiscuous_mode = None
            self.sec_forged_transmits = None
            self.sec_mac_changes = None
        if self.params['traffic_shaping']:
            self.ts_enabled = self.params['traffic_shaping'].get('enabled')
            for value in ['average_bandwidth', 'peak_bandwidth', 'burst_size']:
                if not self.params['traffic_shaping'].get(value):
                    self.module.fail_json(msg="traffic_shaping.%s is a required parameter if traffic_shaping is enabled." % value)
            self.ts_average_bandwidth = self.params['traffic_shaping'].get('average_bandwidth')
            self.ts_peak_bandwidth = self.params['traffic_shaping'].get('peak_bandwidth')
            self.ts_burst_size = self.params['traffic_shaping'].get('burst_size')
        else:
            self.ts_enabled = None
            self.ts_average_bandwidth = None
            self.ts_peak_bandwidth = None
            self.ts_burst_size = None
        if self.params['teaming']:
            self.teaming_load_balancing = self.params['teaming'].get('load_balancing')
            self.teaming_failure_detection = self.params['teaming'].get('network_failure_detection')
            self.teaming_notify_switches = self.params['teaming'].get('notify_switches')
            self.teaming_failback = self.params['teaming'].get('failback')
            self.teaming_failover_order_active = self.params['teaming'].get('active_adapters')
            self.teaming_failover_order_standby = self.params['teaming'].get('standby_adapters')
            if self.teaming_failover_order_active is None:
                self.teaming_failover_order_active = []
            if self.teaming_failover_order_standby is None:
                self.teaming_failover_order_standby = []
            # NOTE: the following options are deprecated and should be removed in 2.11
            self.teaming_inbound_policy = self.module.params['teaming']['inbound_policy']
            self.teaming_rolling_order = self.module.params['teaming']['rolling_order']
        else:
            self.teaming_load_balancing = None
            self.teaming_failure_detection = None
            self.teaming_notify_switches = None
            self.teaming_failback = None
            self.teaming_failover_order_active = None
            self.teaming_failover_order_standby = None
            # NOTE: the following options are deprecated and should be removed in 2.11
            self.teaming_inbound_policy = None
            self.teaming_rolling_order = None
        self.state = self.params['state']

        self.hosts = self.get_all_host_objs(cluster_name=cluster, esxi_host_name=hosts)
        if not self.hosts:
            self.module.fail_json(msg="Failed to find host system with given configuration.")

    def process_state(self):
        """Manage internal state of the portgroup"""
        results = dict(changed=False, result=dict())
        host_change_list = []
        for host in self.hosts:
            changed = False
            results['result'][host.name] = dict()
            switch_state = self.check_if_vswitch_exists(host_system=host)
            if switch_state == 'absent':
                self.module.fail_json(msg="The vSwitch '%s' doesn't exist on host '%s'" % (self.switch, host.name))
            portgroup_state = self.check_if_portgroup_exists(host_system=host)
            if self.state == 'present' and portgroup_state == 'present':
                changed, host_results = self.update_host_port_group(
                    host_system=host,
                    portgroup_object=self.portgroup_object
                )
            elif self.state == 'present' and portgroup_state == 'absent':
                changed, host_results = self.create_host_port_group(host_system=host)
            elif self.state == 'absent' and portgroup_state == 'present':
                changed, host_results = self.remove_host_port_group(host_system=host)
            else:
                host_results = dict()
                host_results['changed'] = False
                host_results['msg'] = "Port Group already deleted"
                host_results['portgroup'] = self.portgroup
            results['result'][host.name] = host_results

            host_change_list.append(changed)

        if any(host_change_list):
            results['changed'] = True
        self.module.exit_json(**results)

    def check_if_portgroup_exists(self, host_system):
        """
        Check if portgroup exists
        Returns: 'present' if portgroup exists or 'absent' if not
        """
        self.portgroup_object = self.find_portgroup_by_name(
            host_system=host_system,
            portgroup_name=self.portgroup,
            vswitch_name=self.switch
        )
        if self.portgroup_object is None:
            return 'absent'
        return 'present'

    def find_portgroup_by_name(self, host_system, portgroup_name, vswitch_name):
        """
        Find and return port group managed object
        Args:
            host_system: Name of Host System
            portgroup_name: Name of the Port Group
            vswitch_name: Name of the vSwitch

        Returns: Port Group managed object if found, else None
        """
        portgroups = self.get_all_port_groups_by_host(host_system=host_system)
        for portgroup in portgroups:
            if portgroup.spec.name == portgroup_name and portgroup.spec.vswitchName != vswitch_name:
                # portgroup names are unique; there can be only one portgroup with the same name per host
                self.module.fail_json(msg="The portgroup already exists on vSwitch '%s'" % portgroup.spec.vswitchName)
            if portgroup.spec.name == portgroup_name and portgroup.spec.vswitchName == vswitch_name:
                return portgroup
        return None

    def check_if_vswitch_exists(self, host_system):
        """
        Check if vSwitch exists
        Returns: 'present' if vSwitch exists or 'absent' if not
        """
        self.switch_object = self.find_vswitch_by_name(
            host_system=host_system,
            vswitch_name=self.switch
        )
        if self.switch_object is None:
            return 'absent'
        return 'present'

    @staticmethod
    def find_vswitch_by_name(host_system, vswitch_name):
        """
        Find and return vSwitch managed object
        Args:
            host: Host system managed object
            vswitch_name: Name of vSwitch to find

        Returns: vSwitch managed object if found, else None
        """
        for vss in host_system.configManager.networkSystem.networkInfo.vswitch:
            if vss.name == vswitch_name:
                return vss
        return None

    def remove_host_port_group(self, host_system):
        """
        Remove a Port Group from a given host
        Args:
            host_system: Name of Host System
        """
        host_results = dict(changed=False, msg="")

        if self.module.check_mode:
            host_results['msg'] = "Port Group would be removed"
        else:
            try:
                host_system.configManager.networkSystem.RemovePortGroup(pgName=self.portgroup)
                host_results['msg'] = "Port Group removed"
            except vim.fault.NotFound as not_found:
                self.module.fail_json(
                    msg="Failed to remove Portgroup as it was not found: %s" % to_native(not_found.msg)
                )
            except vim.fault.ResourceInUse as resource_in_use:
                self.module.fail_json(
                    msg="Failed to remove Portgroup as it is in use: %s" % to_native(resource_in_use.msg)
                )
            except vim.fault.HostConfigFault as host_config_fault:
                self.module.fail_json(
                    msg="Failed to remove Portgroup due to configuration failures: %s" % to_native(host_config_fault.msg)
                )
        host_results['changed'] = True
        host_results['portgroup'] = self.portgroup
        host_results['vswitch'] = self.switch

        return True, host_results

    def create_host_port_group(self, host_system):
        """Create Port Group on a given host
        Args:
            host_system: Name of Host System
        """
        host_results = dict(changed=False, msg="")

        if self.module.check_mode:
            host_results['msg'] = "Port Group would be added"
        else:
            port_group = vim.host.PortGroup.Config()
            port_group.spec = vim.host.PortGroup.Specification()
            port_group.spec.vswitchName = self.switch
            port_group.spec.name = self.portgroup
            port_group.spec.vlanId = self.vlan_id
            port_group.spec.policy = self.create_network_policy()

            try:
                host_system.configManager.networkSystem.AddPortGroup(portgrp=port_group.spec)
                host_results['changed'] = True
                host_results['msg'] = "Port Group added"
            except vim.fault.AlreadyExists as already_exists:
                self.module.fail_json(
                    msg="Failed to add Portgroup as it already exists: %s" % to_native(already_exists.msg)
                )
            except vim.fault.NotFound as not_found:
                self.module.fail_json(
                    msg="Failed to add Portgroup as vSwitch was not found: %s" % to_native(not_found.msg)
                )
            except vim.fault.HostConfigFault as host_config_fault:
                self.module.fail_json(
                    msg="Failed to add Portgroup due to host system configuration failure : %s" %
                    to_native(host_config_fault.msg)
                )
            except vmodl.fault.InvalidArgument as invalid_argument:
                self.module.fail_json(
                    msg="Failed to add Portgroup as VLAN id was not correct as per specifications: %s" %
                    to_native(invalid_argument.msg)
                )
        host_results['changed'] = True
        host_results['portgroup'] = self.portgroup
        host_results['vswitch'] = self.switch
        host_results['vlan_id'] = self.vlan_id
        if self.sec_promiscuous_mode is None:
            host_results['sec_promiscuous_mode'] = "No override"
        else:
            host_results['sec_promiscuous_mode'] = self.sec_promiscuous_mode
        if self.sec_mac_changes is None:
            host_results['sec_mac_changes'] = "No override"
        else:
            host_results['sec_mac_changes'] = self.sec_mac_changes
        if self.sec_forged_transmits is None:
            host_results['sec_forged_transmits'] = "No override"
        else:
            host_results['sec_forged_transmits'] = self.sec_forged_transmits
        host_results['traffic_shaping'] = "No override" if self.ts_enabled is None else self.ts_enabled
        host_results['load_balancing'] = "No override" if self.teaming_load_balancing is None \
            else self.teaming_load_balancing
        host_results['notify_switches'] = "No override" if self.teaming_notify_switches is None \
            else self.teaming_notify_switches
        host_results['failback'] = "No override" if self.teaming_failback is None else self.teaming_failback
        host_results['failover_active'] = "No override" if self.teaming_failover_order_active is None \
            else self.teaming_failover_order_active
        host_results['failover_standby'] = "No override" if self.teaming_failover_order_standby is None \
            else self.teaming_failover_order_standby
        host_results['failure_detection'] = "No override" if self.teaming_failure_detection is None \
            else self.teaming_failure_detection

        return True, host_results

    def update_host_port_group(self, host_system, portgroup_object):
        """Update a Port Group on a given host
        Args:
            host_system: Name of Host System
        """
        changed = changed_security = False
        changed_list = []
        host_results = dict(changed=False, msg="")
        spec = portgroup_object.spec

        # Check VLAN ID
        host_results['vlan_id'] = self.vlan_id
        if spec.vlanId != self.vlan_id:
            changed = True
            changed_list.append("VLAN ID")
            host_results['vlan_id_previous'] = spec.vlanId
            spec.vlanId = self.vlan_id

        # Check security settings
        if self.sec_promiscuous_mode is None:
            host_results['sec_promiscuous_mode'] = "No override"
        else:
            host_results['sec_promiscuous_mode'] = self.sec_promiscuous_mode
        if self.sec_mac_changes is None:
            host_results['sec_mac_changes'] = "No override"
        else:
            host_results['sec_mac_changes'] = self.sec_mac_changes
        if self.sec_forged_transmits is None:
            host_results['sec_forged_transmits'] = "No override"
        else:
            host_results['sec_forged_transmits'] = self.sec_forged_transmits
        if spec.policy.security:
            promiscuous_mode_previous = spec.policy.security.allowPromiscuous
            mac_changes_previous = spec.policy.security.macChanges
            forged_transmits_previous = spec.policy.security.forgedTransmits
            if promiscuous_mode_previous is not self.sec_promiscuous_mode:
                spec.policy.security.allowPromiscuous = self.sec_promiscuous_mode
                changed = changed_security = True
                changed_list.append("Promiscuous mode")
            if mac_changes_previous is not self.sec_mac_changes:
                spec.policy.security.macChanges = self.sec_mac_changes
                changed = changed_security = True
                changed_list.append("MAC address changes")
            if forged_transmits_previous is not self.sec_forged_transmits:
                spec.policy.security.forgedTransmits = self.sec_forged_transmits
                changed = changed_security = True
                changed_list.append("Forged transmits")
            if changed_security:
                if self.sec_promiscuous_mode is None:
                    host_results['sec_promiscuous_mode_previous'] = "No override"
                else:
                    host_results['sec_promiscuous_mode_previous'] = promiscuous_mode_previous
                if self.sec_mac_changes is None:
                    host_results['sec_mac_changes_previous'] = "No override"
                else:
                    host_results['sec_mac_changes'] = mac_changes_previous
                if self.sec_forged_transmits is None:
                    host_results['sec_forged_transmits_previous'] = "No override"
                else:
                    host_results['sec_forged_transmits_previous'] = forged_transmits_previous
        else:
            spec.policy.security = self.create_security_policy()
            changed = True
            changed_list.append("Security")
            host_results['sec_promiscuous_mode_previous'] = "No override"
            host_results['sec_mac_changes_previous'] = "No override"
            host_results['sec_forged_transmits_previous'] = "No override"

        # Check traffic shaping
        if self.ts_enabled is None:
            host_results['traffic_shaping'] = "No override"
        else:
            host_results['traffic_shaping'] = self.ts_enabled
            if self.ts_enabled:
                ts_average_bandwidth = self.ts_average_bandwidth * 1000
                ts_peak_bandwidth = self.ts_peak_bandwidth * 1000
                ts_burst_size = self.ts_burst_size * 1024
                host_results['traffic_shaping_avg_bandw'] = ts_average_bandwidth
                host_results['traffic_shaping_peak_bandw'] = ts_peak_bandwidth
                host_results['traffic_shaping_burst'] = ts_burst_size
        if spec.policy.shapingPolicy and spec.policy.shapingPolicy.enabled is not None:
            if spec.policy.shapingPolicy.enabled:
                if self.ts_enabled:
                    if spec.policy.shapingPolicy.averageBandwidth != ts_average_bandwidth:
                        changed = True
                        changed_list.append("Average bandwidth")
                        host_results['traffic_shaping_avg_bandw_previous'] = spec.policy.shapingPolicy.averageBandwidth
                        spec.policy.shapingPolicy.averageBandwidth = ts_average_bandwidth
                    if spec.policy.shapingPolicy.peakBandwidth != ts_peak_bandwidth:
                        changed = True
                        changed_list.append("Peak bandwidth")
                        host_results['traffic_shaping_peak_bandw_previous'] = spec.policy.shapingPolicy.peakBandwidth
                        spec.policy.shapingPolicy.peakBandwidth = ts_peak_bandwidth
                    if spec.policy.shapingPolicy.burstSize != ts_burst_size:
                        changed = True
                        changed_list.append("Burst size")
                        host_results['traffic_shaping_burst_previous'] = spec.policy.shapingPolicy.burstSize
                        spec.policy.shapingPolicy.burstSize = ts_burst_size
                elif self.ts_enabled is False:
                    changed = True
                    changed_list.append("Traffic shaping")
                    host_results['traffic_shaping_previous'] = True
                    spec.policy.shapingPolicy.enabled = False
                elif self.ts_enabled is None:
                    spec.policy.shapingPolicy = None
                    changed = True
                    changed_list.append("Traffic shaping")
                    host_results['traffic_shaping_previous'] = True
            else:
                if self.ts_enabled:
                    spec.policy.shapingPolicy = self.create_shaping_policy()
                    changed = True
                    changed_list.append("Traffic shaping")
                    host_results['traffic_shaping_previous'] = False
                elif self.ts_enabled is False:
                    changed = True
                    changed_list.append("Traffic shaping")
                    host_results['traffic_shaping_previous'] = True
                    spec.policy.shapingPolicy.enabled = False
                elif self.ts_enabled is None:
                    spec.policy.shapingPolicy = None
                    changed = True
                    changed_list.append("Traffic shaping")
                    host_results['traffic_shaping_previous'] = True
        else:
            if self.ts_enabled:
                spec.policy.shapingPolicy = self.create_shaping_policy()
                changed = True
                changed_list.append("Traffic shaping")
                host_results['traffic_shaping_previous'] = "No override"
            elif self.ts_enabled is False:
                changed = True
                changed_list.append("Traffic shaping")
                host_results['traffic_shaping_previous'] = "No override"
                spec.policy.shapingPolicy.enabled = False

        # Check teaming
        if spec.policy.nicTeaming:
            # Check teaming policy
            if self.teaming_load_balancing is None:
                host_results['load_balancing'] = "No override"
            else:
                host_results['load_balancing'] = self.teaming_load_balancing
            if spec.policy.nicTeaming.policy:
                if spec.policy.nicTeaming.policy != self.teaming_load_balancing:
                    changed = True
                    changed_list.append("Load balancing")
                    host_results['load_balancing_previous'] = spec.policy.nicTeaming.policy
                    spec.policy.nicTeaming.policy = self.teaming_load_balancing
            else:
                if self.teaming_load_balancing:
                    changed = True
                    changed_list.append("Load balancing")
                    host_results['load_balancing_previous'] = "No override"
                    spec.policy.nicTeaming.policy = self.teaming_load_balancing
            # Check teaming notify switches
            if spec.policy.nicTeaming.notifySwitches is None:
                host_results['notify_switches'] = "No override"
            else:
                host_results['notify_switches'] = self.teaming_notify_switches
            if spec.policy.nicTeaming.notifySwitches is not None:
                if self.teaming_notify_switches is not None:
                    if spec.policy.nicTeaming.notifySwitches is not self.teaming_notify_switches:
                        changed = True
                        changed_list.append("Notify switches")
                        host_results['notify_switches_previous'] = spec.policy.nicTeaming.notifySwitches
                        spec.policy.nicTeaming.notifySwitches = self.teaming_notify_switches
                else:
                    changed = True
                    changed_list.append("Notify switches")
                    host_results['notify_switches_previous'] = spec.policy.nicTeaming.notifySwitches
                    spec.policy.nicTeaming.notifySwitches = None
            else:
                if self.teaming_notify_switches is not None:
                    changed = True
                    changed_list.append("Notify switches")
                    host_results['notify_switches_previous'] = "No override"
                    spec.policy.nicTeaming.notifySwitches = self.teaming_notify_switches
            # Check failback
            if spec.policy.nicTeaming.rollingOrder is None:
                host_results['failback'] = "No override"
            else:
                host_results['failback'] = self.teaming_failback
            if spec.policy.nicTeaming.rollingOrder is not None:
                if self.teaming_failback is not None:
                    # this option is called 'failback' in the vSphere Client
                    # rollingOrder also uses the opposite value displayed in the client
                    if spec.policy.nicTeaming.rollingOrder is self.teaming_failback:
                        changed = True
                        changed_list.append("Failback")
                        host_results['failback_previous'] = not spec.policy.nicTeaming.rollingOrder
                        spec.policy.nicTeaming.rollingOrder = not self.teaming_failback
                else:
                    changed = True
                    changed_list.append("Failback")
                    host_results['failback_previous'] = spec.policy.nicTeaming.rollingOrder
                    spec.policy.nicTeaming.rollingOrder = None
            else:
                if self.teaming_failback is not None:
                    changed = True
                    changed_list.append("Failback")
                    host_results['failback_previous'] = "No override"
                    spec.policy.nicTeaming.rollingOrder = not self.teaming_failback
            # Check teaming failover order
            if self.teaming_failover_order_active is None and self.teaming_failover_order_standby is None:
                host_results['failover_active'] = "No override"
                host_results['failover_standby'] = "No override"
            else:
                host_results['failover_active'] = self.teaming_failover_order_active
                host_results['failover_standby'] = self.teaming_failover_order_standby
            if spec.policy.nicTeaming.nicOrder:
                if self.teaming_failover_order_active or self.teaming_failover_order_standby:
                    if spec.policy.nicTeaming.nicOrder.activeNic != self.teaming_failover_order_active:
                        changed = True
                        changed_list.append("Failover order active")
                        host_results['failover_active_previous'] = spec.policy.nicTeaming.nicOrder.activeNic
                        spec.policy.nicTeaming.nicOrder.activeNic = self.teaming_failover_order_active
                    if spec.policy.nicTeaming.nicOrder.standbyNic != self.teaming_failover_order_standby:
                        changed = True
                        changed_list.append("Failover order standby")
                        host_results['failover_standby_previous'] = spec.policy.nicTeaming.nicOrder.standbyNic
                        spec.policy.nicTeaming.nicOrder.standbyNic = self.teaming_failover_order_standby
                else:
                    spec.policy.nicTeaming.nicOrder = None
                    changed = True
                    changed_list.append("Failover order")
                    if hasattr(spec.policy.nicTeaming.nicOrder, 'activeNic'):
                        host_results['failover_active_previous'] = spec.policy.nicTeaming.nicOrder.activeNic
                    else:
                        host_results['failover_active_previous'] = []
                    if hasattr(spec.policy.nicTeaming.nicOrder, 'standbyNic'):
                        host_results['failover_standby_previous'] = spec.policy.nicTeaming.nicOrder.standbyNic
                    else:
                        host_results['failover_standby_previous'] = []
            else:
                if self.teaming_failover_order_active or self.teaming_failover_order_standby:
                    changed = True
                    changed_list.append("Failover order")
                    host_results['failover_active_previous'] = "No override"
                    host_results['failover_standby_previous'] = "No override"
                    spec.policy.nicTeaming.nicOrder = self.create_nic_order_policy()
            # Check teaming failure detection
            if self.teaming_failure_detection is None:
                host_results['failure_detection'] = "No override"
            else:
                host_results['failure_detection'] = self.teaming_failure_detection
            if spec.policy.nicTeaming.failureCriteria and spec.policy.nicTeaming.failureCriteria.checkBeacon is not None:
                if self.teaming_failure_detection == "link_status_only":
                    if spec.policy.nicTeaming.failureCriteria.checkBeacon is True:
                        changed = True
                        changed_list.append("Network failure detection")
                        host_results['failure_detection_previous'] = "beacon_probing"
                        spec.policy.nicTeaming.failureCriteria.checkBeacon = False
                elif self.teaming_failure_detection == "beacon_probing":
                    if spec.policy.nicTeaming.failureCriteria.checkBeacon is False:
                        changed = True
                        changed_list.append("Network failure detection")
                        host_results['failure_detection_previous'] = "link_status_only"
                        spec.policy.nicTeaming.failureCriteria.checkBeacon = True
                elif spec.policy.nicTeaming.failureCriteria.checkBeacon is not None:
                    changed = True
                    changed_list.append("Network failure detection")
                    host_results['failure_detection_previous'] = spec.policy.nicTeaming.failureCriteria.checkBeacon
                    spec.policy.nicTeaming.failureCriteria = None
            else:
                if self.teaming_failure_detection:
                    spec.policy.nicTeaming.failureCriteria = self.create_nic_failure_policy()
                    changed = True
                    changed_list.append("Network failure detection")
                    host_results['failure_detection_previous'] = "No override"
        else:
            spec.policy.nicTeaming = self.create_teaming_policy()
            if spec.policy.nicTeaming:
                changed = True
                changed_list.append("Teaming and failover")
                host_results['load_balancing_previous'] = "No override"
                host_results['notify_switches_previous'] = "No override"
                host_results['failback_previous'] = "No override"
                host_results['failover_active_previous'] = "No override"
                host_results['failover_standby_previous'] = "No override"
                host_results['failure_detection_previous'] = "No override"

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
                    host_system.configManager.networkSystem.UpdatePortGroup(
                        pgName=self.portgroup,
                        portgrp=spec
                    )
                except vim.fault.AlreadyExists as already_exists:
                    self.module.fail_json(
                        msg="Failed to update Portgroup as it would conflict with an existing port group: %s" %
                        to_native(already_exists.msg)
                    )
                except vim.fault.NotFound as not_found:
                    self.module.fail_json(
                        msg="Failed to update Portgroup as vSwitch was not found: %s" %
                        to_native(not_found.msg)
                    )
                except vim.fault.HostConfigFault as host_config_fault:
                    self.module.fail_json(
                        msg="Failed to update Portgroup due to host system configuration failure : %s" %
                        to_native(host_config_fault.msg)
                    )
                except vmodl.fault.InvalidArgument as invalid_argument:
                    self.module.fail_json(
                        msg="Failed to update Port Group '%s', this can be due to either of following :"
                        " 1. VLAN id was not correct as per specifications, 2. Network policy is invalid : %s" %
                        (self.portgroup, to_native(invalid_argument.msg))
                    )
        else:
            message = "Port Group already configured properly"
        host_results['changed'] = changed
        host_results['msg'] = message
        host_results['portgroup'] = self.portgroup
        host_results['vswitch'] = self.switch

        return changed, host_results

    def create_network_policy(self):
        """
        Create a Network Policy
        Returns: Network Policy object
        """
        security_policy = None
        shaping_policy = None
        teaming_policy = None

        # Only configure security policy if an option is defined
        if not all(option is None for option in [self.sec_promiscuous_mode,
                                                 self.sec_mac_changes,
                                                 self.sec_forged_transmits]):
            security_policy = self.create_security_policy()
        if self.ts_enabled:
            shaping_policy = self.create_shaping_policy()
        teaming_policy = self.create_teaming_policy()

        network_policy = vim.host.NetworkPolicy(
            security=security_policy,
            nicTeaming=teaming_policy,
            shapingPolicy=shaping_policy
        )

        return network_policy

    def create_security_policy(self):
        """
        Create a Security Policy
        Returns: Security Policy object
        """
        security_policy = vim.host.NetworkPolicy.SecurityPolicy()
        security_policy.allowPromiscuous = self.sec_promiscuous_mode
        security_policy.macChanges = self.sec_mac_changes
        security_policy.forgedTransmits = self.sec_forged_transmits
        return security_policy

    def create_shaping_policy(self):
        """
        Create a Traffic Shaping Policy
        Returns: Traffic Shaping Policy object
        """
        shaping_policy = vim.host.NetworkPolicy.TrafficShapingPolicy()
        shaping_policy.enabled = self.ts_enabled
        shaping_policy.averageBandwidth = self.ts_average_bandwidth * 1000
        shaping_policy.peakBandwidth = self.ts_peak_bandwidth * 1000
        shaping_policy.burstSize = self.ts_burst_size * 1024
        return shaping_policy

    def create_teaming_policy(self):
        """
        Create a NIC Teaming Policy
        Returns: NIC Teaming Policy object
        """
        # Only configure teaming policy if an option is defined
        if not all(option is None for option in [self.teaming_load_balancing,
                                                 self.teaming_failure_detection,
                                                 self.teaming_notify_switches,
                                                 self.teaming_failback,
                                                 self.teaming_failover_order_active,
                                                 self.teaming_failover_order_standby]):
            teaming_policy = vim.host.NetworkPolicy.NicTeamingPolicy()
            teaming_policy.policy = self.teaming_load_balancing
            # NOTE: 'teaming_inbound_policy' is deprecated and the following if statement should be removed in 2.11
            if self.teaming_inbound_policy:
                teaming_policy.reversePolicy = self.teaming_inbound_policy
            else:
                # Deprecated since VI API 5.1. The system default (true) will be used
                teaming_policy.reversePolicy = True
            teaming_policy.notifySwitches = self.teaming_notify_switches
            # NOTE: 'teaming_rolling_order' is deprecated and the following if statement should be removed in 2.11
            if self.teaming_rolling_order:
                teaming_policy.rollingOrder = self.teaming_rolling_order
            else:
                # this option is called 'failback' in the vSphere Client
                # rollingOrder also uses the opposite value displayed in the client
                if self.teaming_failback is None:
                    teaming_policy.rollingOrder = None
                else:
                    teaming_policy.rollingOrder = not self.teaming_failback
            if self.teaming_failover_order_active is None and self.teaming_failover_order_standby is None:
                teaming_policy.nicOrder = None
            else:
                teaming_policy.nicOrder = self.create_nic_order_policy()
            if self.teaming_failure_detection is None:
                teaming_policy.failureCriteria = None
            else:
                teaming_policy.failureCriteria = self.create_nic_failure_policy()
            return teaming_policy
        return None

    def create_nic_order_policy(self):
        """
        Create a NIC order Policy
        Returns: NIC order Policy object
        """
        for active_nic in self.teaming_failover_order_active:
            if active_nic not in self.switch_object.spec.bridge.nicDevice:
                self.module.fail_json(
                    msg="NIC '%s' (active) is not configured on vSwitch '%s'" % (active_nic, self.switch)
                )
        for standby_nic in self.teaming_failover_order_standby:
            if standby_nic not in self.switch_object.spec.bridge.nicDevice:
                self.module.fail_json(
                    msg="NIC '%s' (standby) is not configured on vSwitch '%s'" % (standby_nic, self.switch)
                )
        nic_order = vim.host.NetworkPolicy.NicOrderPolicy()
        nic_order.activeNic = self.teaming_failover_order_active
        nic_order.standbyNic = self.teaming_failover_order_standby
        return nic_order

    def create_nic_failure_policy(self):
        """
        Create a NIC Failure Criteria Policy
        Returns: NIC Failure Criteria Policy object
        """
        failure_criteria = vim.host.NetworkPolicy.NicFailureCriteria()
        if self.teaming_failure_detection == "link_status_only":
            failure_criteria.checkBeacon = False
        elif self.teaming_failure_detection == "beacon_probing":
            failure_criteria.checkBeacon = True
        elif self.teaming_failure_detection is None:
            failure_criteria = None
        # The following properties are deprecated since VI API 5.1. Default values are used
        failure_criteria.fullDuplex = False
        failure_criteria.percentage = 0
        failure_criteria.checkErrorPercent = False
        failure_criteria.checkDuplex = False
        failure_criteria.speed = 10
        failure_criteria.checkSpeed = 'minimum'
        return failure_criteria


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        portgroup=dict(type='str', required=True, aliases=['portgroup_name']),
        switch=dict(type='str', required=True, aliases=['switch_name', 'vswitch']),
        vlan_id=dict(type='int', required=False, default=0, aliases=['vlan']),
        hosts=dict(type='list', aliases=['esxi_hostname']),
        cluster_name=dict(type='str', aliases=['cluster']),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        security=dict(
            type='dict',
            options=dict(
                promiscuous_mode=dict(type='bool'),
                forged_transmits=dict(type='bool'),
                mac_changes=dict(type='bool'),
            ),
            aliases=['security_policy', 'network_policy']
        ),
        traffic_shaping=dict(
            type='dict',
            options=dict(
                enabled=dict(type='bool'),
                average_bandwidth=dict(type='int'),
                peak_bandwidth=dict(type='int'),
                burst_size=dict(type='int'),
            ),
        ),
        teaming=dict(
            type='dict',
            options=dict(
                load_balancing=dict(
                    type='str',
                    choices=[
                        None,
                        'loadbalance_ip',
                        'loadbalance_srcmac',
                        'loadbalance_srcid',
                        'failover_explicit',
                    ],
                    aliases=['load_balance_policy'],
                ),
                network_failure_detection=dict(
                    type='str',
                    choices=['link_status_only', 'beacon_probing']
                ),
                notify_switches=dict(type='bool'),
                failback=dict(type='bool'),
                active_adapters=dict(type='list'),
                standby_adapters=dict(type='list'),
                # NOTE: Deprecated from 2.11 onwards
                inbound_policy=dict(type='bool'),
                rolling_order=dict(type='bool'),
            ),
            aliases=['teaming_policy']
        ),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'hosts'],
        ],
        supports_check_mode=True
    )

    try:
        host_portgroup = VMwareHostPortGroup(module)
        host_portgroup.process_state()
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=to_native(runtime_fault.msg))
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=to_native(method_fault.msg))
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
