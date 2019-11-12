#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: xenserver_guest_facts
short_description: Gathers facts for virtual machines running on Citrix Hypervisor/XenServer host or pool
description: >
   This module can be used to gather essential VM facts.
version_added: '2.8'
author:
- Bojan Vitnik (@bvitnik) <bvitnik@mainstream.rs>
notes:
- Minimal supported version of XenServer is 5.6.
- Module was tested with XenServer 6.5, 7.1, 7.2, 7.6, Citrix Hypervisor 8.0, XCP-ng 7.6 and 8.0.
- 'To acquire XenAPI Python library, just run C(pip install XenAPI) on your Ansible Control Node. The library can also be found inside
   Citrix Hypervisor/XenServer SDK (downloadable from Citrix website). Copy the XenAPI.py file from the SDK to your Python site-packages on your
   Ansible Control Node to use it. Latest version of the library can also be acquired from GitHub:
   https://raw.githubusercontent.com/xapi-project/xen-api/master/scripts/examples/python/XenAPI.py'
- 'If no scheme is specified in C(hostname), module defaults to C(http://) because C(https://) is problematic in most setups. Make sure you are
   accessing XenServer host in trusted environment or use C(https://) scheme explicitly.'
- 'To use C(https://) scheme for C(hostname) you have to either import host certificate to your OS certificate store or use C(validate_certs: no)
   which requires XenAPI library from XenServer 7.2 SDK or newer and Python 2.7.9 or newer.'
requirements:
- python >= 2.6
- XenAPI
options:
  name:
    description:
    - Name of the VM to gather facts from.
    - VMs running on XenServer do not necessarily have unique names. The module will fail if multiple VMs with same name are found.
    - In case of multiple VMs with same name, use C(uuid) to uniquely specify VM to manage.
    - This parameter is case sensitive.
    type: str
    required: yes
    aliases: [ name_label ]
  uuid:
    description:
    - UUID of the VM to gather fact of. This is XenServer's unique identifier.
    - It is required if name is not unique.
    type: str
extends_documentation_fragment: xenserver.documentation
'''

EXAMPLES = r'''
- name: Gather facts
  xenserver_guest_facts:
    hostname: "{{ xenserver_hostname }}"
    username: "{{ xenserver_username }}"
    password: "{{ xenserver_password }}"
    name: testvm_11
  delegate_to: localhost
  register: facts
'''

RETURN = r'''
instance:
    description: Metadata about the VM
    returned: always
    type: dict
    sample: {
        "cdrom": {
            "type": "none"
        },
        "customization_agent": "native",
        "disks": [
            {
                "name": "testvm_11-0",
                "name_desc": "",
                "os_device": "xvda",
                "size": 42949672960,
                "sr": "Local storage",
                "sr_uuid": "0af1245e-bdb0-ba33-1446-57a962ec4075",
                "vbd_userdevice": "0"
            },
            {
                "name": "testvm_11-1",
                "name_desc": "",
                "os_device": "xvdb",
                "size": 42949672960,
                "sr": "Local storage",
                "sr_uuid": "0af1245e-bdb0-ba33-1446-57a962ec4075",
                "vbd_userdevice": "1"
            }
        ],
        "domid": "56",
        "folder": "",
        "hardware": {
            "memory_mb": 8192,
            "num_cpu_cores_per_socket": 2,
            "num_cpus": 4
        },
        "home_server": "",
        "is_template": false,
        "name": "testvm_11",
        "name_desc": "",
        "networks": [
            {
                "gateway": "192.168.0.254",
                "gateway6": "fc00::fffe",
                "ip": "192.168.0.200",
                "ip6": [
                    "fe80:0000:0000:0000:e9cb:625a:32c5:c291",
                    "fc00:0000:0000:0000:0000:0000:0000:0001"
                ],
                "mac": "ba:91:3a:48:20:76",
                "mtu": "1500",
                "name": "Pool-wide network associated with eth1",
                "netmask": "255.255.255.128",
                "prefix": "25",
                "prefix6": "64",
                "vif_device": "0"
            }
        ],
        "other_config": {
            "base_template_name": "Windows Server 2016 (64-bit)",
            "import_task": "OpaqueRef:e43eb71c-45d6-5351-09ff-96e4fb7d0fa5",
            "install-methods": "cdrom",
            "instant": "true",
            "mac_seed": "f83e8d8a-cfdc-b105-b054-ef5cb416b77e"
        },
        "platform": {
            "acpi": "1",
            "apic": "true",
            "cores-per-socket": "2",
            "device_id": "0002",
            "hpet": "true",
            "nx": "true",
            "pae": "true",
            "timeoffset": "-25200",
            "vga": "std",
            "videoram": "8",
            "viridian": "true",
            "viridian_reference_tsc": "true",
            "viridian_time_ref_count": "true"
        },
        "state": "poweredon",
        "uuid": "e3c0b2d5-5f05-424e-479c-d3df8b3e7cda",
        "xenstore_data": {
            "vm-data": ""
        }
    }
'''

HAS_XENAPI = False
try:
    import XenAPI
    HAS_XENAPI = True
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.xenserver import (xenserver_common_argument_spec, XAPI, XenServerObject, get_object_ref,
                                            gather_vm_params, gather_vm_facts)


class XenServerVM(XenServerObject):
    """Class for managing XenServer VM.

    Attributes:
        vm_ref (str): XAPI reference to VM.
        vm_params (dict): A dictionary with VM parameters as returned
            by gather_vm_params() function.
    """

    def __init__(self, module):
        """Inits XenServerVM using module parameters.

        Args:
            module: Reference to AnsibleModule object.
        """
        super(XenServerVM, self).__init__(module)

        self.vm_ref = get_object_ref(self.module, self.module.params['name'], self.module.params['uuid'], obj_type="VM", fail=True, msg_prefix="VM search: ")
        self.gather_params()

    def gather_params(self):
        """Gathers all VM parameters available in XAPI database."""
        self.vm_params = gather_vm_params(self.module, self.vm_ref)

    def gather_facts(self):
        """Gathers and returns VM facts."""
        return gather_vm_facts(self.module, self.vm_params)


def main():
    argument_spec = xenserver_common_argument_spec()
    argument_spec.update(
        name=dict(type='str', aliases=['name_label']),
        uuid=dict(type='str'),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=[
                               ['name', 'uuid'],
                           ],
                           )

    result = {'failed': False, 'changed': False}

    # Module will exit with an error message if no VM is found.
    vm = XenServerVM(module)

    # Gather facts.
    result['instance'] = vm.gather_facts()

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
