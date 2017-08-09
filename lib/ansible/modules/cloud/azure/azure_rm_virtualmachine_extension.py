#!/usr/bin/python
#
# Copyright (c) 2017 Sertac Ozercan, <seozerca@microsoft.com>
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
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_virtualmachine_extension

version_added: "2.4"

short_description:

description:
    - C

options:
    resource_group:
        description:
            - Name of a resource group where the vm extension exists or will be created.
        required: true
    name:
        description:a
            - Name of the vm extension
        required: true
    state:
        description:
            - Assert the state of the vm extension. Use 'present' to create or update a vm extension and
              'absent' to delete a vm extension.
        default: present
        choices:
            - absent
            - present
        required: false
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
        default: resource_group location
        required: false
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Sertac Ozercan (@sozercan)"
    - "Julien Stroheker (@ju_stroh)"
'''

EXAMPLES = '''
    - name: Create VM Extension
      azure_rm_virtualmachine_extension:
        name: myvmextension
        location: eastus
        resource_group: Testing
        virtual_machine_name: myvm

    - name: Delete VM Extension
      azure_rm_virtualmachine_extension:
        name: myvmextension
        location: eastus
        resource_group: Testing
        state: absent
'''

RETURN = '''
state:
    description: Current state of the vm extension
    returned: always
    type: dict
changed:
    description: Whether or not the resource has changed
    returned: always
    type: bool
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureHttpError
    from azure.mgmt.compute.models import (
        VirtualMachineExtension
    )
except ImportError:
    # This is handled in azure_rm_common
    pass

def vmextension_to_dict(extension):
    return dict(
        name=extension.name,
        location=extension.location,
        publisher=extension.publisher,
        virtual_machine_extension_type=extension.virtual_machine_extension_type,
        type_handler_version=extension.type_handler_version,
        settings=extension.settings,
        tags=extension.tags
    )

class AzureRMVMExtension(AzureRMModuleBase):
    """Configuration class for an Azure RM VM Extension resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            state=dict(
                type='str',
                required=False,
                default='present',
                choices=['present', 'absent']
            ),
            location=dict(
                type='str',
                required=False
            ),
            virtual_machine_name=dict(
                type='str',
                required=False
            ),
            publisher=dict(
                type='str',
                required=False
            ),
            virtual_machine_extension_type=dict(
                type='str',
                required=False
            ),
            type_handler_version=dict(
                type='str',
                required=False
            ),
            settings=dict(
                type='dict',
                required=False
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.tags = None
        self.publisher = None
        self.virtual_machine_extension_type = None
        self.type_handler_version = None
        self.settings = None

        self.results = dict(changed=False, state=dict())

        super(AzureRMVMExtension, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                    supports_check_mode=True,
                                                    supports_tags=True)


    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        results = dict()
        resource_group = None
        response= None

        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail('resource group {} not found'.format(self.resource_group))
        if not self.location:
            self.location = resource_group.location

        if self.state == 'present':
            response = self.get_vmextension()
            if not response:
                self.results['state'] = self.create_vmextension()
            else:
                self.log("VM Extension already there, updating Tags")
                update_tags, response['tags'] = self.update_tags(response['tags'])
                if update_tags:
                    self.create_vmextension()
                    self.results['changed'] = True
        elif self.state == 'absent':
            self.delete_vmextension()

        return self.results

    def create_vmextension(self):
        self.log("Creating vmextension {0}".format(self.name))
        try:
            params = VirtualMachineExtension(
                location=self.location,
                tags=self.tags,
                publisher=self.publisher,
                virtual_machine_extension_type=self.virtual_machine_extension_type,
                type_handler_version=self.type_handler_version,
                settings=self.settings
                )
            response = self.compute_client.virtual_machine_extensions.create_or_update(self.resource_group, self.virtual_machine_name, self.name, params)
        except AzureHttpError as e:
            self.log('Error attempting to create the vmextension.')
            self.fail("Error creating the vmextension: {0}".format(str(e)))

        return vmextension_to_dict(response)

    def delete_vmextension(self):
        self.log("Deleting vmextension {0}".format(self.name))
        try:
            response = self.compute_client.virtual_machine_extensions.delete(self.resource_group, self.virtual_machine_name, self.name)
        except AzureHttpError as e:
            self.log('Error attempting to delete the vmextension.')
            self.fail("Error deleting the vmextension: {0}".format(str(e)))

        return True

    def get_vmextension(self):
        self.log("Checking if the vm extension {0} is present".format(self.name))
        found = False
        try:
            response = self.compute_client.virtual_machine_extensions.get(self.resource_group, self.virtual_machine_name, self.name)
            found = True
        except CloudError as e:
            self.log('Did not find vm extension')
        if found==True:
            return vmextension_to_dict(response)
        else:
            return False

def main():
    """Main execution"""
    AzureRMVMExtension()

if __name__ == '__main__':
    main()