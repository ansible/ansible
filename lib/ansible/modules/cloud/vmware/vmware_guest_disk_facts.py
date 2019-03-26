#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, NAER William Leemans (@bushvin) <willie@elaba.net>
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
module: vmware_guest_disk_facts
short_description: Gather facts about disks of given virtual machine
description:
    - This module can be used to gather facts about disks belonging to given virtual machine.
    - All parameters and VMware object names are case sensitive.
version_added: 2.6
author:
    - Abhijeet Kasurde (@Akasurde) <akasurde@redhat.com>
notes:
    - Tested on vSphere 6.0 and 6.5.
    - Disk UUID information is added in version 2.8.
    - Additional information about guest disk backings added in version 2.8.
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
     description:
     - Name of the virtual machine.
     - This is required parameter, if parameter C(uuid) is not supplied.
   uuid:
     description:
     - UUID of the instance to gather facts if known, this is VMware's unique identifier.
     - This is required parameter, if parameter C(name) is not supplied.
   use_instance_uuid:
     description:
     - Whether to use the VMWare instance UUID rather than the BIOS UUID.
     default: no
     type: bool
     version_added: '2.8'
   folder:
     description:
     - Destination folder, absolute or relative path to find an existing guest.
     - This is required parameter, only if multiple VMs are found with same name.
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
   datacenter:
     description:
     - The datacenter name to which virtual machine belongs to.
     required: True
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Gather disk facts from virtual machine using UUID
  vmware_guest_disk_facts:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: ha-datacenter
    validate_certs: no
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
  delegate_to: localhost
  register: disk_facts

- name: Gather disk facts from virtual machine using name
  vmware_guest_disk_facts:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: ha-datacenter
    validate_certs: no
    name: VM_225
  delegate_to: localhost
  register: disk_facts
'''

RETURN = """
guest_disk_facts:
    description: metadata about the virtual machine's disks
    returned: always
    type: dict
    sample: {
        "0": {
            "backing_datastore": "datastore2",
            "backing_disk_mode": "persistent",
            "backing_eagerlyscrub": false,
            "backing_filename": "[datastore2] VM_225/VM_225.vmdk",
            "backing_thinprovisioned": false,
            "backing_type": "FlatVer2",
            "backing_writethrough": false,
            "backing_uuid": "200C3A00-f82a-97af-02ff-62a595f0020a",
            "capacity_in_bytes": 10485760,
            "capacity_in_kb": 10240,
            "controller_key": 1000,
            "key": 2000,
            "label": "Hard disk 1",
            "summary": "10,240 KB",
            "unit_number": 0
        },
        "1": {
            "backing_datastore": "datastore3",
            "backing_devicename": "vml.012345678901234567890123456789012345678901234567890123",
            "backing_disk_mode": "independent_persistent",
            "backing_filename": "[datastore3] VM_226/VM_226.vmdk",
            "backing_lunuuid": "012345678901234567890123456789012345678901234567890123",
            "backing_type": "RawDiskMappingVer1",
            "backing_uuid": null,
            "capacity_in_bytes": 15728640,
            "capacity_in_kb": 15360,
            "controller_key": 1000,
            "key": 2001,
            "label": "Hard disk 3",
            "summary": "15,360 KB",
            "unit_number": 1
        },
    }
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)

    def gather_disk_facts(self, vm_obj):
        """
        Gather facts about VM's disks
        Args:
            vm_obj: Managed object of virtual machine

        Returns: A list of dict containing disks information

        """
        disks_facts = dict()
        if vm_obj is None:
            return disks_facts

        disk_index = 0
        for disk in vm_obj.config.hardware.device:
            if isinstance(disk, vim.vm.device.VirtualDisk):
                disks_facts[disk_index] = dict(
                    key=disk.key,
                    label=disk.deviceInfo.label,
                    summary=disk.deviceInfo.summary,
                    backing_filename=disk.backing.fileName,
                    backing_datastore=disk.backing.datastore.name,
                    controller_key=disk.controllerKey,
                    unit_number=disk.unitNumber,
                    capacity_in_kb=disk.capacityInKB,
                    capacity_in_bytes=disk.capacityInBytes,
                )
                if isinstance(disk.backing, vim.vm.device.VirtualDisk.FlatVer1BackingInfo):
                    disks_facts[disk_index]['backing_type'] = 'FlatVer1'
                    disks_facts[disk_index]['backing_writethrough'] = disk.backing.writeThrough

                elif isinstance(disk.backing, vim.vm.device.VirtualDisk.FlatVer2BackingInfo):
                    disks_facts[disk_index]['backing_type'] = 'FlatVer2'
                    disks_facts[disk_index]['backing_writethrough'] = bool(disk.backing.writeThrough)
                    disks_facts[disk_index]['backing_thinprovisioned'] = bool(disk.backing.thinProvisioned)
                    disks_facts[disk_index]['backing_eagerlyscrub'] = bool(disk.backing.eagerlyScrub)
                    disks_facts[disk_index]['backing_uuid'] = disk.backing.uuid

                elif isinstance(disk.backing, vim.vm.device.VirtualDisk.LocalPMemBackingInfo):
                    disks_facts[disk_index]['backing_type'] = 'LocalPMem'
                    disks_facts[disk_index]['backing_volumeuuid'] = disk.backing.volumeUUID
                    disks_facts[disk_index]['backing_uuid'] = disk.backing.uuid

                elif isinstance(disk.backing, vim.vm.device.VirtualDisk.PartitionedRawDiskVer2BackingInfo):
                    disks_facts[disk_index]['backing_type'] = 'PartitionedRawDiskVer2'
                    disks_facts[disk_index]['backing_descriptorfilename'] = disk.backing.descriptorFileName
                    disks_facts[disk_index]['backing_uuid'] = disk.backing.uuid

                elif isinstance(disk.backing, vim.vm.device.VirtualDisk.RawDiskMappingVer1BackingInfo):
                    disks_facts[disk_index]['backing_type'] = 'RawDiskMappingVer1'
                    disks_facts[disk_index]['backing_devicename'] = disk.backing.deviceName
                    disks_facts[disk_index]['backing_diskmode'] = disk.backing.diskMode
                    disks_facts[disk_index]['backing_lunuuid'] = disk.backing.lunUuid
                    disks_facts[disk_index]['backing_uuid'] = disk.backing.uuid

                elif isinstance(disk.backing, vim.vm.device.VirtualDisk.RawDiskVer2BackingInfo):
                    disks_facts[disk_index]['backing_type'] = 'RawDiskVer2'
                    disks_facts[disk_index]['backing_descriptorfilename'] = disk.backing.descriptorFileName
                    disks_facts[disk_index]['backing_uuid'] = disk.backing.uuid

                elif isinstance(disk.backing, vim.vm.device.VirtualDisk.SeSparseBackingInfo):
                    disks_facts[disk_index]['backing_type'] = 'SeSparse'
                    disks_facts[disk_index]['backing_diskmode'] = disk.backing.diskMode
                    disks_facts[disk_index]['backing_writethrough'] = bool(disk.backing.writeThrough)
                    disks_facts[disk_index]['backing_uuid'] = disk.backing.uuid

                elif isinstance(disk.backing, vim.vm.device.VirtualDisk.SparseVer1BackingInfo):
                    disks_facts[disk_index]['backing_type'] = 'SparseVer1'
                    disks_facts[disk_index]['backing_diskmode'] = disk.backing.diskMode
                    disks_facts[disk_index]['backing_spaceusedinkb'] = disk.backing.spaceUsedInKB
                    disks_facts[disk_index]['backing_split'] = bool(disk.backing.split)
                    disks_facts[disk_index]['backing_writethrough'] = bool(disk.backing.writeThrough)

                elif isinstance(disk.backing, vim.vm.device.VirtualDisk.SparseVer2BackingInfo):
                    disks_facts[disk_index]['backing_type'] = 'SparseVer2'
                    disks_facts[disk_index]['backing_diskmode'] = disk.backing.diskMode
                    disks_facts[disk_index]['backing_spaceusedinkb'] = disk.backing.spaceUsedInKB
                    disks_facts[disk_index]['backing_split'] = bool(disk.backing.split)
                    disks_facts[disk_index]['backing_writethrough'] = bool(disk.backing.writeThrough)
                    disks_facts[disk_index]['backing_uuid'] = disk.backing.uuid
                disk_index += 1
        return disks_facts


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        folder=dict(type='str'),
        datacenter=dict(type='str', required=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[['name', 'uuid']],
        supports_check_mode=True,
    )

    if module.params['folder']:
        # FindByInventoryPath() does not require an absolute path
        # so we should leave the input folder path unmodified
        module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    if vm:
        # VM exists
        try:
            module.exit_json(guest_disk_facts=pyv.gather_disk_facts(vm))
        except Exception as exc:
            module.fail_json(msg="Failed to gather facts with exception : %s" % to_text(exc))
    else:
        # We unable to find the virtual machine user specified
        # Bail out
        module.fail_json(msg="Unable to gather disk facts for non-existing VM %s" % (module.params.get('uuid') or module.params.get('name')))


if __name__ == '__main__':
    main()
