#!/usr/bin/python
# -*- coding: utf-8 -*-
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_guest_tools_wait
short_description: Wait for VMware tools to become available and return facts
description:
    - Wait for VMware tools to become available on the VM and return facts
version_added: 2.4
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
            - Name of the VM for which to wait until the tools become available
            - This is required if uuid is not supplied.
   name_match:
        description:
            - If multiple VMs matching the name, use the first or last found
        default: 'first'
        choices: ['first', 'last']
   folder:
        description:
            - Destination folder, absolute or relative path to find an existing guest.
            - This is required if name is supplied.
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
        default: /vm
   uuid:
        description:
            - UUID of the VM  for which to wait until the tools become available, if known. This is VMware's unique identifier.
            - This is required if name is not supplied.
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

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import connect_to_api, gather_vm_facts, vmware_argument_spec, find_vm_by_id

try:
    import json
except ImportError:
    import simplejson as json

HAS_PYVMOMI = False
try:
    import pyVmomi
    from pyVmomi import vim

    HAS_PYVMOMI = True
except ImportError:
    pass


class PyVmomiHelper(object):
    def __init__(self, module):
        if not HAS_PYVMOMI:
            module.fail_json(msg='pyvmomi module required')

        self.module = module
        self.params = module.params
        self.content = connect_to_api(self.module)

    def getvm(self, name=None, uuid=None, folder=None):
        vm = None
        match_first = False
        if uuid:
            vm = find_vm_by_id(self.content, vm_id=uuid, vm_id_type="uuid")
        elif folder and name:
            if self.params['name_match'] == 'first':
                match_first = True
            vm = find_vm_by_id(self.content, vm_id=name, vm_id_type="inventory_path", folder=folder, match_first=match_first)
        return vm

    def gather_facts(self, vm):
        return gather_vm_facts(self.content, vm)

    def wait_for_tools(self, vm, poll=100, sleep=5):
        tools_running = False
        vm_facts = {}
        poll_num = 0
        vm_uuid = vm.config.uuid
        while not tools_running and poll_num <= poll:
            newvm = self.getvm(uuid=vm_uuid)
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
        name_match=dict(type='str', default='first'),
        folder=dict(type='str', default='/vm'),
        uuid=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[['name', 'uuid']],
        required_together=['name', 'folder']
    )

    # FindByInventoryPath() does not require an absolute path
    # so we should leave the input folder path unmodified
    module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.getvm(name=module.params['name'],
                   folder=module.params['folder'],
                   uuid=module.params['uuid'])

    # VM exists
    if vm:
        try:
            result = pyv.wait_for_tools(vm)
            if result['failed']:
                module.fail_json(**result)
            else:
                module.exit_json(**result)
        except Exception as exc:
            module.fail_json(msg="Waiting for tools failed with exception: %s" % to_native(exc))
    else:
        msg = "Unable to wait for tools for non-existing VM "
        if module.params['name']:
            msg += "%(name)s" % module.params
        elif module.params['uuid']:
            msg += "%(uuid)s" % module.params
        module.fail_json(msg=msg)

if __name__ == '__main__':
    main()
