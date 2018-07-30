#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
- This module can be used to add, remove and update a VMware Standard Switch to an ESXi host.
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
- Russell Teague (@mtnbikenc)
- Abhijeet Kasurde (@Akasurde) <akasurde@redhat.com>
notes:
- Tested on vSphere 5.5 and 6.5
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
    default: []
  number_of_ports:
    description:
    - Number of port to configure on vSwitch.
    default: 128
  mtu:
    description:
    - MTU to configure on vSwitch.
    default: 1500
  state:
    description:
    - Add or remove the switch.
    default: present
    choices: [ absent, present ]
  esxi_hostname:
    description:
    - Manage the vSwitch using this ESXi host system.
    version_added: "2.5"
    aliases: [ 'host' ]
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

- name: Add a VMware vSwitch to a specific host system
  vmware_vswitch:
    hostname: 192.168.10.1
    username: esxi_username
    password: esxi_password
    esxi_hostname: DC0_H0
    switch_name: vswitch_001
    nic_name: vmnic0
    mtu: 9000
  delegate_to: localhost
'''

RETURN = """
result:
    description: information about performed operation
    returned: always
    type: string
    sample: "vSwitch 'vSwitch_1002' is created successfully"
"""

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native


class VMwareHostVirtualSwitch(PyVmomi):
    def __init__(self, module):
        super(VMwareHostVirtualSwitch, self).__init__(module)
        self.host_system = None
        self.vss = None
        self.switch = module.params['switch']
        self.number_of_ports = module.params['number_of_ports']
        self.nics = module.params['nics']
        self.mtu = module.params['mtu']
        self.state = module.params['state']
        esxi_hostname = module.params['esxi_hostname']

        hosts = self.get_all_host_objs(esxi_host_name=esxi_hostname)
        if hosts:
            self.host_system = hosts[0]
        else:
            self.module.fail_json(msg="Failed to get details of ESXi server."
                                      " Please specify esxi_hostname.")

        if self.params.get('state') == 'present':
            # Gather information about all vSwitches and Physical NICs
            network_manager = self.host_system.configManager.networkSystem
            available_pnic = [pnic.device for pnic in network_manager.networkInfo.pnic]
            self.available_vswitches = dict()
            for available_vswitch in network_manager.networkInfo.vswitch:
                used_pnic = []
                for pnic in available_vswitch.pnic:
                    # vSwitch contains all PNICs as string in format of 'key-vim.host.PhysicalNic-vmnic0'
                    m_pnic = pnic.split("-", 3)[-1]
                    used_pnic.append(m_pnic)
                self.available_vswitches[available_vswitch.name] = dict(pnic=used_pnic,
                                                                        mtu=available_vswitch.mtu,
                                                                        num_ports=available_vswitch.spec.numPorts,
                                                                        )
            for desired_pnic in self.nics:
                if desired_pnic not in available_pnic:
                    # Check if pnic does not exists
                    self.module.fail_json(msg="Specified Physical NIC '%s' does not"
                                              " exists on given ESXi '%s'." % (desired_pnic,
                                                                               self.host_system.name))
                for vswitch in self.available_vswitches:
                    if desired_pnic in self.available_vswitches[vswitch]['pnic'] and vswitch != self.switch:
                        # Check if pnic is already part of some other vSwitch
                        self.module.fail_json(msg="Specified Physical NIC '%s' is already used"
                                                  " by vSwitch '%s'." % (desired_pnic, vswitch))

    def process_state(self):
        """
        Manage internal state of vSwitch
        """
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
        except Exception as e:
            self.module.fail_json(msg=to_native(e))

    def state_create_vswitch(self):
        """
        Create a virtual switch

        Source from
        https://github.com/rreubenur/pyvmomi-community-samples/blob/patch-1/samples/create_vswitch.py

        """

        results = dict(changed=False, result="")
        vss_spec = vim.host.VirtualSwitch.Specification()
        vss_spec.numPorts = self.number_of_ports
        vss_spec.mtu = self.mtu
        if self.nics:
            vss_spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=self.nics)
        try:
            network_mgr = self.host_system.configManager.networkSystem
            if network_mgr:
                network_mgr.AddVirtualSwitch(vswitchName=self.switch,
                                             spec=vss_spec)
                results['changed'] = True
                results['result'] = "vSwitch '%s' is created successfully" % self.switch
            else:
                self.module.fail_json(msg="Failed to find network manager for ESXi system")
        except vim.fault.AlreadyExists as already_exists:
            results['result'] = "vSwitch with name %s already exists: %s" % (self.switch,
                                                                             to_native(already_exists.msg))
        except vim.fault.ResourceInUse as resource_used:
            self.module.fail_json(msg="Failed to add vSwitch '%s' as physical network adapter"
                                      " being bridged is already in use: %s" % (self.switch,
                                                                                to_native(resource_used.msg)))
        except vim.fault.HostConfigFault as host_config_fault:
            self.module.fail_json(msg="Failed to add vSwitch '%s' due to host"
                                      " configuration fault : %s" % (self.switch,
                                                                     to_native(host_config_fault.msg)))
        except vmodl.fault.InvalidArgument as invalid_argument:
            self.module.fail_json(msg="Failed to add vSwitch '%s', this can be due to either of following :"
                                      " 1. vSwitch Name exceeds the maximum allowed length,"
                                      " 2. Number of ports specified falls out of valid range,"
                                      " 3. Network policy is invalid,"
                                      " 4. Beacon configuration is invalid : %s" % (self.switch,
                                                                                    to_native(invalid_argument.msg)))
        except vmodl.fault.SystemError as system_error:
            self.module.fail_json(msg="Failed to add vSwitch '%s' due to : %s" % (self.switch,
                                                                                  to_native(system_error.msg)))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to add vSwitch '%s' due to"
                                      " generic exception : %s" % (self.switch,
                                                                   to_native(generic_exc)))
        self.module.exit_json(**results)

    def state_exit_unchanged(self):
        """
        Declare exit without unchanged
        """
        self.module.exit_json(changed=False)

    def state_destroy_vswitch(self):
        """
        Remove vSwitch from configuration

        """
        results = dict(changed=False, result="")

        try:
            self.host_system.configManager.networkSystem.RemoveVirtualSwitch(self.vss.name)
            results['changed'] = True
            results['result'] = "vSwitch '%s' removed successfully." % self.vss.name
        except vim.fault.NotFound as vswitch_not_found:
            results['result'] = "vSwitch '%s' not available. %s" % (self.switch,
                                                                    to_native(vswitch_not_found.msg))
        except vim.fault.ResourceInUse as vswitch_in_use:
            self.module.fail_json(msg="Failed to remove vSwitch '%s' as vSwitch"
                                      " is used by several virtual"
                                      " network adapters: %s" % (self.switch,
                                                                 to_native(vswitch_in_use.msg)))
        except vim.fault.HostConfigFault as host_config_fault:
            self.module.fail_json(msg="Failed to remove vSwitch '%s' due to host"
                                      " configuration fault : %s" % (self.switch,
                                                                     to_native(host_config_fault.msg)))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to remove vSwitch '%s' due to generic"
                                      " exception : %s" % (self.switch,
                                                           to_native(generic_exc)))

        self.module.exit_json(**results)

    def state_update_vswitch(self):
        """
        Update vSwitch

        """
        results = dict(changed=False, result="No change in vSwitch '%s'" % self.switch)
        vswitch_pnic_info = self.available_vswitches[self.switch]
        remain_pnic = []
        for desired_pnic in self.nics:
            if desired_pnic not in vswitch_pnic_info['pnic']:
                remain_pnic.append(desired_pnic)

        diff = False
        # Update all nics
        all_nics = vswitch_pnic_info['pnic']
        if remain_pnic:
            all_nics += remain_pnic
            diff = True

        if vswitch_pnic_info['mtu'] != self.mtu or \
                vswitch_pnic_info['num_ports'] != self.number_of_ports:
            diff = True

        if not all_nics:
            diff = False
            results['result'] += " as no NICs provided / found which are required while updating vSwitch."

        try:
            if diff:
                # vSwitch needs every parameter again while updating,
                # even if we are updating any one of them
                vss_spec = vim.host.VirtualSwitch.Specification()
                vss_spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=all_nics)
                vss_spec.numPorts = self.number_of_ports
                vss_spec.mtu = self.mtu

                network_mgr = self.host_system.configManager.networkSystem
                if network_mgr:
                    network_mgr.UpdateVirtualSwitch(vswitchName=self.switch,
                                                    spec=vss_spec)
                    results['changed'] = True
                    results['result'] = "vSwitch '%s' is updated successfully" % self.switch
                else:
                    self.module.fail_json(msg="Failed to find network manager for ESXi system.")
        except vim.fault.ResourceInUse as resource_used:
            self.module.fail_json(msg="Failed to update vSwitch '%s' as physical network adapter"
                                      " being bridged is already in use: %s" % (self.switch,
                                                                                to_native(resource_used.msg)))
        except vim.fault.NotFound as not_found:
            self.module.fail_json(msg="Failed to update vSwitch with name '%s'"
                                      " as it does not exists: %s" % (self.switch,
                                                                      to_native(not_found.msg)))

        except vim.fault.HostConfigFault as host_config_fault:
            self.module.fail_json(msg="Failed to update vSwitch '%s' due to host"
                                      " configuration fault : %s" % (self.switch,
                                                                     to_native(host_config_fault.msg)))
        except vmodl.fault.InvalidArgument as invalid_argument:
            self.module.fail_json(msg="Failed to update vSwitch '%s', this can be due to either of following :"
                                      " 1. vSwitch Name exceeds the maximum allowed length,"
                                      " 2. Number of ports specified falls out of valid range,"
                                      " 3. Network policy is invalid,"
                                      " 4. Beacon configuration is invalid : %s" % (self.switch,
                                                                                    to_native(invalid_argument.msg)))
        except vmodl.fault.SystemError as system_error:
            self.module.fail_json(msg="Failed to update vSwitch '%s' due to : %s" % (self.switch,
                                                                                     to_native(system_error.msg)))
        except vmodl.fault.NotSupported as not_supported:
            self.module.fail_json(msg="Failed to update vSwitch '%s' as network adapter teaming policy"
                                      " is set but is not supported : %s" % (self.switch,
                                                                             to_native(not_supported.msg)))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to update vSwitch '%s' due to"
                                      " generic exception : %s" % (self.switch,
                                                                   to_native(generic_exc)))
        self.module.exit_json(**results)

    def check_vswitch_configuration(self):
        """
        Check if vSwitch exists
        Returns: 'present' if vSwitch exists or 'absent' if not

        """
        self.vss = self.find_vswitch_by_name(self.host_system, self.switch)
        if self.vss is None:
            return 'absent'
        else:
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
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        switch=dict(type='str', required=True, aliases=['switch_name']),
        nics=dict(type='list', aliases=['nic_name'], default=[]),
        number_of_ports=dict(type='int', default=128),
        mtu=dict(type='int', default=1500),
        state=dict(type='str', default='present', choices=['absent', 'present'])),
        esxi_hostname=dict(type='str', aliases=['host']),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    host_virtual_switch = VMwareHostVirtualSwitch(module)
    host_virtual_switch.process_state()


if __name__ == '__main__':
    main()
