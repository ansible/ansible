#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Bede Carroll <bc+github () bedecarroll.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_vmotion
short_description: Move a virtual machine using vMotion
description:
    - Using VMware vCenter, move a virtual machine using vMotion to a different
      host.
version_added: 2.2
author:
- Bede Carroll (@bedecarroll)
notes:
    - Tested on vSphere 6.0
requirements:
    - "python >= 2.6"
    - pyVmomi
options:
    vm_name:
        description:
            - Name of the VM to perform a vMotion on
        required: True
        aliases: ['vm']
    destination_host:
        description:
            - Name of the end host the VM should be running on
        required: True
        aliases: ['destination']
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
# Example from Ansible playbook

    - name: Perform vMotion of VM
      local_action:
        module: vmware_vmotion
        hostname: 'vcenter_hostname'
        username: 'vcenter_username'
        password: 'vcenter_password'
        validate_certs: False
        vm_name: 'vm_name_as_per_vcenter'
        destination_host: 'destination_host_as_per_vcenter'
'''

RETURN = '''
running_host:
    description: List the host the virtual machine is registered to
    returned: changed or success
    type: string
    sample: 'host1.example.com'
'''

try:
    from pyVmomi import vim
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (connect_to_api, find_hostsystem_by_name, find_vm_by_name,
                                         vmware_argument_spec, wait_for_task)


def migrate_vm(vm_object, host_object):
    """
    Migrate virtual machine and return the task.
    """
    relocate_spec = vim.vm.RelocateSpec(host=host_object)
    task_object = vm_object.Relocate(relocate_spec)
    return task_object


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            vm_name=dict(required=True, aliases=['vm'], type='str'),
            destination_host=dict(required=True, aliases=['destination'], type='str'),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyVmomi is required for this module')

    content = connect_to_api(module=module)

    vm_object = find_vm_by_name(content=content, vm_name=module.params['vm_name'])
    host_object = find_hostsystem_by_name(content=content, hostname=module.params['destination_host'])

    # Setup result
    result = {
        'changed': False
    }

    # Check if we could find the VM or Host
    if not vm_object:
        module.fail_json(msg='Cannot find virtual machine')
    if not host_object:
        module.fail_json(msg='Cannot find host')

    # Make sure VM isn't already at the destination
    if vm_object.runtime.host.name == module.params['destination_host']:
        module.exit_json(**result)

    if not module.check_mode:
        # Migrate VM and get Task object back
        task_object = migrate_vm(vm_object=vm_object, host_object=host_object)

        # Wait for task to complete
        wait_for_task(task_object)

        # If task was a success the VM has moved, update running_host and complete module
        if task_object.info.state == vim.TaskInfo.State.success:
            vm_object = find_vm_by_name(content=content, vm_name=module.params['vm_name'])
            result['running_host'] = vm_object.runtime.host.name
            result['changed'] = True
            module.exit_json(**result)
        else:
            if task_object.info.error is None:
                module.fail_json(msg='Unable to migrate VM due to an error, please check vCenter')
            else:
                module.fail_json(msg='Unable to migrate VM due to an error: %s' % task_object.info.error)
    else:
        # If we are in check mode return a result as if move was performed
        result['running_host'] = module.params['destination_host']
        result['changed'] = True
        module.exit_json(**result)


if __name__ == '__main__':
    main()
