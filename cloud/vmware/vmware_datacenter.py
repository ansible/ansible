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
module: vmware_datacenter
short_description: Manage VMware vSphere Datacenters
description:
    - Manage VMware vSphere Datacenters
version_added: 2.0
author: "Joseph Callen (@jcpowermac), Kamil Szczygiel (@kamsz)"
notes:
    - Tested on vSphere 6.0
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
    datacenter_name:
        description:
            - The name of the datacenter the cluster will be created in.
        required: True
    state:
        description:
            - If the datacenter should be present or absent
        choices: ['present', 'absent']
        default: present
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
# Example vmware_datacenter command from Ansible Playbooks
- name: Create Datacenter
      local_action: >
        vmware_datacenter
        hostname="{{ ansible_ssh_host }}" username=root password=vmware
        datacenter_name="datacenter" state=present
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def get_datacenter(context, module):
    try:
        datacenter_name = module.params.get('datacenter_name')
        datacenter = find_datacenter_by_name(context, datacenter_name)
        return datacenter
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)


def create_datacenter(context, module):
    datacenter_name = module.params.get('datacenter_name')
    folder = context.rootFolder

    try:
        datacenter = get_datacenter(context, module)
        if not datacenter:
            changed = True
            if not module.check_mode:
                folder.CreateDatacenter(name=datacenter_name)
        module.exit_json(changed=changed)
    except vim.fault.DuplicateName:
        module.fail_json(msg="A datacenter with the name %s already exists" % datacenter_name)
    except vim.fault.InvalidName:
        module.fail_json(msg="%s is an invalid name for a cluster" % datacenter_name)
    except vmodl.fault.NotSupported:
        # This should never happen
        module.fail_json(msg="Trying to create a datacenter on an incorrect folder object")
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)


def destroy_datacenter(context, module):
    result = None

    try:
        datacenter = get_datacenter(context, module)
        if datacenter:
            changed = True
            if not module.check_mode:
                task = datacenter.Destroy_Task()
                changed, result = wait_for_task(task)
        module.exit_json(changed=changed, result=result)
    except vim.fault.VimFault as vim_fault:
        module.fail_json(msg=vim_fault.msg)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            datacenter_name=dict(required=True, type='str'),
            state=dict(default='present', choices=['present', 'absent'], type='str')
        )
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    context = connect_to_api(module)
    state = module.params.get('state')

    if state == 'present':
        create_datacenter(context, module)

    if state == 'absent':
        destroy_datacenter(context, module)

from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *

if __name__ == '__main__':
    main()
