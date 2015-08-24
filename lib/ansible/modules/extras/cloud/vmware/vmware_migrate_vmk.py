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
module: vmware_migrate_vmk
short_description: Migrate a VMK interface from VSS to VDS
description:
    - Migrate a VMK interface from VSS to VDS
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
            - The hostname or IP address of the vSphere vCenter API server
        required: True
    username:
        description:
            - The username of the vSphere vCenter
        required: True
        aliases: ['user', 'admin']
    password:
        description:
            - The password of the vSphere vCenter
        required: True
        aliases: ['pass', 'pwd']
    esxi_hostname:
        description:
            - ESXi hostname to be managed
        required: True
    device:
        description:
            - VMK interface name
        required: True
    current_switch_name:
        description:
            - Switch VMK interface is currently on
        required: True
    current_portgroup_name:
        description:
            - Portgroup name VMK interface is currently on
        required: True
    migrate_switch_name:
        description:
            - Switch name to migrate VMK interface to
        required: True
    migrate_portgroup_name:
        description:
            - Portgroup name to migrate VMK interface to
        required: True
'''

EXAMPLES = '''
Example from Ansible playbook

    - name: Migrate Management vmk
      local_action:
        module: vmware_migrate_vmk
        hostname: vcsa_host
        username: vcsa_user
        password: vcsa_pass
        esxi_hostname: esxi_hostname
        device: vmk1
        current_switch_name: temp_vswitch
        current_portgroup_name: esx-mgmt
        migrate_switch_name: dvSwitch
        migrate_portgroup_name: Management
'''


try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def state_exit_unchanged(module):
    module.exit_json(changed=False)


def state_migrate_vds_vss(module):
    module.exit_json(changed=False, msg="Currently Not Implemented")


def create_host_vnic_config(dv_switch_uuid, portgroup_key, device):

    host_vnic_config = vim.host.VirtualNic.Config()
    host_vnic_config.spec = vim.host.VirtualNic.Specification()
    host_vnic_config.changeOperation = "edit"
    host_vnic_config.device = device
    host_vnic_config.portgroup = ""
    host_vnic_config.spec.distributedVirtualPort = vim.dvs.PortConnection()
    host_vnic_config.spec.distributedVirtualPort.switchUuid = dv_switch_uuid
    host_vnic_config.spec.distributedVirtualPort.portgroupKey = portgroup_key

    return host_vnic_config


def create_port_group_config(switch_name, portgroup_name):
    port_group_config = vim.host.PortGroup.Config()
    port_group_config.spec = vim.host.PortGroup.Specification()

    port_group_config.changeOperation = "remove"
    port_group_config.spec.name = portgroup_name
    port_group_config.spec.vlanId = -1
    port_group_config.spec.vswitchName = switch_name
    port_group_config.spec.policy = vim.host.NetworkPolicy()

    return port_group_config


def state_migrate_vss_vds(module):
    content = module.params['content']
    host_system = module.params['host_system']
    migrate_switch_name = module.params['migrate_switch_name']
    migrate_portgroup_name = module.params['migrate_portgroup_name']
    current_portgroup_name = module.params['current_portgroup_name']
    current_switch_name = module.params['current_switch_name']
    device = module.params['device']

    host_network_system = host_system.configManager.networkSystem

    dv_switch = find_dvs_by_name(content, migrate_switch_name)
    pg = find_dvspg_by_name(dv_switch, migrate_portgroup_name)

    config = vim.host.NetworkConfig()
    config.portgroup = [create_port_group_config(current_switch_name, current_portgroup_name)]
    config.vnic = [create_host_vnic_config(dv_switch.uuid, pg.key, device)]
    host_network_system.UpdateNetworkConfig(config, "modify")
    module.exit_json(changed=True)


def check_vmk_current_state(module):

    device = module.params['device']
    esxi_hostname = module.params['esxi_hostname']
    current_portgroup_name = module.params['current_portgroup_name']
    current_switch_name = module.params['current_switch_name']

    content = connect_to_api(module)

    host_system = find_hostsystem_by_name(content, esxi_hostname)

    module.params['content'] = content
    module.params['host_system'] = host_system

    for vnic in host_system.configManager.networkSystem.networkInfo.vnic:
        if vnic.device == device:
            module.params['vnic'] = vnic
            if vnic.spec.distributedVirtualPort is None:
                if vnic.portgroup == current_portgroup_name:
                    return "migrate_vss_vds"
            else:
                dvs = find_dvs_by_name(content, current_switch_name)
                if dvs is None:
                    return "migrated"
                if vnic.spec.distributedVirtualPort.switchUuid == dvs.uuid:
                    return "migrate_vds_vss"


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(esxi_hostname=dict(required=True, type='str'),
                              device=dict(required=True, type='str'),
                              current_switch_name=dict(required=True, type='str'),
                              current_portgroup_name=dict(required=True, type='str'),
                              migrate_switch_name=dict(required=True, type='str'),
                              migrate_portgroup_name=dict(required=True, type='str')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi required for this module')

    try:
        vmk_migration_states = {
            'migrate_vss_vds': state_migrate_vss_vds,
            'migrate_vds_vss': state_migrate_vds_vss,
            'migrated': state_exit_unchanged
        }

        vmk_migration_states[check_vmk_current_state(module)](module)

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
