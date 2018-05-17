#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vmware_guest_powerstate
short_description: Manages power states of virtual machines in vCenter
description:
- Power on / Power off / Restart a virtual machine.
version_added: '2.5'
author:
- Abhijeet Kasurde (@Akasurde) <akasurde@redhat.com>
requirements:
- python >= 2.6
- PyVmomi
options:
  state:
    description:
    - Set the state of the virtual machine.
    choices: [ powered-off, powered-on, reboot-guest, restarted, shutdown-guest, suspended, present]
    default: present
  name:
    description:
    - Name of the virtual machine to work with.
    - Virtual machine names in vCenter are not necessarily unique, which may be problematic, see C(name_match).
  name_match:
    description:
    - If multiple virtual machines matching the name, use the first or last found.
    default: first
    choices: [ first, last ]
  uuid:
    description:
    - UUID of the instance to manage if known, this is VMware's unique identifier.
    - This is required if name is not supplied.
  folder:
    description:
    - Destination folder, absolute or relative path to find an existing guest or create the new guest.
    - The folder should include the datacenter. ESX's datacenter is ha-datacenter
    - 'Examples:'
    - '   folder: /ha-datacenter/vm'
    - '   folder: ha-datacenter/vm'
    - '   folder: /datacenter1/vm'
    - '   folder: datacenter1/vm'
    - '   folder: /datacenter1/vm/folder1'
    - '   folder: datacenter1/vm/folder1'
    - '   folder: /folder1/datacenter1/vm'
    - '   folder: folder1/datacenter1/vm'
    - '   folder: /folder1/datacenter1/vm/folder2'
    - '   folder: vm/folder2'
    - '   folder: folder2'
    default: /vm
  scheduled_at:
    description:
    - Date and time in string format at which specificed task needs to be performed.
    - "The required format for date and time - 'dd/mm/yyyy hh:mm'."
    - Scheduling task requires vCenter server. A standalone ESXi server does not support this option.
  force:
    description:
    - Ignore warnings and complete the actions.
    - This parameter is useful while forcing virtual machine state.
    default: False
    type: bool
    version_added: 2.5
  state_change_timeout:
    description:
    - If the C(state) is set to C(shutdown-guest), by default the module will return immediately after sending the shutdown signal.
    - If this argument is set to a positive integer, the module will instead wait for the VM to reach the poweredoff state.
    - The value sets a timeout in seconds for the module to wait for the state change.
    default: 0
    version_added: '2.6'
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Set the state of a virtual machine to poweroff
  vmware_guest_powerstate:
    hostname: 192.0.2.44
    username: administrator@vsphere.local
    password: vmware
    validate_certs: no
    folder: /testvms
    name: testvm_2
    state: powered-off
  delegate_to: localhost
  register: deploy

- name: Set the state of a virtual machine to poweroff at given scheduled time
  vmware_guest_powerstate:
    hostname: 192.0.2.44
    username: administrator@vsphere.local
    password: vmware
    validate_certs: no
    folder: /datacenter-1/vm/my_folder
    name: testvm_2
    state: powered-off
    scheduled_at: "09/01/2018 10:18"
  delegate_to: localhost
  register: deploy_at_schedule_datetime

- name: Wait for the virtual machine to shutdown
  vmware_guest_powerstate:
    hostname: 192.0.2.44
    username: administrator@vsphere.local
    password: vmware
    validate_certs: no
    name: testvm_2
    state: shutdown-guest
    state_change_timeout: 200
  delegate_to: localhost
  register: deploy
'''

RETURN = r''' # '''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from datetime import datetime
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, set_vm_power_state, vmware_argument_spec
from ansible.module_utils._text import to_native


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present',
                   choices=['present', 'powered-off', 'powered-on', 'reboot-guest', 'restarted', 'shutdown-guest', 'suspended']),
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        folder=dict(type='str', default='/vm'),
        force=dict(type='bool', default=False),
        scheduled_at=dict(type='str'),
        state_change_timeout=dict(type='int', default=0),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           mutually_exclusive=[
                               ['name', 'uuid'],
                           ],
                           )

    result = dict(changed=False,)

    pyv = PyVmomi(module)

    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    if vm:
        # VM already exists, so set power state
        scheduled_at = module.params.get('scheduled_at', None)
        if scheduled_at:
            if not pyv.is_vcenter():
                module.fail_json(msg="Scheduling task requires vCenter, hostname %s "
                                     "is an ESXi server." % module.params.get('hostname'))
            powerstate = {
                'powered-off': vim.VirtualMachine.PowerOff,
                'powered-on': vim.VirtualMachine.PowerOn,
                'reboot-guest': vim.VirtualMachine.RebootGuest,
                'restarted': vim.VirtualMachine.Reset,
                'shutdown-guest': vim.VirtualMachine.ShutdownGuest,
                'suspended': vim.VirtualMachine.Suspend,
            }
            dt = ''
            try:
                dt = datetime.strptime(scheduled_at, '%d/%m/%Y %H:%M')
            except ValueError as e:
                module.fail_json(msg="Failed to convert given date and time string to Python datetime object,"
                                     "please specify string in 'dd/mm/yyyy hh:mm' format: %s" % to_native(e))
            schedule_task_spec = vim.scheduler.ScheduledTaskSpec()
            schedule_task_desc = 'Schedule task for vm %s for operation %s at %s' % (vm.name,
                                                                                     module.params.get('state'),
                                                                                     scheduled_at)
            schedule_task_spec.name = schedule_task_desc
            schedule_task_spec.description = schedule_task_desc
            schedule_task_spec.scheduler = vim.scheduler.OnceTaskScheduler()
            schedule_task_spec.scheduler.runAt = dt
            schedule_task_spec.action = vim.action.MethodAction()
            schedule_task_spec.action.name = powerstate[module.params.get('state')]
            schedule_task_spec.enabled = True

            try:
                pyv.content.scheduledTaskManager.CreateScheduledTask(vm, schedule_task_spec)
                # As this is async task, we create scheduled task and mark state to changed.
                module.exit_json(changed=True)
            except vim.fault.InvalidName as e:
                module.fail_json(msg="Failed to create scheduled task %s for %s : %s" % (module.params.get('state'),
                                                                                         vm.name,
                                                                                         to_native(e.msg)))
            except vim.fault.DuplicateName as e:
                module.exit_json(chanaged=False, details=to_native(e.msg))
            except vmodl.fault.InvalidArgument as e:
                module.fail_json(msg="Failed to create scheduled task %s as specifications "
                                     "given are invalid: %s" % (module.params.get('state'),
                                                                to_native(e.msg)))
        else:
            result = set_vm_power_state(pyv.content, vm, module.params['state'], module.params['force'])
    else:
        module.fail_json(msg="Unable to set power state for non-existing virtual machine : '%s'" % (module.params.get('uuid') or module.params.get('name')))

    if result.get('failed') is True:
        module.fail_json(**result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
