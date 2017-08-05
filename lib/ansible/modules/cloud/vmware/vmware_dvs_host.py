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
module: vmware_dvs_host
short_description: Add or remove a host from distributed virtual switch
description:
    - Add or remove a host from distributed virtual switch
version_added: 2.0
author: "Joseph Callen (@jcpowermac)"
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.7"
    - PyVmomi
options:
    esxi_hostname:
        description:
            - The ESXi hostname
        required: True
    switch_name:
        description:
            - The name of the Distributed vSwitch
        required: True
    vmnics:
        description:
            - The ESXi hosts vmnics to use with the Distributed vSwitch
        required: True
    state:
        description:
            - If the host should be present or absent attached to the vSwitch
        choices: ['present', 'absent']
        required: True
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
# Example vmware_dvs_host command from Ansible Playbooks
- name: Add Host to dVS
  local_action:
    module: vmware_dvs_host
    hostname: vcenter_ip_or_hostname
    username: vcenter_username
    password: vcenter_password
    esxi_hostname: esxi_hostname_as_listed_in_vcenter
    switch_name: dvSwitch
    vmnics:
        - vmnic0
        - vmnic1
    state: present
'''

try:
    from collections import Counter
    HAS_COLLECTIONS_COUNTER = True
except ImportError:
    HAS_COLLECTIONS_COUNTER = False

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (HAS_PYVMOMI, connect_to_api, find_dvs_by_name,
                                         find_hostsystem_by_name, vmware_argument_spec, wait_for_task)


class VMwareDvsHost(object):
    def __init__(self, module):
        self.module = module
        self.dv_switch = None
        self.uplink_portgroup = None
        self.host = None
        self.dv_switch = None
        self.nic = None
        self.content = connect_to_api(self.module)
        self.state = self.module.params['state']
        self.switch_name = self.module.params['switch_name']
        self.esxi_hostname = self.module.params['esxi_hostname']
        self.vmnics = self.module.params['vmnics']

    def process_state(self):
        try:
            dvs_host_states = {
                'absent': {
                    'present': self.state_destroy_dvs_host,
                    'absent': self.state_exit_unchanged,
                },
                'present': {
                    'update': self.state_update_dvs_host,
                    'present': self.state_exit_unchanged,
                    'absent': self.state_create_dvs_host,
                }
            }

            dvs_host_states[self.state][self.check_dvs_host_state()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def find_dvspg_by_name(self):
        portgroups = self.dv_switch.portgroup

        for pg in portgroups:
            if pg.name == self.portgroup_name:
                return pg
        return None

    def find_dvs_uplink_pg(self):
        # There should only always be a single uplink port group on
        # a distributed virtual switch

        if len(self.dv_switch.config.uplinkPortgroup):
            return self.dv_switch.config.uplinkPortgroup[0]
        else:
            return None

    # operation should be edit, add and remove
    def modify_dvs_host(self, operation):
        spec = vim.DistributedVirtualSwitch.ConfigSpec()
        spec.configVersion = self.dv_switch.config.configVersion
        spec.host = [vim.dvs.HostMember.ConfigSpec()]
        spec.host[0].operation = operation
        spec.host[0].host = self.host

        if operation in ("edit", "add"):
            spec.host[0].backing = vim.dvs.HostMember.PnicBacking()
            count = 0

            for nic in self.vmnics:
                spec.host[0].backing.pnicSpec.append(vim.dvs.HostMember.PnicSpec())
                spec.host[0].backing.pnicSpec[count].pnicDevice = nic
                spec.host[0].backing.pnicSpec[count].uplinkPortgroupKey = self.uplink_portgroup.key
                count += 1

        task = self.dv_switch.ReconfigureDvs_Task(spec)
        changed, result = wait_for_task(task)
        return changed, result

    def state_destroy_dvs_host(self):
        operation = "remove"
        changed = True
        result = None

        if not self.module.check_mode:
            changed, result = self.modify_dvs_host(operation)
        self.module.exit_json(changed=changed, result=str(result))

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def state_update_dvs_host(self):
        operation = "edit"
        changed = True
        result = None

        if not self.module.check_mode:
            changed, result = self.modify_dvs_host(operation)
        self.module.exit_json(changed=changed, result=str(result))

    def state_create_dvs_host(self):
        operation = "add"
        changed = True
        result = None

        if not self.module.check_mode:
            changed, result = self.modify_dvs_host(operation)
        self.module.exit_json(changed=changed, result=str(result))

    def find_host_attached_dvs(self):
        for dvs_host_member in self.dv_switch.config.host:
            if dvs_host_member.config.host.name == self.esxi_hostname:
                return dvs_host_member.config.host

        return None

    def check_uplinks(self):
        pnic_device = []

        for dvs_host_member in self.dv_switch.config.host:
            if dvs_host_member.config.host == self.host:
                for pnicSpec in dvs_host_member.config.backing.pnicSpec:
                    pnic_device.append(pnicSpec.pnicDevice)

        return Counter(pnic_device) == Counter(self.vmnics)

    def check_dvs_host_state(self):
        self.dv_switch = find_dvs_by_name(self.content, self.switch_name)

        if self.dv_switch is None:
            raise Exception("A distributed virtual switch %s does not exist" % self.switch_name)

        self.uplink_portgroup = self.find_dvs_uplink_pg()

        if self.uplink_portgroup is None:
            raise Exception("An uplink portgroup does not exist on the distributed virtual switch %s"
                            % self.switch_name)

        self.host = self.find_host_attached_dvs()

        if self.host is None:
            # We still need the HostSystem object to add the host
            # to the distributed vswitch
            self.host = find_hostsystem_by_name(self.content, self.esxi_hostname)
            if self.host is None:
                self.module.fail_json(msg="The esxi_hostname %s does not exist in vCenter" % self.esxi_hostname)
            return 'absent'
        else:
            if self.check_uplinks():
                return 'present'
            else:
                return 'update'


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(esxi_hostname=dict(required=True, type='str'),
                         switch_name=dict(required=True, type='str'),
                         vmnics=dict(required=True, type='list'),
                         state=dict(default='present', choices=['present', 'absent'], type='str')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    if not HAS_COLLECTIONS_COUNTER:
        module.fail_json(msg='collections.Counter from Python-2.7 is required for this module')

    vmware_dvs_host = VMwareDvsHost(module)
    vmware_dvs_host.process_state()


if __name__ == '__main__':
    main()
