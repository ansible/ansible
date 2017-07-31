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
  local_action:
    module: vmware_datacenter
    hostname: "{{ ansible_ssh_host }}"
    username: root
    password: vmware
    datacenter_name: "datacenter"
    state: present
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (HAS_PYVMOMI, connect_to_api, find_datacenter_by_name,
                                         vmware_argument_spec, wait_for_task)


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
        changed = False
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
        changed = False
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


if __name__ == '__main__':
    main()
