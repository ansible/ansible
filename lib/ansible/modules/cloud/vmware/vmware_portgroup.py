#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Joseph Callen <jcallen () csc.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_portgroup
short_description: Create a VMware portgroup
description:
    - Create a VMware portgroup
version_added: 2.0
author: "Joseph Callen (@jcpowermac), Russell Teague (@mtnbikenc)"
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    switch_name:
        description:
            - vSwitch to modify
        required: True
    portgroup_name:
        description:
            - Portgroup name to add
        required: True
    vlan_id:
        description:
            - VLAN ID to assign to portgroup
        required: True
    network_policy:
        description:
            - Network policy specifies layer 2 security settings for a
              portgroup such as promiscuous mode, where guest adapter listens
              to all the packets, MAC address changes and forged transmits.
              Settings are promiscuous_mode, forged_transmits, mac_changes
        required: False
        version_added: "2.2"
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
# Example from Ansible playbook

    - name: Add Management Network VM Portgroup
      local_action:
        module: vmware_portgroup
        hostname: esxi_hostname
        username: esxi_username
        password: esxi_password
        switch_name: vswitch_name
        portgroup_name: portgroup_name
        vlan_id: vlan_id

    - name: Add Portgroup with Promiscuous Mode Enabled
      local_action:
        module: vmware_portgroup
        hostname: esxi_hostname
        username: esxi_username
        password: esxi_password
        switch_name: vswitch_name
        portgroup_name: portgroup_name
        network_policy:
            promiscuous_mode: True
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (HAS_PYVMOMI,
                                         connect_to_api,
                                         find_host_portgroup_by_name,
                                         get_all_objs,
                                         vmware_argument_spec,
                                         )


def create_network_policy(promiscuous_mode, forged_transmits, mac_changes):

    security_policy = vim.host.NetworkPolicy.SecurityPolicy()
    if promiscuous_mode:
        security_policy.allowPromiscuous = promiscuous_mode
    if forged_transmits:
        security_policy.forgedTransmits = forged_transmits
    if mac_changes:
        security_policy.macChanges = mac_changes
    network_policy = vim.host.NetworkPolicy(security=security_policy)
    return network_policy


def create_port_group(host_system, portgroup_name, vlan_id, vswitch_name, network_policy):

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


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(portgroup_name=dict(required=True, type='str'),
                         switch_name=dict(required=True, type='str'),
                         vlan_id=dict(required=True, type='int'),
                         network_policy=dict(required=False, type='dict', default={})))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    portgroup_name = module.params['portgroup_name']
    switch_name = module.params['switch_name']
    vlan_id = module.params['vlan_id']
    promiscuous_mode = module.params['network_policy'].get('promiscuous_mode', None)
    forged_transmits = module.params['network_policy'].get('forged_transmits', None)
    mac_changes = module.params['network_policy'].get('mac_changes', None)

    try:
        content = connect_to_api(module)
        host = get_all_objs(content, [vim.HostSystem])
        if not host:
            raise SystemExit("Unable to locate Physical Host.")
        host_system = host.keys()[0]

        if find_host_portgroup_by_name(host_system, portgroup_name):
            module.exit_json(changed=False)

        network_policy = create_network_policy(promiscuous_mode, forged_transmits, mac_changes)
        changed = create_port_group(host_system, portgroup_name, vlan_id, switch_name, network_policy)

        module.exit_json(changed=changed)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
