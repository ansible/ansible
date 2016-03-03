#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Joseph Callen <jcallen () csc.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: vmware_dvs_portgroup
short_description: Create or remove a Distributed vSwitch portgroup
description:
    - Create or remove a Distributed vSwitch portgroup
version_added: 2.0
author: "Joseph Callen (@jcpowermac)"
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    portgroup_name:
        description:
            - The name of the portgroup that is to be created or deleted
        required: True
    switch_name:
        description:
            - The name of the distributed vSwitch the port group should be created on.
        required: True
    vlan_id:
        description:
            - The VLAN ID that should be configured with the portgroup
        required: True
    num_ports:
        description:
            - The number of ports the portgroup should contain
        required: True
    portgroup_type:
        description:
            - See VMware KB 1022312 regarding portgroup types
        required: True
        choices:
            - 'earlyBinding'
            - 'lateBinding'
            - 'ephemeral'
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
   - name: Create Management portgroup
      local_action:
        module: vmware_dvs_portgroup
        hostname: vcenter_ip_or_hostname
        username: vcenter_username
        password: vcenter_password
        portgroup_name: Management
        switch_name: dvSwitch
        vlan_id: 123 
        num_ports: 120
        portgroup_type: earlyBinding
        state: present
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


class VMwareDvsPortgroup(object):
    def __init__(self, module):
        self.module = module
        self.dvs_portgroup = None
        self.switch_name = self.module.params['switch_name']
        self.portgroup_name = self.module.params['portgroup_name']
        self.vlan_id = self.module.params['vlan_id']
        self.num_ports = self.module.params['num_ports']
        self.portgroup_type = self.module.params['portgroup_type']
        self.dv_switch = None
        self.state = self.module.params['state']
        self.content = connect_to_api(module)
        
    def process_state(self):
        try:
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
            dvspg_states[self.state][self.check_dvspg_state()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def create_port_group(self):
        config = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()

        config.name = self.portgroup_name
        config.numPorts = self.num_ports

        # vim.VMwareDVSPortSetting() does not exist in the pyvmomi documentation
        # but this is the correct managed object type.

        config.defaultPortConfig = vim.VMwareDVSPortSetting()

        # vim.VmwareDistributedVirtualSwitchVlanIdSpec() does not exist in the
        # pyvmomi documentation but this is the correct managed object type
        config.defaultPortConfig.vlan = vim.VmwareDistributedVirtualSwitchVlanIdSpec()
        config.defaultPortConfig.vlan.inherited = False
        config.defaultPortConfig.vlan.vlanId = self.vlan_id
        config.type = self.portgroup_type

        spec = [config]
        task = self.dv_switch.AddDVPortgroup_Task(spec)
        changed, result = wait_for_task(task)
        return changed, result

    def state_destroy_dvspg(self):
        changed = True
        result = None

        if not self.module.check_mode:
            task = dvs_portgroup.Destroy_Task()
            changed, result = wait_for_task(task)
        self.module.exit_json(changed=changed, result=str(result))

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def state_update_dvspg(self):
        self.module.exit_json(changed=False, msg="Currently not implemented.")

    def state_create_dvspg(self):
        changed = True
        result = None

        if not self.module.check_mode:
            changed, result = self.create_port_group()
        self.module.exit_json(changed=changed, result=str(result))

    def check_dvspg_state(self):
        self.dv_switch = find_dvs_by_name(self.content, self.switch_name)

        if self.dv_switch is None:
            raise Exception("A distributed virtual switch with name %s does not exist" % self.switch_name)
        self.dvs_portgroup = find_dvspg_by_name(self.dv_switch, self.portgroup_name)

        if self.dvs_portgroup is None:
            return 'absent'
        else:
            return 'present'


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(portgroup_name=dict(required=True, type='str'),
                         switch_name=dict(required=True, type='str'),
                         vlan_id=dict(required=True, type='int'),
                         num_ports=dict(required=True, type='int'),
                         portgroup_type=dict(required=True, choices=['earlyBinding', 'lateBinding', 'ephemeral'], type='str'),
                         state=dict(default='present', choices=['present', 'absent'], type='str')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    vmware_dvs_portgroup = VMwareDvsPortgroup(module)
    vmware_dvs_portgroup.process_state()

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
