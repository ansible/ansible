#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2017, Ansible Project
# Copyright: (c) 2017, Abhijeet Kasurde <akasurde@redhat.com>
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
- Abhijeet Kasurde (@akasurde) <akasurde@redhat.com>
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
    cluster_name:
        description:
            - Name of cluster name for host membership.
            - Portgroup will be created on all hosts of the given cluster.
            - This option is required if hosts is not specified.
        version_added: "2.5"
    hosts:
        description:
            - List of name of host or hosts on which portgroup needs to be added.
            - This option is required if cluster_name is not specified.
        version_added: "2.5"
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

'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)

        self.hosts = self.params['hosts']
        self.cluster = self.params['cluster_name']
        self.portgroup_name = self.params['portgroup_name']
        self.switch_name = self.params['switch_name']
        self.vlan_id = self.params['vlan_id']
        self.promiscuous_mode = self.params['network_policy'].get('promiscuous_mode')
        self.forged_transmits = self.params['network_policy'].get('forged_transmits')
        self.mac_changes = self.params['network_policy'].get('mac_changes')
        self.network_policy = self.create_network_policy()
        self.changed = False

    def add_hosts_port_group(self, hosts):
        for host in hosts:
            self.changed = self.create_port_group(host, self.portgroup_name, self.vlan_id,
                                                  self.switch_name, self.network_policy)

    def create_port_group(self, host_system, portgroup_name, vlan_id, vswitch_name, network_policy):
        config = vim.host.NetworkConfig()
        config.portgroup = [vim.host.PortGroup.Config()]
        config.portgroup[0].changeOperation = "add"
        config.portgroup[0].spec = vim.host.PortGroup.Specification()
        config.portgroup[0].spec.name = portgroup_name
        config.portgroup[0].spec.vlanId = vlan_id
        config.portgroup[0].spec.vswitchName = vswitch_name
        config.portgroup[0].spec.policy = network_policy

        host_system.configManager.networkSystem.UpdateNetworkConfig(config, "modify")
        return True

    def create_network_policy(self):
        security_policy = vim.host.NetworkPolicy.SecurityPolicy()
        if self.promiscuous_mode:
            security_policy.allowPromiscuous = self.promiscuous_mode
        if self.forged_transmits:
            security_policy.forgedTransmits = self.forged_transmits
        if self.mac_changes:
            security_policy.macChanges = self.mac_changes
        network_policy = vim.host.NetworkPolicy(security=security_policy)
        return network_policy

    def add_portgroup(self):
        if self.cluster and self.find_cluster_by_name(cluster_name=self.cluster):
            hosts = self.get_all_hosts_by_cluster(cluster_name=self.cluster)
            self.add_hosts_port_group(hosts=hosts)
        elif self.hosts:
            for host in self.hosts:
                host_system = self.find_hostsystem_by_name(host_name=host)
                if host_system:
                    self.add_hosts_port_group([host_system])


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        portgroup_name=dict(required=True, type='str'),
        switch_name=dict(required=True, type='str'),
        vlan_id=dict(required=True, type='int'),
        hosts=dict(type='list'),
        cluster_name=dict(type='str'),
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
                            )
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
        pyv.add_portgroup()
        changed = pyv.changed

        module.exit_json(changed=changed)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
