#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Philippe Dellaert <philippe@dellaert.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_guest_tools_wait
short_description: Wait for VMware tools to become available
description:
    - This module can be used to wait for VMware tools to become available on the given VM and return facts.
version_added: '2.4'
author:
    - Philippe Dellaert (@pdellaert) <philippe@dellaert.org>
notes:
    - Tested on vSphere 6.5
requirements:
    - python >= 2.6
    - PyVmomi
options:
   name:
     description:
     - Name of the VM for which to wait until the tools become available.
     - This is required if C(uuid) or C(moid) is not supplied.
     type: str
   name_match:
     description:
     - If multiple VMs match the name, use the first or last found.
     default: 'first'
     choices: ['first', 'last']
     type: str
   folder:
     description:
     - Destination folder, absolute or relative path to find an existing guest.
     - This is required only, if multiple VMs with same C(name) is found.
     - The folder should include the datacenter. ESX's datacenter is C(ha-datacenter).
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
     type: str
   uuid:
     description:
     - UUID of the VM  for which to wait until the tools become available, if known. This is VMware's unique identifier.
     - This is required, if C(name) or C(moid) is not supplied.
     type: str
   moid:
     description:
     - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
     - This is required if C(name) or C(uuid) is not supplied.
     version_added: '2.9'
     type: str
   use_instance_uuid:
     description:
     - Whether to use the VMware instance UUID rather than the BIOS UUID.
     default: no
     type: bool
     version_added: '2.8'
   timeout:
     description:
     - Max duration of the waiting period (seconds).
     default: 500
     type: int
     version_added: '2.10'
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Wait for VMware tools to become available by UUID
  vmware_guest_facts:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter: "{{ datacenter }}"
    folder: "/{{datacenter}}/vm"
    name: "{{ vm_name }}"
  delegate_to: localhost
  register: vm_facts

- name: Get UUID from previous task and pass it to this task
  vmware_guest_tools_wait:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    uuid: "{{ vm_facts.instance.hw_product_uuid }}"
  delegate_to: localhost
  register: facts


- name: Wait for VMware tools to become available by MoID
  vmware_guest_tools_wait:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    moid: vm-42
  delegate_to: localhost
  register: facts

- name: Wait for VMware tools to become available by name
  vmware_guest_tools_wait:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    name: test-vm
    folder: "/{{datacenter}}/vm"
  delegate_to: localhost
  register: facts
'''

RETURN = """
instance:
    description: metadata about the virtual machine
    returned: always
    type: dict
    sample: None
"""

import datetime
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import PyVmomi, gather_vm_facts, vmware_argument_spec


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)

    def gather_facts(self, vm):
        return gather_vm_facts(self.content, vm)

    def wait_for_tools(self, vm, timeout):
        tools_running = False
        vm_facts = {}
        start_at = datetime.datetime.now()

        while start_at + timeout > datetime.datetime.now():
            newvm = self.get_vm()
            vm_facts = self.gather_facts(newvm)
            if vm_facts['guest_tools_status'] == 'guestToolsRunning':
                return {'changed': True, 'failed': False, 'instance': vm_facts}
            time.sleep(5)

        if not tools_running:
            return {'failed': True, 'msg': 'VMware tools either not present or not running after {0} seconds'.format(timeout.total_seconds())}


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        name_match=dict(type='str', default='first', choices=['first', 'last']),
        folder=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        timeout=dict(type='int', default=500),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['name', 'uuid', 'moid']
        ]
    )

    if module.params['folder']:
        # FindByInventoryPath() does not require an absolute path
        # so we should leave the input folder path unmodified
        module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    if not vm:
        vm_id = module.params.get('name') or module.params.get('uuid') or module.params.get('moid')
        module.fail_json(msg="Unable to wait for VMware tools for non-existing VM '%s'." % vm_id)

    timeout = datetime.timedelta(seconds=module.params['timeout'])

    result = dict(changed=False)
    try:
        result = pyv.wait_for_tools(vm, timeout)
    except Exception as e:
        module.fail_json(msg="Waiting for VMware tools failed with"
                             " exception: {0:s}".format(to_native(e)))

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
