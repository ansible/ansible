#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright, (c) 2018, Ansible Project
# Copyright, (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright, (c) 2018, Fedor Vompe <f.vompe () comptek.ru>
#
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
module: vmware_guest_custom_attributes
short_description: Manage custom attributes from VMWare for the given virtual machine
description:
    - This module can be used to get, add, remove and update custom attributes for the given virtual machine.
version_added: 2.7
author:
    - Jimmy Conner (@cigamit)
    - Abhijeet Kasurde (@Akasurde)
    - Fedor Vompe (@sumkincpp)
notes:
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
     description:
     - Name of the virtual machine to work with.
     required: True
   state:
     description:
     - The action to take.
     - If set to C(present), then custom attribute is added or updated.
     - If set to C(absent), then custom attribute is removed.
     default: 'present'
     choices: ['present', 'absent']
   uuid:
     description:
     - UUID of the virtual machine to manage if known. This is VMware's unique identifier.
     - This is required parameter, if C(name) is not supplied.
   folder:
     description:
     - Absolute path to find an existing guest.
     - This is required parameter, if C(name) is supplied and multiple virtual machines with same name are found.
   datacenter:
     description:
     - Datacenter name where the virtual machine is located in.
     required: True
   attributes:
     description:
     - A list of name and value of custom attributes that needs to be manage.
     - Value of custom attribute is not required and will be ignored, if C(state) is set to C(absent).
     default: []
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Get current virtual machine attributes
  vmware_guest_custom_attributes:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
  delegate_to: localhost
  register: attributes

- name: Add virtual machine custom attributes
  vmware_guest_custom_attributes:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
    state: present
    attributes:
      - name: MyAttribute
        value: MyValue
  delegate_to: localhost
  register: attributes

- name: Add multiple virtual machine custom attributes
  vmware_guest_custom_attributes:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
    state: present
    attributes:
      - name: MyAttribute
        value: MyValue
      - name: MyAttribute2
        value: MyValue2
  delegate_to: localhost
  register: attributes

- name: Remove virtual machine attribute
  vmware_guest_custom_attributes:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
    state: absent
    attributes:
      - name: MyAttribute
  delegate_to: localhost
  register: attributes

'''

RETURN = """
custom_attributes:
    description: metadata about the virtual machine attributes with non-empty values
    returned: always
    type: dict
    sample: {
        "mycustom": "my_custom_value",
        "mycustom_2": "my_custom_value_2",
        "sample_1": "sample_1_value",
        "sample_2": "sample_2_value",
        "sample_3": "sample_3_value"
    }
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec


class VmAttributeManager(PyVmomi):

    def __init__(self, module):
        super(VmAttributeManager, self).__init__(module)

        self.vm_attributes = self.get_vm_attributes(self.get_vm())
        self.result_vm_attributes = self.vm_attributes.copy()

    def get_vm_attributes(self):
        return dict((x.name, v.value) for x in self.content.customFieldsManager.field
                    for v in self.get_vm().customValue if x.key == v.key)

    def set_attributes(self, user_fields):
        for field in user_fields:
            self.set_attr_value(self, field.get('name'), field.get('value'))

        changed = self.vm_attributes == self.result_vm_attributes

        return {'changed': changed, 'failed': False, 'custom_attributes': self.result_vm_attributes}

    def set_attr_value(self, field_name, field_value):
        if field_name is None or field_value is None:
            return

        if self.vm_attributes.get(field_name) == field_value:
            return

        if field_value:
            self.result_vm_attributes[field_name] = field_value
        else:
            del self.result_vm_attributes[field_name]

        if self.module.check_mode:
            return

        field_definition = self.get_or_add_field_definition(field_name)

        self.content.customFieldsManager.SetField(
            entity=self.vm, key=field_definition.key, value=field_value)

    def get_or_add_field_definition(self, field_name):
        field_definition = self.field_definition(field_name)

        if not field_definition and not self.module.check_mode:
            field_definition = self.content.customFieldsManager.AddFieldDefinition(
                name=field_name, moType=vim.VirtualMachine)

        return field_definition

    def field_definition(self, field_name):
        for x in self.content.customFieldsManager.field:
            if x.name == field_name:
                return x
        return None


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        datacenter=dict(type='str'),
        name=dict(required=True, type='str'),
        folder=dict(type='str'),
        uuid=dict(type='str'),
        state=dict(type='str', default='present',
                   choices=['absent', 'present']),
        attributes=dict(
            type='list',
            default=[],
            options=dict(
                name=dict(type='str', required=True),
                value=dict(type='str'),
            )
        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['name', 'uuid']],
    )

    if module.params.get('folder'):
        # FindByInventoryPath() does not require an absolute path
        # so we should leave the input folder path unmodified
        module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = VmAttributeManager(module)
    results = {'changed': False, 'failed': False, 'instance': dict()}

    # Check if the virtual machine exists before continuing
    if pyv.get_vm():
        # TODO: Make absent/present state distinguishible
        # Currently we rely on logic when for deleting custom field we need
        # to pass empty field value
        if module.params['state'] == "present":
            results = pyv.set_attributes(module.params['attributes'])
        elif module.params['state'] == "absent":
            results = pyv.set_attributes(module.params['attributes'])

        module.exit_json(**results)
    else:
        # virtual machine does not exists
        module.fail_json(msg="Unable to manage custom attributes for non-existing"
                             " virtual machine %s" %
                             (module.params.get('name') or
                              module.params.get('uuid')))


if __name__ == '__main__':
    main()
