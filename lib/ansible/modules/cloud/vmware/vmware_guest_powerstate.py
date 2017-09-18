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
- Abhijeet Kasurde (@akasurde) <akasurde@redhat.com>
requirements:
- python >= 2.6
- PyVmomi
options:
  state:
    description:
    - Set the state of the virtual machine.
    choices: [ powered-off, powered-on, reboot-guest, restarted, shutdown-guest, suspended ]
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
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, set_vm_power_state, vmware_argument_spec


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present',
                   choices=['powered-off', 'powered-on', 'reboot-guest', 'restarted', 'shutdown-guest', 'suspended']),
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        folder=dict(type='str', default='/vm'),
        force=dict(type='bool', default=False),
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
        result = set_vm_power_state(pyv.content, vm, module.params['state'], module.params['force'])
    else:
        module.fail_json(msg="Unable to set power state for non-existing virtual machine : '%s'" % (module.params.get('uuid') or module.params.get('name')))

    if result.get('failed') is True:
        module.fail_json(**result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
