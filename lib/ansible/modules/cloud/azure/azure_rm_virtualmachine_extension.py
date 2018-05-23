#!/usr/bin/python
#
# Copyright (c) 2017 Sertac Ozercan <seozerca@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_virtualmachine_extension

version_added: "2.4"

short_description: Managed Azure Virtual Machine extension

description:
    - Create, update and delete Azure Virtual Machine Extension

options:
    resource_group:
        description:
            - Name of a resource group where the vm extension exists or will be created.
        required: true
    name:
        description:
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
        required: false
    virtual_machine_name:
        description:
            - The name of the virtual machine where the extension should be create or updated.
        required: false
    publisher:
        description:
            - The name of the extension handler publisher.
        required: false
    virtual_machine_extension_type:
        description:
            - The type of the extension handler.
        required: false
    type_handler_version:
        description:
            - The type version of the extension handler.
        required: false
    settings:
        description:
            - Json formatted public settings for the extension.
        required: false
    protected_settings:
        description:
            - Json formatted protected settings for the extension.
        required: false
    auto_upgrade_minor_version:
        description:
            - Whether the extension handler should be automatically upgraded across minor versions.
        required: false
        type: bool

extends_documentation_fragment:
    - azure

author:
    - "Sertac Ozercan (@sozercan)"
    - "Julien Stroheker (@julienstroheker)"
'''

EXAMPLES = '''
    - name: Create VM Extension
      azure_rm_virtualmachine_extension:
        name: myvmextension
        location: eastus
        resource_group: Testing
        virtual_machine_name: myvm
        publisher: Microsoft.Azure.Extensions
        virtual_machine_extension_type: CustomScript
        type_handler_version: 2.0
        settings: '{"commandToExecute": "hostname"}'
        auto_upgrade_minor_version: true

    - name: Delete VM Extension
      azure_rm_virtualmachine_extension:
        name: myvmextension
        location: eastus
        resource_group: Testing
        virtual_machine_name: myvm
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
except ImportError:
    # This is handled in azure_rm_common
    pass


def vmextension_to_dict(extension):
    '''
    Serializing the VM Extension from the API to Dict
    :return: dict
    '''
    return dict(
        id=extension.id,
        name=extension.name,
        location=extension.location,
        publisher=extension.publisher,
        virtual_machine_extension_type=extension.virtual_machine_extension_type,
        type_handler_version=extension.type_handler_version,
        auto_upgrade_minor_version=extension.auto_upgrade_minor_version,
        settings=extension.settings,
        protected_settings=extension.protected_settings,
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
            auto_upgrade_minor_version=dict(
                type='bool',
                required=False
            ),
            settings=dict(
                type='dict',
                required=False
            ),
            protected_settings=dict(
                type='dict',
                required=False
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.publisher = None
        self.virtual_machine_extension_type = None
        self.type_handler_version = None
        self.auto_upgrade_minor_version = None
        self.settings = None
        self.protected_settings = None
        self.state = None

        self.results = dict(changed=False, state=dict())

        super(AzureRMVMExtension, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                 supports_check_mode=False,
                                                 supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        resource_group = None
        response = None
        to_be_updated = False

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        if self.state == 'present':
            response = self.get_vmextension()
            if not response:
                to_be_updated = True
            else:
                if response['settings'] != self.settings:
                    response['settings'] = self.settings
                    to_be_updated = True

                if response['protected_settings'] != self.protected_settings:
                    response['protected_settings'] = self.protected_settings
                    to_be_updated = True

            if to_be_updated:
                self.results['changed'] = True
                self.results['state'] = self.create_or_update_vmextension()
        elif self.state == 'absent':
            self.delete_vmextension()
            self.results['changed'] = True

        return self.results

    def create_or_update_vmextension(self):
        '''
        Method calling the Azure SDK to create or update the VM extension.
        :return: void
        '''
        self.log("Creating VM extension {0}".format(self.name))
        try:
            params = self.compute_models.VirtualMachineExtension(
                location=self.location,
                publisher=self.publisher,
                virtual_machine_extension_type=self.virtual_machine_extension_type,
                type_handler_version=self.type_handler_version,
                auto_upgrade_minor_version=self.auto_upgrade_minor_version,
                settings=self.settings,
                protected_settings=self.protected_settings
            )
            poller = self.compute_client.virtual_machine_extensions.create_or_update(self.resource_group, self.virtual_machine_name, self.name, params)
            response = self.get_poller_result(poller)
            return vmextension_to_dict(response)

        except CloudError as e:
            self.log('Error attempting to create the VM extension.')
            self.fail("Error creating the VM extension: {0}".format(str(e)))

    def delete_vmextension(self):
        '''
        Method calling the Azure SDK to delete the VM Extension.
        :return: void
        '''
        self.log("Deleting vmextension {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machine_extensions.delete(self.resource_group, self.virtual_machine_name, self.name)
            self.get_poller_result(poller)
        except CloudError as e:
            self.log('Error attempting to delete the vmextension.')
            self.fail("Error deleting the vmextension: {0}".format(str(e)))

    def get_vmextension(self):
        '''
        Method calling the Azure SDK to get a VM Extension.
        :return: void
        '''
        self.log("Checking if the vm extension {0} is present".format(self.name))
        found = False
        try:
            response = self.compute_client.virtual_machine_extensions.get(self.resource_group, self.virtual_machine_name, self.name)
            found = True
        except CloudError as e:
            self.log('Did not find vm extension')
        if found:
            return vmextension_to_dict(response)
        else:
            return False


def main():
    """Main execution"""
    AzureRMVMExtension()

if __name__ == '__main__':
    main()
