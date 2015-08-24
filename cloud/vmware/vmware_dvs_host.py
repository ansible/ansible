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
module: vmware_dvs_host
short_description: Add or remove a host from distributed virtual switch
description:
    - Add or remove a host from distributed virtual switch
version_added: 2.0
author: "Joseph Callen (@jcpowermac)"
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
    import collections
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def find_dvspg_by_name(dv_switch, portgroup_name):
    portgroups = dv_switch.portgroup

    for pg in portgroups:
        if pg.name == portgroup_name:
            return pg

    return None


def find_dvs_uplink_pg(dv_switch):
    # There should only always be a single uplink port group on
    # a distributed virtual switch

    if len(dv_switch.config.uplinkPortgroup):
        return dv_switch.config.uplinkPortgroup[0]
    else:
        return None


# operation should be edit, add and remove
def modify_dvs_host(dv_switch, host, operation, uplink_portgroup=None, vmnics=None):

    spec = vim.DistributedVirtualSwitch.ConfigSpec()

    spec.configVersion = dv_switch.config.configVersion
    spec.host = [vim.dvs.HostMember.ConfigSpec()]
    spec.host[0].operation = operation
    spec.host[0].host = host

    if operation in ("edit", "add"):
        spec.host[0].backing = vim.dvs.HostMember.PnicBacking()
        count = 0

        for nic in vmnics:
            spec.host[0].backing.pnicSpec.append(vim.dvs.HostMember.PnicSpec())
            spec.host[0].backing.pnicSpec[count].pnicDevice = nic
            spec.host[0].backing.pnicSpec[count].uplinkPortgroupKey = uplink_portgroup.key
            count += 1

    task = dv_switch.ReconfigureDvs_Task(spec)
    changed, result = wait_for_task(task)
    return changed, result


def state_destroy_dvs_host(module):

    operation = "remove"
    host = module.params['host']
    dv_switch = module.params['dv_switch']

    changed = True
    result = None

    if not module.check_mode:
        changed, result = modify_dvs_host(dv_switch, host, operation)
    module.exit_json(changed=changed, result=str(result))


def state_exit_unchanged(module):
    module.exit_json(changed=False)


def state_update_dvs_host(module):
    dv_switch = module.params['dv_switch']
    uplink_portgroup = module.params['uplink_portgroup']
    vmnics = module.params['vmnics']
    host = module.params['host']
    operation = "edit"
    changed = True
    result = None

    if not module.check_mode:
        changed, result = modify_dvs_host(dv_switch, host, operation, uplink_portgroup, vmnics)
    module.exit_json(changed=changed, result=str(result))


def state_create_dvs_host(module):
    dv_switch = module.params['dv_switch']
    uplink_portgroup = module.params['uplink_portgroup']
    vmnics = module.params['vmnics']
    host = module.params['host']
    operation = "add"
    changed = True
    result = None

    if not module.check_mode:
        changed, result = modify_dvs_host(dv_switch, host, operation, uplink_portgroup, vmnics)
    module.exit_json(changed=changed, result=str(result))


def find_host_attached_dvs(esxi_hostname, dv_switch):
    for dvs_host_member in dv_switch.config.host:
        if dvs_host_member.config.host.name == esxi_hostname:
            return dvs_host_member.config.host

    return None


def check_uplinks(dv_switch, host, vmnics):
    pnic_device = []
    
    for dvs_host_member in dv_switch.config.host:
        if dvs_host_member.config.host == host:
            for pnicSpec in dvs_host_member.config.backing.pnicSpec:
                pnic_device.append(pnicSpec.pnicDevice)
    
    return collections.Counter(pnic_device) == collections.Counter(vmnics)


def check_dvs_host_state(module):

    switch_name = module.params['switch_name']
    esxi_hostname = module.params['esxi_hostname']
    vmnics = module.params['vmnics']

    content = connect_to_api(module)
    module.params['content'] = content

    dv_switch = find_dvs_by_name(content, switch_name)

    if dv_switch is None:
        raise Exception("A distributed virtual switch %s does not exist" % switch_name)

    uplink_portgroup = find_dvs_uplink_pg(dv_switch)

    if uplink_portgroup is None:
        raise Exception("An uplink portgroup does not exist on the distributed virtual switch %s" % switch_name)

    module.params['dv_switch'] = dv_switch
    module.params['uplink_portgroup'] = uplink_portgroup

    host = find_host_attached_dvs(esxi_hostname, dv_switch)

    if host is None:
        # We still need the HostSystem object to add the host
        # to the distributed vswitch
        host = find_hostsystem_by_name(content, esxi_hostname)
        if host is None:
            module.fail_json(msg="The esxi_hostname %s does not exist in vCenter" % esxi_hostname)
        module.params['host'] = host
        return 'absent'
    else:
        module.params['host'] = host
        if check_uplinks(dv_switch, host, vmnics):
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

    try:

        dvs_host_states = {
            'absent': {
                'present': state_destroy_dvs_host,
                'absent': state_exit_unchanged,
            },
            'present': {
                'update': state_update_dvs_host,
                'present': state_exit_unchanged,
                'absent': state_create_dvs_host,
            }
        }

        dvs_host_states[module.params['state']][check_dvs_host_state(module)](module)
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
