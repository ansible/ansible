#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2017-18, Ansible Project
# Copyright: (c) 2017-18, Abhijeet Kasurde <akasurde@redhat.com>
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
    - Create a VMware portgroup on given host/s or hosts of given cluster
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
- Russell Teague (@mtnbikenc)
- Abhijeet Kasurde (@Akasurde) <akasurde@redhat.com>
notes:
    - Tested on vSphere 5.5, 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    switch_name:
        description:
            - vSwitch to modify.
        required: True
    portgroup_name:
        description:
            - Portgroup name to add.
        required: True
    vlan_id:
        description:
            - VLAN ID to assign to portgroup.
        required: True
    network_policy:
        description:
            - Network policy specifies layer 2 security settings for a
              portgroup such as promiscuous mode, where guest adapter listens
              to all the packets, MAC address changes and forged transmits.
            - Dict which configures the different security values for portgroup.
            - 'Valid attributes are:'
            - '- C(promiscuous_mode) (bool): indicates whether promiscuous mode is allowed. (default: false)'
            - '- C(forged_transmits) (bool): indicates whether forged transmits are allowed. (default: false)'
            - '- C(mac_changes) (bool): indicates whether mac changes are allowed. (default: false)'
        required: False
        version_added: "2.2"
        default: {
            mac_changes: false,
            promiscuous_mode: false,
            forged_transmits: false,
        }
    teaming_policy:
        description:
            - Dictionary which configures the different teaming values for portgroup.
            - 'Valid attributes are:'
            - '- C(load_balance_policy) (string): Network adapter teaming policy. (default: loadbalance_srcid)'
            - '   - choices: [ loadbalance_ip, loadbalance_srcmac, loadbalance_srcid, failover_explicit ]'
            - '- C(inbound_policy) (bool): Indicate whether or not the teaming policy is applied to inbound frames as well. (default: False)'
            - '- C(notify_switches) (bool): Indicate whether or not to notify the physical switch if a link fails. (default: True)'
            - '- C(rolling_order) (bool): Indicate whether or not to use a rolling policy when restoring links. (default: False)'
        required: False
        version_added: '2.6'
        default: {
            'notify_switches': True,
            'load_balance_policy': 'loadbalance_srcid',
            'inbound_policy': False,
            'rolling_order': False
        }
    cluster_name:
        description:
            - Name of cluster name for host membership.
            - Portgroup will be created on all hosts of the given cluster.
            - This option is required if C(hosts) is not specified.
        version_added: "2.5"
    hosts:
        description:
            - List of name of host or hosts on which portgroup needs to be added.
            - This option is required if C(cluster_name) is not specified.
        aliases: [ esxi_hostname ]
        version_added: "2.5"
    state:
        description:
            - Determines if the portgroup should be present or not.
        choices:
            - 'present'
            - 'absent'
        version_added: '2.5'
        default: present
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Add Management Network VM Portgroup
  vmware_portgroup:
    hostname: esxi_hostname
    username: esxi_username
    password: esxi_password
    switch_name: vswitch_name
    portgroup_name: portgroup_name
    vlan_id: vlan_id

- name: Add Portgroup with Promiscuous Mode Enabled
  vmware_portgroup:
    hostname: esxi_hostname
    username: esxi_username
    password: esxi_password
    switch_name: vswitch_name
    portgroup_name: portgroup_name
    network_policy:
        promiscuous_mode: True

- name: Add Management Network VM Portgroup to specific hosts
  vmware_portgroup:
    hostname: vCenter_hostname
    username: esxi_username
    password: esxi_password
    hosts: [esxi_hostname_one]
    switch_name: vswitch_name
    portgroup_name: portgroup_name
    vlan_id: vlan_id

- name: Add Management Network VM Portgroup to all hosts in a cluster
  vmware_portgroup:
    hostname: vCenter_hostname
    username: esxi_username
    password: esxi_password
    cluster_name: rh_engineering
    switch_name: vswitch_name
    portgroup_name: portgroup_name
    vlan_id: vlan_id

- name: Remove Management Network VM Portgroup to all hosts in a cluster
  vmware_portgroup:
    hostname: vCenter_hostname
    username: esxi_username
    password: esxi_password
    cluster_name: rh_engineering
    switch_name: vswitch_name
    portgroup_name: portgroup_name
    vlan_id: vlan_id
    state: absent

- name: Add Portgroup with teaming policy
  vmware_portgroup:
    hostname: esxi_hostname
    username: esxi_username
    password: esxi_password
    switch_name: vswitch_name
    portgroup_name: portgroup_name
    teaming_policy:
      load_balance_policy: 'failover_explicit'
      inbound_policy: True
  register: teaming_result
'''

RETURN = r'''
result:
    description: metadata about the portgroup
    returned: always
    type: dict
    sample: {
        "esxi01.example.com": {
            "portgroup_name": "pg0010",
            "switch_name": "vswitch_0001",
            "vlan_id": 1
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


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)

        hosts = self.params['hosts']
        cluster = self.params['cluster_name']
        self.portgroup_name = self.params['portgroup_name']
        self.switch_name = self.params['switch_name']
        self.vlan_id = self.params['vlan_id']
        self.promiscuous_mode = self.params['network_policy'].get('promiscuous_mode')
        self.forged_transmits = self.params['network_policy'].get('forged_transmits')
        self.mac_changes = self.params['network_policy'].get('mac_changes')
        self.network_policy = self.create_network_policy()
        self.state = self.params['state']
        self.host_obj_list = self.get_all_host_objs(cluster_name=cluster, esxi_host_name=hosts)

    def process_state(self):
        """
        Function to manage state
        """
        if self.state == 'present':
            self.add_hosts_port_group()
        elif self.state == 'absent':
            self.remove_hosts_port_group()

    # Get
    def get_port_group_by_name(self, host_system, portgroup_name, vswitch_name):
        """
        Function to get specific port group by given name
        Args:
            host_system: Name of Host System
            portgroup_name: Name of Port Group
            vswitch_name: Name of vSwitch

        Returns: List of port groups by given specifications

        """
        pgs_list = self.get_all_port_groups_by_host(host_system=host_system)
        desired_pgs = []
        for pg in pgs_list:
            if pg.spec.name == portgroup_name and pg.spec.vswitchName == vswitch_name:
                desired_pgs.append(pg)
        return desired_pgs

    @staticmethod
    def check_network_policy_diff(current_policy, desired_policy):
        """
        Function to find difference between existing network policy and user given network policy
        Args:
            current_policy: Current network policy
            desired_policy: User defined network policy

        Returns: True if difference found, False if not.

        """
        ret = False
        if (current_policy.security.allowPromiscuous != desired_policy.security.allowPromiscuous) or \
                (current_policy.security.forgedTransmits != desired_policy.security.forgedTransmits) or \
                (current_policy.security.macChanges != desired_policy.security.macChanges) or \
                (current_policy.nicTeaming.policy != desired_policy.nicTeaming.policy) or \
                (current_policy.nicTeaming.reversePolicy != desired_policy.nicTeaming.reversePolicy) or \
                (current_policy.nicTeaming.notifySwitches != desired_policy.nicTeaming.notifySwitches) or \
                (current_policy.nicTeaming.rollingOrder != desired_policy.nicTeaming.rollingOrder):
            ret = True
        return ret

    # Add
    def add_hosts_port_group(self):
        """
        Function to add port group to given hosts
        """
        results = dict(changed=False, result=dict())
        host_change_list = []
        for host in self.host_obj_list:
            change = False
            results['result'][host.name] = dict(portgroup_name=self.portgroup_name,
                                                vlan_id=self.vlan_id,
                                                switch_name=self.switch_name)
            change = self.create_host_port_group(host, self.portgroup_name, self.vlan_id, self.switch_name, self.network_policy)
            host_change_list.append(change)
        if any(host_change_list):
            results['changed'] = True
        self.module.exit_json(**results)

    def create_host_port_group(self, host_system, portgroup_name, vlan_id, vswitch_name, network_policy):
        """
        Function to create/update portgroup on given host using portgroup specifications
        Args:
            host_system: Name of Host System
            portgroup_name: Name of Portgroup
            vlan_id: The VLAN ID for ports using this port group.
            vswitch_name: Name of vSwitch Name
            network_policy: Network policy object
        """
        desired_pgs = self.get_port_group_by_name(host_system=host_system,
                                                  portgroup_name=portgroup_name,
                                                  vswitch_name=vswitch_name)

        port_group = vim.host.PortGroup.Config()
        port_group.spec = vim.host.PortGroup.Specification()
        port_changed = False

        if not desired_pgs:
            # Add new portgroup
            port_group.spec.name = portgroup_name
            port_group.spec.vlanId = vlan_id
            port_group.spec.vswitchName = vswitch_name
            port_group.spec.policy = network_policy

            try:
                host_system.configManager.networkSystem.AddPortGroup(portgrp=port_group.spec)
                port_changed = True
            except vim.fault.AlreadyExists as e:
                # To match with other vmware_* modules if portgroup
                # exists, we proceed, as user may want idempotency
                pass
            except vim.fault.NotFound as not_found:
                self.module.fail_json(msg="Failed to add Portgroup as vSwitch"
                                          " was not found: %s" % to_native(not_found.msg))
            except vim.fault.HostConfigFault as host_config_fault:
                self.module.fail_json(msg="Failed to add Portgroup due to host system"
                                          " configuration failure : %s" % to_native(host_config_fault.msg))
            except vmodl.fault.InvalidArgument as invalid_argument:
                self.module.fail_json(msg="Failed to add Portgroup as VLAN id was not"
                                          " correct as per specifications: %s" % to_native(invalid_argument.msg))
            except Exception as generic_exception:
                self.module.fail_json(msg="Failed to add Portgroup due to generic"
                                          " exception : %s" % to_native(generic_exception))
        else:
            # Change portgroup
            port_group.spec.name = portgroup_name
            port_group.spec.vlanId = vlan_id
            port_group.spec.policy = network_policy
            port_group.spec.vswitchName = desired_pgs[0].spec.vswitchName
            if self.check_network_policy_diff(desired_pgs[0].spec.policy, network_policy) or \
                    desired_pgs[0].spec.vlanId != vlan_id:
                port_changed = True
                try:
                    host_system.configManager.networkSystem.UpdatePortGroup(pgName=self.portgroup_name,
                                                                            portgrp=port_group.spec)
                except vim.fault.AlreadyExists as e:
                    # To match with other vmware_* modules if portgroup
                    # exists, we proceed, as user may want idempotency
                    pass
                except vim.fault.NotFound as not_found:
                    self.module.fail_json(msg="Failed to update Portgroup as"
                                              " vSwitch was not found: %s" % to_native(not_found.msg))
                except vim.fault.HostConfigFault as host_config_fault:
                    self.module.fail_json(msg="Failed to update Portgroup due to host"
                                              " system configuration failure : %s" % to_native(host_config_fault.msg))
                except vmodl.fault.InvalidArgument as invalid_argument:
                    self.module.fail_json(msg="Failed to update Portgroup as VLAN id was not"
                                              " correct as per specifications: %s" % to_native(invalid_argument.msg))
                except Exception as generic_exception:
                    self.module.fail_json(msg="Failed to update Portgroup due to generic"
                                              " exception : %s" % to_native(generic_exception))
        return port_changed

    def create_network_policy(self):
        """
        Function to create Network policy
        Returns: Network policy object
        """
        security_policy = vim.host.NetworkPolicy.SecurityPolicy()
        if self.promiscuous_mode:
            security_policy.allowPromiscuous = self.promiscuous_mode
        if self.forged_transmits:
            security_policy.forgedTransmits = self.forged_transmits
        if self.mac_changes:
            security_policy.macChanges = self.mac_changes

        # Teaming Policy
        teaming_policy = vim.host.NetworkPolicy.NicTeamingPolicy()
        teaming_policy.policy = self.module.params['teaming_policy']['load_balance_policy']
        teaming_policy.reversePolicy = self.module.params['teaming_policy']['inbound_policy']
        teaming_policy.notifySwitches = self.module.params['teaming_policy']['notify_switches']
        teaming_policy.rollingOrder = self.module.params['teaming_policy']['rolling_order']

        network_policy = vim.host.NetworkPolicy(nicTeaming=teaming_policy,
                                                security=security_policy)

        return network_policy

    def remove_hosts_port_group(self):
        """
        Function to remove port group from given host
        """
        results = dict(changed=False, result=dict())
        host_change_list = []
        for host in self.host_obj_list:
            change = False
            results['result'][host.name] = dict(portgroup_name=self.portgroup_name,
                                                vlan_id=self.vlan_id,
                                                switch_name=self.switch_name)
            change = self.remove_host_port_group(host_system=host,
                                                 portgroup_name=self.portgroup_name,
                                                 vswitch_name=self.switch_name)
            host_change_list.append(change)
        if any(host_change_list):
            results['changed'] = True
        self.module.exit_json(**results)

    def remove_host_port_group(self, host_system, portgroup_name, vswitch_name):
        """
        Function to remove port group depending upon host system, port group name and vswitch name
        Args:
            host_system: Name of Host System
            portgroup_name: Name of Portgroup
            vswitch_name: Name of vSwitch

        """
        changed = False
        desired_pgs = self.get_port_group_by_name(host_system=host_system,
                                                  portgroup_name=portgroup_name,
                                                  vswitch_name=vswitch_name)
        if desired_pgs:
            try:
                host_system.configManager.networkSystem.RemovePortGroup(pgName=self.portgroup_name)
                changed = True
            except vim.fault.NotFound as not_found:
                self.module.fail_json(msg="Failed to remove Portgroup as it was"
                                          " not found: %s" % to_native(not_found.msg))
            except vim.fault.ResourceInUse as resource_in_use:
                self.module.fail_json(msg="Failed to remove Portgroup as it is"
                                          " in use: %s" % to_native(resource_in_use.msg))
            except vim.fault.HostConfigFault as host_config_fault:
                self.module.fail_json(msg="Failed to remove Portgroup due to configuration"
                                          " failures: %s" % to_native(host_config_fault.msg))
            except Exception as generic_exception:
                self.module.fail_json(msg="Failed to remove Portgroup due to generic"
                                          " exception : %s" % to_native(generic_exception))
        return changed


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        portgroup_name=dict(required=True, type='str'),
        switch_name=dict(required=True, type='str'),
        vlan_id=dict(required=True, type='int'),
        hosts=dict(type='list', aliases=['esxi_hostname']),
        cluster_name=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        network_policy=dict(type='dict',
                            options=dict(
                                promiscuous_mode=dict(type='bool'),
                                forged_transmits=dict(type='bool'),
                                mac_changes=dict(type='bool'),
                            ),
                            default=dict(
                                promiscuous_mode=False,
                                forged_transmits=False,
                                mac_changes=False,
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
    )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           required_one_of=[
                               ['cluster_name', 'hosts'],
                           ]
                           )

    try:
        pyv = PyVmomiHelper(module)
        pyv.process_state()
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=to_native(runtime_fault.msg))
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=to_native(method_fault.msg))
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
