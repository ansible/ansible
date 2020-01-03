#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Anusha Hegde <anushah@vmware.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: vmware_guest_cross_vc_clone

short_description: Cross-vCenter VM/template clone

version_added: '2.10'

description:
  - 'This module can be used for Cross-vCenter vm/template clone'

options:
  name:
    description:
      - Name of the virtual machine or template.
      - This is a required parameter, if parameter C(uuid) or C(moid) is not supplied.
    type: str
  uuid:
    description:
      - UUID of the vm/template instance to clone from, this is VMware's unique identifier.
      - This is a required parameter, if parameter C(name) or C(moid) is not supplied.
    type: str
  moid:
    description:
      - Managed Object ID of the vm/template instance to manage if known, this is a unique identifier only within a single vCenter instance.
      - This is required if C(name) or C(uuid) is not supplied.
    type: str
  use_instance_uuid:
    description:
      - Whether to use the VMware instance UUID rather than the BIOS UUID.
    default: no
    type: bool
  destination_vm_name:
    description:
      - The name of the cloned VM.
    type: str
    required: True
  destination_vcenter:
    description:
      - The hostname or IP address of the destination VCenter.
    type: str
    required: True
  destination_vcenter_username:
    description:
      - The username of the destination VCenter.
    type: str
    required: True
  destination_vcenter_password:
    description:
      - The password of the destination VCenter.
    type: str
    required: True
  destination_host:
    description:
      - The name of the destination host.
    type: str
    required: True
  destination_datastore:
    description:
      - The name of the destination datastore.
    type: str
    required: True
  destination_vm_folder:
    description:
      - The name of the destination folder where the VM will be cloned.
    type: str
    required: True
  power_on:
    description:
      - Whether to power on the VM after cloning
    default: no
    type: bool

extends_documentation_fragment:
  - vmware.documentation

author:
  - Anusha Hegde (@anusha94)
'''

EXAMPLES = '''
# Clone template
- name: clone a template across VC
  vmware_guest_cross_vc_clone:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    name: "test_vm1"
    destination_vm_name: "cloned_vm_from_template"
    destination_vcenter: '{{ destination_vcenter_hostname }}'
    destination_vcenter_username: '{{ destination_vcenter_username }}'
    destination_vcenter_password: '{{ destination_vcenter_password }}'
    destination_host: '{{ destination_esxi }}'
    destination_datastore: '{{ destination_datastore }}'
    destination_vm_folder: '{{ destination_vm_folder }}'
    power_on: no
  register: cross_vc_clone_from_template

- name: clone a VM across VC
  vmware_guest_cross_vc_clone:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: "{{ vcenter_password }}"
    validate_certs: no
    name: "test_vm1"
    destination_vm_name: "cloned_vm_from_vm"
    destination_vcenter: '{{ destination_vcenter_hostname }}'
    destination_vcenter_username: '{{ destination_vcenter_username }}'
    destination_vcenter_password: '{{ destination_vcenter_password }}'
    destination_host: '{{ destination_esxi }}'
    destination_datastore: '{{ destination_datastore }}'
    destination_vm_folder: '{{ destination_vm_folder }}'
    power_on: yes
  register: cross_vc_clone_from_vm
'''

RETURN = r'''
vm_info:
    description: metadata about the virtual machine
    returned: always
    type: dict
    sample: {
        "vm_name": "",
        "vcenter": "",
        "host": "",
        "datastore": "",
        "vm_folder": "",
        "power_on": ""
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, find_hostsystem_by_name,
                                         find_vm_by_id, find_datastore_by_name,
                                         find_folder_by_name, find_vm_by_name,
                                         connect_to_api, vmware_argument_spec,
                                         gather_vm_facts,
                                         wait_for_task, TaskError)
from ansible.module_utils._text import to_native
try:
    from pyVmomi import vim
except ImportError:
    pass


class CrossVCCloneManager(PyVmomi):
    def __init__(self, module):
        super(CrossVCCloneManager, self).__init__(module)
        self.config_spec = vim.vm.ConfigSpec()
        self.clone_spec = vim.vm.CloneSpec()
        self.relocate_spec = vim.vm.RelocateSpec()
        self.service_locator = vim.ServiceLocator()
        self.destination_vcenter = self.params['destination_vcenter']
        self.destination_vcenter_username = self.params['destination_vcenter_username']
        self.destination_vcenter_password = self.params['destination_vcenter_password']

    def get_new_vm_info(self, vm):
        # to check if vm has been cloned in the destination vc
        # query for the vm in destination vc
        # get the host and datastore info
        # get the power status of the newly cloned vm
        info = {}
        vm_obj = find_vm_by_name(content=self.destination_content, vm_name=vm)
        if vm_obj is None:
            self.module.fail_json(msg="Newly cloned VM is not found in the destination VCenter")
        else:
            vm_facts = gather_vm_facts(self.destination_content, vm_obj)
            info['vm_name'] = vm
            info['vcenter'] = self.destination_vcenter
            info['host'] = vm_facts['hw_esxi_host']
            info['datastore'] = vm_facts['hw_datastores']
            info['vm_folder'] = vm_facts['hw_folder']
            info['power_on'] = vm_facts['hw_power_status']
        return info

    def clone(self):
        # clone the vm/template on destination VC
        vm_folder = find_folder_by_name(content=self.destination_content, folder_name=self.params['destination_vm_folder'])
        vm_name = self.params['destination_vm_name']
        task = self.vm_obj.Clone(folder=vm_folder, name=vm_name, spec=self.clone_spec)
        wait_for_task(task)
        if task.info.state == 'error':
            result = {'changed': False, 'failed': True, 'msg': task.info.error.msg}
        else:
            vm_info = self.get_new_vm_info(vm_name)
            result = {'changed': True, 'failed': False, 'vm_info': vm_info}
        return result

    def sanitize_params(self):
        '''
        this method is used to verify user provided parameters
        '''
        self.vm_obj = find_vm_by_name(content=self.content, vm_name=self.params['name'])
        if self.vm_obj is None:
            vm_id = self.vm_uuid or self.vm_name or self.moid
            self.module.fail_json(msg="Failed to find the VM/template with %s" % vm_id)

        # connect to destination VC
        self.destination_content = connect_to_api(
            self.module,
            hostname=self.destination_vcenter,
            username=self.destination_vcenter_username,
            password=self.destination_vcenter_password)
        if self.params['destination_datastore']:
          self.destination_datastore = find_datastore_by_name(content=self.destination_content, datastore_name=self.params['destination_datastore'])
          if self.destination_datastore is None:
            self.module.fail_json(msg="Destination datastore not found.")
        else:
          self.module.fail_json(msg="Destination datastore not specified by the user.")

        if self.params['destination_host']:
          self.destination_host = find_hostsystem_by_name(content=self.destination_content, hostname=self.params['destination_host'])
          if self.destination_host is None:
            self.module.fail_json(msg="Destination host not found.")
        else:
          self.module.fail_json(msg="Destination host not specified by the user.")

    def populate_specs(self):
        # populate service locator
        self.service_locator.instanceUuid = self.destination_content.about.instanceUuid
        self.service_locator.url = "https://" + self.destination_vcenter + ":" + str(self.params['port']) + "/sdk"
        creds = vim.ServiceLocatorNamePassword()
        creds.username = self.destination_vcenter_username
        creds.password = self.destination_vcenter_password
        self.service_locator.credential = creds

        # populate relocate spec
        self.relocate_spec.datastore = self.destination_datastore
        self.relocate_spec.pool = self.destination_host.parent.resourcePool
        self.relocate_spec.service = self.service_locator
        self.relocate_spec.host = self.destination_host

        # populate config spec
        self.config_spec.numCPUs = 1
        self.config_spec.memoryMB = 1024

        # populate clone spec
        self.clone_spec.config = self.config_spec
        self.clone_spec.powerOn = self.module.params['power_on']
        self.clone_spec.location = self.relocate_spec


def main():
    """
    Main method
    """
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        destination_vm_name=dict(type='str', required=True),
        destination_datastore=dict(type='str', required=True),
        destination_host=dict(type='str', required=True),
        destination_vcenter=dict(type='str', required=True),
        destination_vcenter_username=dict(type='str', required=True),
        destination_vcenter_password=dict(type='str', required=True),
        destination_vm_folder=dict(type='str', required=True),
        power_on=dict(type='bool', default=False)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['uuid', 'name', 'moid'],
        ],
        mutually_exclusive=[
            ['uuid', 'name', 'moid'],
        ],
    )
    result = {'failed': False, 'changed': False}

    clone_manager = CrossVCCloneManager(module)
    clone_manager.sanitize_params()
    clone_manager.populate_specs()
    result = clone_manager.clone()

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
