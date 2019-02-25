#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This module is also sponsored by E.T.A.I. (www.etai.fr)
# Copyright (C) 2018 James E. King III (@jeking3) <jking@apache.org>
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
module: vmware_guest_facts
short_description: Gather facts about a single VM
description:
    - Gather facts about a single VM on a VMware ESX cluster.
version_added: 2.3
author:
    - Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
notes:
    - Tested on vSphere 5.5, 6.7
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
   use_instance_uuid:
     description:
     - Whether to use the VMWare instance UUID rather than the BIOS UUID.
     default: no
     type: bool
     version_added: '2.8'
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
   datacenter:
     description:
     - Destination datacenter for the deploy operation
     required: True
   tags:
     description:
     - Whether to show tags or not.
     - If set C(True), shows tag facts.
     - If set C(False), hides tags facts.
     - vSphere Automation SDK and vCloud Suite SDK is required.
     default: 'no'
     type: bool
     version_added: '2.8'
   schema:
     description:
     - Specify the output schema desired.
     - The 'summary' output schema is the legacy output from the module
     - The 'vsphere' output schema is the vSphere API class definition
       which requires pyvmomi>6.7.1
     choices: ['summary', 'vsphere']
     default: 'summary'
     type: str
     version_added: '2.8'
   properties:
     description:
     - Specify the properties to retrieve.
     - If not specified, all properties are retrieved (deeply).
     - Results are returned in a structure identical to the vsphere API.
     - 'Example:'
     - '   properties: ['
     - '      "config.hardware.memoryMB",'
     - '      "config.hardware.numCPU",'
     - '      "guest.disk",'
     - '      "overallStatus"'
     - '   ]'
     - Only valid when C(schema) is C(vsphere).
     type: list
     required: False
     version_added: '2.8'
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Gather facts from standalone ESXi server having datacenter as 'ha-datacenter'
  vmware_guest_facts:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: ha-datacenter
    validate_certs: no
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
  delegate_to: localhost
  register: facts

- name: Gather some facts from a guest using the vSphere API output schema
  vmware_guest_facts:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter: "{{ datacenter_name }}"
    name: "{{ vm_name }}"
    schema: "vsphere"
    properties: ["config.hardware.memoryMB", "guest.disk", "overallStatus"]
  delegate_to: localhost
  register: facts
'''

RETURN = """
instance:
    description: metadata about the virtual machine
    returned: always
    type: dict
    sample: {
        "annotation": "",
        "current_snapshot": null,
        "customvalues": {},
        "guest_consolidation_needed": false,
        "guest_question": null,
        "guest_tools_status": "guestToolsNotRunning",
        "guest_tools_version": "10247",
        "hw_cores_per_socket": 1,
        "hw_datastores": [
            "ds_226_3"
        ],
        "hw_esxi_host": "10.76.33.226",
        "hw_eth0": {
            "addresstype": "assigned",
            "ipaddresses": null,
            "label": "Network adapter 1",
            "macaddress": "00:50:56:87:a5:9a",
            "macaddress_dash": "00-50-56-87-a5-9a",
            "portgroup_key": null,
            "portgroup_portkey": null,
            "summary": "VM Network"
        },
        "hw_files": [
            "[ds_226_3] ubuntu_t/ubuntu_t.vmx",
            "[ds_226_3] ubuntu_t/ubuntu_t.nvram",
            "[ds_226_3] ubuntu_t/ubuntu_t.vmsd",
            "[ds_226_3] ubuntu_t/vmware.log",
            "[ds_226_3] u0001/u0001.vmdk"
        ],
        "hw_folder": "/DC0/vm/Discovered virtual machine",
        "hw_guest_full_name": null,
        "hw_guest_ha_state": null,
        "hw_guest_id": null,
        "hw_interfaces": [
            "eth0"
        ],
        "hw_is_template": false,
        "hw_memtotal_mb": 1024,
        "hw_name": "ubuntu_t",
        "hw_power_status": "poweredOff",
        "hw_processor_count": 1,
        "hw_product_uuid": "4207072c-edd8-3bd5-64dc-903fd3a0db04",
        "hw_version": "vmx-13",
        "instance_uuid": "5007769d-add3-1e12-f1fe-225ae2a07caf",
        "ipv4": null,
        "ipv6": null,
        "module_hw": true,
        "snapshots": [],
        "tags": [
            "backup"
        ],
        "vnc": {}
    }
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils.vmware_rest_client import VmwareRestClient
try:
    from com.vmware.vapi.std_client import DynamicID
    from com.vmware.cis.tagging_client import Tag, TagAssociation
    HAS_VCLOUD = True
except ImportError:
    HAS_VCLOUD = False


class VmwareTag(VmwareRestClient):
    def __init__(self, module):
        super(VmwareTag, self).__init__(module)
        self.tag_service = Tag(self.connect)
        self.tag_association_svc = TagAssociation(self.connect)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        folder=dict(type='str'),
        datacenter=dict(type='str', required=True),
        tags=dict(type='bool', default=False),
        schema=dict(type='str', choices=['summary', 'vsphere'], default='summary'),
        properties=dict(type='list')
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=[['name', 'uuid']])

    if module.params.get('folder'):
        # FindByInventoryPath() does not require an absolute path
        # so we should leave the input folder path unmodified
        module.params['folder'] = module.params['folder'].rstrip('/')

    if module.params['schema'] != 'vsphere' and module.params.get('properties'):
        module.fail_json(msg="The option 'properties' is only valid when the schema is 'vsphere'")

    pyv = PyVmomi(module)
    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    # VM already exists
    if vm:
        try:
            if module.params['schema'] == 'summary':
                instance = pyv.gather_facts(vm)
            else:
                instance = pyv.to_json(vm, module.params['properties'])

            if module.params.get('tags'):
                if not HAS_VCLOUD:
                    module.fail_json(msg="Unable to find 'vCloud Suite SDK' Python library which is required."
                                         " Please refer this URL for installation steps"
                                         " - https://code.vmware.com/web/sdk/60/vcloudsuite-python")

                vm_rest_client = VmwareTag(module)
                instance.update(
                    tags=vm_rest_client.get_vm_tags(vm_rest_client.tag_service,
                                                    vm_rest_client.tag_association_svc,
                                                    vm_mid=vm._moId)
                )
            module.exit_json(instance=instance)
        except Exception as exc:
            module.fail_json(msg="Fact gather failed with exception %s" % to_text(exc))
    else:
        module.fail_json(msg="Unable to gather facts for non-existing VM %s" % (module.params.get('uuid') or
                                                                                module.params.get('name')))


if __name__ == '__main__':
    main()
