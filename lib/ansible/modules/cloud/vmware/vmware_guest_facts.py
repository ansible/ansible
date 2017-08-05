#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This module is also sponsored by E.T.A.I. (www.etai.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_guest_facts
short_description: Gather facts about a single VM
description:
    - Gather facts about a single VM on a VMware ESX cluster
version_added: 2.3
author:
    - Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
        description:
            - Name of the VM to work with
            - This is required if UUID is not supplied.
   name_match:
        description:
            - If multiple VMs matching the name, use the first or last found
        default: 'first'
        choices: ['first', 'last']
   uuid:
        description:
            - UUID of the instance to manage if known, this is VMware's unique identifier.
            - This is required if name is not supplied.
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
            - '   folder: vm/folder2'
            - '   folder: folder2'
        default: /vm
   datacenter:
        description:
            - Destination datacenter for the deploy operation
        required: True
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Gather VM facts
  vmware_guest_facts:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    validate_certs: no
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
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

try:
    import pyVmomi
    from pyVmomi import vim

    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from ansible.module_utils.vmware import connect_to_api, find_vm_by_id, gather_vm_facts, vmware_argument_spec


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


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        folder=dict(type='str', default='/vm'),
        datacenter=dict(type='str', required=True),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=[['name', 'uuid']])

    # FindByInventoryPath() does not require an absolute path
    # so we should leave the input folder path unmodified
    module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.getvm(name=module.params['name'],
                   folder=module.params['folder'],
                   uuid=module.params['uuid'])

    # VM already exists
    if vm:
        try:
            module.exit_json(instance=pyv.gather_facts(vm))
        except Exception as exc:
            module.fail_json(msg="Fact gather failed with exception %s" % to_text(exc))
    else:
        msg = "Unable to gather facts for non-existing VM "
        if module.params['name']:
            msg += "%(name)s" % module.params
        elif module.params['uuid']:
            msg += "%(uuid)s" % module.params
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
