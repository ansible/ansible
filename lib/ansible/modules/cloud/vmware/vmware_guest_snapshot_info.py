#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_guest_snapshot_info
short_description: Gather info about virtual machine's snapshots in vCenter
description:
    - This module can be used to gather information about virtual machine's snapshots.
    - This module was called C(vmware_guest_snapshot_facts) before Ansible 2.9. The usage did not change.
version_added: 2.6
author:
    - Abhijeet Kasurde (@Akasurde)
notes:
    - Tested on vSphere 6.0 and 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
     description:
     - Name of the VM to work with.
     - This is required if C(uuid) or C(moid) is not supplied.
     type: str
   uuid:
     description:
     - UUID of the instance to manage if known, this is VMware's BIOS UUID by default.
     - This is required if C(name) or C(moid) parameter is not supplied.
     - The C(folder) is ignored, if C(uuid) is provided.
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
   folder:
     description:
     - Destination folder, absolute or relative path to find an existing guest.
     - This is required only, if multiple virtual machines with same name are found on given vCenter.
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
     type: str
   datacenter:
     description:
     - Name of the datacenter.
     required: True
     type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Gather snapshot information about the virtual machine in the given vCenter
  vmware_guest_snapshot_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    name: "{{ guest_name }}"
  delegate_to: localhost
  register: snapshot_info

- name: Gather snapshot information about the virtual machine using MoID
  vmware_guest_snapshot_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    moid: vm-42
  delegate_to: localhost
  register: snapshot_info
'''

RETURN = """
guest_snapshots:
    description: metadata about the snapshot information
    returned: always
    type: dict
    sample: {
        "current_snapshot": {
            "creation_time": "2018-02-10T14:48:31.999459+00:00",
            "description": "",
            "id": 28,
            "name": "snap_0003",
            "state": "poweredOff"
        },
        "snapshots": [
            {
                "creation_time": "2018-02-10T14:48:31.999459+00:00",
                "description": "",
                "id": 28,
                "name": "snap_0003",
                "state": "poweredOff"
            }
        ]
    }
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, list_snapshots, vmware_argument_spec


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)

    @staticmethod
    def gather_guest_snapshot_info(vm_obj=None):
        """
        Return snapshot related information about given virtual machine
        Args:
            vm_obj: Virtual Machine Managed object

        Returns: Dictionary containing snapshot information

        """
        if vm_obj is None:
            return {}
        return list_snapshots(vm=vm_obj)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        folder=dict(type='str'),
        datacenter=dict(required=True, type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=[
            ['name', 'folder']
        ],
        required_one_of=[
            ['name', 'uuid', 'moid']
        ],
        supports_check_mode=True,
    )
    if module._name == 'vmware_guest_snapshot_facts':
        module.deprecate("The 'vmware_guest_snapshot_facts' module has been renamed to 'vmware_guest_snapshot_info'", version='2.13')

    if module.params['folder']:
        # FindByInventoryPath() does not require an absolute path
        # so we should leave the input folder path unmodified
        module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    if not vm:
        # If UUID is set, get_vm select UUID, show error message accordingly.
        vm_id = (module.params.get('uuid') or module.params.get('name') or module.params.get('moid'))
        module.fail_json(msg="Unable to gather information about snapshots for"
                             " non-existing VM ['%s']" % vm_id)

    results = dict(changed=False, guest_snapshots=pyv.gather_guest_snapshot_info(vm_obj=vm))
    module.exit_json(**results)


if __name__ == '__main__':
    main()
