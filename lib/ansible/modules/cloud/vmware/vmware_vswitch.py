#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Joseph Callen <jcallen () csc.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_vswitch
short_description: Add or remove a VMware Standard Switch to an ESXi host
description:
- Add or remove a VMware Standard Switch to an ESXi host.
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
- Russell Teague (@mtnbikenc)
notes:
- Tested on vSphere 5.5
requirements:
- python >= 2.6
- PyVmomi
options:
  switch:
    description:
    - vSwitch name to add.
    - Alias C(switch) is added in version 2.4.
    required: yes
    aliases: [ switch_name ]
  nics:
    description:
    - A list of vmnic names or vmnic name to attach to vSwitch.
    - Alias C(nics) is added in version 2.4.
    aliases: [ nic_name ]
  number_of_ports:
    description:
    - Number of port to configure on vSwitch.
    default: 128
  mtu:
    description:
    - MTU to configure on vSwitch.
  state:
    description:
    - Add or remove the switch.
    default: present
    choices: [ absent, present ]
extends_documentation_fragment:
- vmware.documentation
'''

EXAMPLES = '''
- name: Add a VMware vSwitch
  action:
    module: vmware_vswitch
    hostname: esxi_hostname
    username: esxi_username
    password: esxi_password
    switch: vswitch_name
    nics: vmnic_name
    mtu: 9000
  delegate_to: localhost

- name: Add a VMWare vSwitch without any physical NIC attached
  vmware_vswitch:
    hostname: 192.168.10.1
    username: admin
    password: password123
    switch: vswitch_0001
    mtu: 9000
  delegate_to: localhost

- name: Add a VMWare vSwitch with multiple NICs
  vmware_vswitch:
    hostname: esxi_hostname
    username: esxi_username
    password: esxi_password
    switch: vmware_vswitch_0004
    nics:
    - vmnic1
    - vmnic2
    mtu: 9000
  delegate_to: localhost
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, get_all_objs, connect_to_api


def find_vswitch_by_name(host, vswitch_name):
    for vss in host.configManager.networkSystem.networkInfo.vswitch:
        if vss.name == vswitch_name:
            return vss
    return None


class VMwareHostVirtualSwitch(object):

    def __init__(self, module):
        self.host_system = None
        self.content = None
        self.vss = None
        self.module = module
        self.switch = module.params['switch']
        self.number_of_ports = module.params['number_of_ports']
        self.nics = module.params['nics']
        self.mtu = module.params['mtu']
        self.state = module.params['state']
        self.content = connect_to_api(self.module)

    def process_state(self):
        try:
            vswitch_states = {
                'absent': {
                    'present': self.state_destroy_vswitch,
                    'absent': self.state_exit_unchanged,
                },
                'present': {
                    'update': self.state_update_vswitch,
                    'present': self.state_exit_unchanged,
                    'absent': self.state_create_vswitch,
                }
            }

            vswitch_states[self.state][self.check_vswitch_configuration()]()

        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    # Source from
    # https://github.com/rreubenur/pyvmomi-community-samples/blob/patch-1/samples/create_vswitch.py

    def state_create_vswitch(self):
        vss_spec = vim.host.VirtualSwitch.Specification()
        vss_spec.numPorts = self.number_of_ports
        vss_spec.mtu = self.mtu
        if self.nics:
            vss_spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=self.nics)
        self.host_system.configManager.networkSystem.AddVirtualSwitch(vswitchName=self.switch, spec=vss_spec)
        self.module.exit_json(changed=True)

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def state_destroy_vswitch(self):
        config = vim.host.NetworkConfig()

        for portgroup in self.host_system.configManager.networkSystem.networkInfo.portgroup:
            if portgroup.spec.vswitchName == self.vss.name:
                portgroup_config = vim.host.PortGroup.Config()
                portgroup_config.changeOperation = "remove"
                portgroup_config.spec = vim.host.PortGroup.Specification()
                portgroup_config.spec.name = portgroup.spec.name
                portgroup_config.spec.name = portgroup.spec.name
                portgroup_config.spec.vlanId = portgroup.spec.vlanId
                portgroup_config.spec.vswitchName = portgroup.spec.vswitchName
                portgroup_config.spec.policy = vim.host.NetworkPolicy()
                config.portgroup.append(portgroup_config)

        self.host_system.configManager.networkSystem.UpdateNetworkConfig(config, "modify")
        self.host_system.configManager.networkSystem.RemoveVirtualSwitch(self.vss.name)
        self.module.exit_json(changed=True)

    def state_update_vswitch(self):
        self.module.exit_json(changed=False, msg="Currently not implemented.")

    def check_vswitch_configuration(self):
        host = get_all_objs(self.content, [vim.HostSystem])
        if not host:
            self.module.fail_json(msg="Unable to find host")

        self.host_system = list(host.keys())[0]
        self.vss = find_vswitch_by_name(self.host_system, self.switch)

        if self.vss is None:
            return 'absent'
        else:
            return 'present'


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        switch=dict(type='str', required=True, aliases=['switch_name']),
        nics=dict(type='list', aliases=['nic_name']),
        number_of_ports=dict(type='int', default=128),
        mtu=dict(type='int', default=1500),
        state=dict(type='str', default='present', choices=['absent', 'present'])),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    host_virtual_switch = VMwareHostVirtualSwitch(module)
    host_virtual_switch.process_state()


if __name__ == '__main__':
    main()
