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
    hostname:
        description:
            - The hostname or IP address of the ESXi server
        required: True
    username:
        description:
            - The username of the ESXi server
        required: True
        aliases: ['user', 'admin']
    password:
        description:
            - The password of the ESXi server
        required: True
        aliases: ['pass', 'pwd']
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
'''

EXAMPLES = '''
Example from Ansible playbook

    - name: Add Management Network VM Portgroup
      local_action:
        module: vmware_portgroup
        hostname: esxi_hostname
        username: esxi_username
        password: esxi_password
        switch_name: vswitch_name
        portgroup_name: portgroup_name
        vlan_id: vlan_id
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def create_port_group(host_system, portgroup_name, vlan_id, vswitch_name):

    config = vim.host.NetworkConfig()
    config.portgroup = [vim.host.PortGroup.Config()]
    config.portgroup[0].changeOperation = "add"
    config.portgroup[0].spec = vim.host.PortGroup.Specification()
    config.portgroup[0].spec.name = portgroup_name
    config.portgroup[0].spec.vlanId = vlan_id
    config.portgroup[0].spec.vswitchName = vswitch_name
    config.portgroup[0].spec.policy = vim.host.NetworkPolicy()

    host_network_config_result = host_system.configManager.networkSystem.UpdateNetworkConfig(config, "modify")
    return True


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(portgroup_name=dict(required=True, type='str'),
                         switch_name=dict(required=True, type='str'),
                         vlan_id=dict(required=True, type='int')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    portgroup_name = module.params['portgroup_name']
    switch_name = module.params['switch_name']
    vlan_id = module.params['vlan_id']

    try:
        content = connect_to_api(module)
        host = get_all_objs(content, [vim.HostSystem])
        if not host:
            raise SystemExit("Unable to locate Physical Host.")
        host_system = host.keys()[0]

        changed = create_port_group(host_system, portgroup_name, vlan_id, switch_name)

        module.exit_json(changed=changed)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
