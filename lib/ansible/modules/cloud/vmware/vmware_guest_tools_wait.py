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
     - This is required if uuid is not supplied.
   name_match:
     description:
     - If multiple VMs match the name, use the first or last found.
     default: 'first'
     choices: ['first', 'last']
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
   uuid:
     description:
     - UUID of the VM  for which to wait until the tools become available, if known. This is VMware's unique identifier.
     - This is required, if C(name) is not supplied.
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Wait for VMware tools to become available by UUID
  vmware_guest_tools_wait:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    validate_certs: no
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
  delegate_to: localhost
  register: facts

- name: Wait for VMware tools to become available by name
  vmware_guest_tools_wait:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    validate_certs: no
    name: test-vm
    folder: /datacenter1/vm
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

import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import PyVmomi, gather_vm_facts, vmware_argument_spec


try:
    import pyVmomi
    from pyVmomi import vim
except ImportError:
    pass


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)

    def gather_facts(self, vm):
        return gather_vm_facts(self.content, vm)

    def wait_for_tools(self, vm, poll=100, sleep=5):
        tools_running = False
        vm_facts = {}
        poll_num = 0
        while not tools_running and poll_num <= poll:
            newvm = self.get_vm()
            vm_facts = self.gather_facts(newvm)
            if vm_facts['guest_tools_status'] == 'guestToolsRunning':
                tools_running = True
            else:
                time.sleep(sleep)
                poll_num += 1

        if not tools_running:
            return {'failed': True, 'msg': 'VMware tools either not present or not running after {0} seconds'.format((poll * sleep))}

        changed = False
        if poll_num > 0:
            changed = True
        return {'changed': changed, 'failed': False, 'instance': vm_facts}


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        name_match=dict(type='str', default='first', choices=['first', 'last']),
        folder=dict(type='str'),
        uuid=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[['name', 'uuid']])

    if module.params['folder']:
        # FindByInventoryPath() does not require an absolute path
        # so we should leave the input folder path unmodified
        module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    if not vm:
        module.fail_json(msg="Unable to wait for VMware tools for "
                             "non-existing VM '%s'." % (module.params.get('name') or
                                                        module.params.get('uuid')))

    result = dict(changed=False)
    try:
        result = pyv.wait_for_tools(vm)
    except Exception as e:
        module.fail_json(msg="Waiting for VMware tools failed with"
                             " exception: {0:s}".format(to_native(e)))

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
