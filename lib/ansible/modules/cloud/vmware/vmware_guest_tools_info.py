#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# Copyright: (c) 2019, VMware, Inc. All Rights Reserved.
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
module: vmware_guest_tools_info
short_description: Gather info about VMware tools installed in VM
description:
    - Gather information about the VMware tools installed in virtual machine.
version_added: '2.10'
author:
    - Diane Wang (@Tomorrow9) <dianew@vmware.com>
notes:
    - Tested on vSphere 6.0, 6.5, 6.7
requirements:
    - "python >= 2.7"
    - PyVmomi
options:
   name:
     description:
     - Name of the VM to get VMware tools info.
     - This is required if C(uuid) or C(moid) is not supplied.
     type: str
   name_match:
     description:
     - If multiple VMs matching the name, use the first or last found.
     default: 'first'
     choices: ['first', 'last']
     type: str
   uuid:
     description:
     - UUID of the instance to manage if known, this is VMware's unique identifier.
     - This is required if C(name) or C(moid) is not supplied.
     type: str
   use_instance_uuid:
     description:
     - Whether to use the VMware instance UUID rather than the BIOS UUID.
     default: no
     type: bool
   moid:
     description:
     - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
     - This is required if C(name) or C(uuid) is not supplied.
     type: str
   folder:
     description:
     - Destination folder, absolute or relative path to find an existing guest.
     - This is required if name is supplied.
     - The folder should include the datacenter. ESXi server's datacenter is ha-datacenter.
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
     - The datacenter name to which virtual machine belongs to.
     type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Gather VMware tools info installed in VM specified by uuid
  vmware_guest_tools_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
  delegate_to: localhost
  register: vmtools_info

- name: Gather VMware tools info installed in VM specified by name
  vmware_guest_tools_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    name: "{{ vm_name }}"
  delegate_to: localhost
  register: vmtools_info
'''

RETURN = """
vmtools_info:
    description: metadata about the VMware tools installed in virtual machine
    returned: always
    type: dict
    sample: {
        "vm_uuid": null,
        "vm_moid": null,
        "vm_use_instance_uuid": false,
        "vm_guest_fullname": "Microsoft Windows 10 (64-bit)",
        "vm_guest_hostname": "test",
        "vm_guest_id": "windows9_64Guest",
        "vm_hw_version": "vmx-14",
        "vm_ipaddress": "10.10.10.10",
        "vm_name": "test_vm",
        "vm_tools_install_status": "toolsOk",
        "vm_tools_install_type": "guestToolsTypeMSI",
        "vm_tools_last_install_count": 0,
        "vm_tools_running_status": "guestToolsRunning",
        "vm_tools_upgrade_policy": "manual",
        "vm_tools_version": 10341,
        "vm_tools_version_status": "guestToolsCurrent"
    }
"""


try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.name = self.params['name']
        self.uuid = self.params['uuid']
        self.moid = self.params['moid']
        self.use_instance_uuid = self.params['use_instance_uuid']

    def gather_vmtools_info(self):
        vmtools_info = dict(
            vm_name=self.name,
            vm_uuid=self.uuid,
            vm_moid=self.moid,
            vm_use_instance_uuid=self.use_instance_uuid,
            vm_hw_version=self.current_vm_obj.config.version,
            vm_guest_id=self.current_vm_obj.summary.guest.guestId,
            vm_guest_fullname=self.current_vm_obj.summary.guest.guestFullName,
            vm_guest_hostname=self.current_vm_obj.summary.guest.hostName,
            vm_ipaddress=self.current_vm_obj.summary.guest.ipAddress,
            vm_tools_running_status=self.current_vm_obj.summary.guest.toolsRunningStatus,
            vm_tools_install_status=self.current_vm_obj.summary.guest.toolsStatus,
            vm_tools_version_status=self.current_vm_obj.summary.guest.toolsVersionStatus,
            vm_tools_install_type=self.current_vm_obj.config.tools.toolsInstallType,
            vm_tools_version=self.current_vm_obj.config.tools.toolsVersion,
            vm_tools_upgrade_policy=self.current_vm_obj.config.tools.toolsUpgradePolicy,
            vm_tools_last_install_count=self.current_vm_obj.config.tools.lastInstallInfo.counter,
        )

        return {'changed': False, 'failed': False, 'vmtools_info': vmtools_info}


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        name_match=dict(
            choices=['first', 'last'],
            default='first',
            type='str'
        ),
        folder=dict(type='str'),
        datacenter=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['name', 'uuid', 'moid']
        ],
        mutually_exclusive=[
            ['name', 'uuid', 'moid']
        ],
        supports_check_mode=True,
    )

    pyv = PyVmomiHelper(module)
    vm = pyv.get_vm()
    if not vm:
        vm_id = (module.params.get('uuid') or module.params.get('name') or module.params.get('moid'))
        module.fail_json(msg='Unable to find the specified virtual machine using: %s' % vm_id)
    results = pyv.gather_vmtools_info()
    module.exit_json(**results)


if __name__ == '__main__':
    main()
