#!/usr/bin/python
#
# Copyright (c) 2017 Julien Stroheker, <juliens@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_availabilityset

version_added: "2.4"

short_description: Manage Azure availability set.

description:
    - Create, update and delete Azure availability set. An availability set cannot be updated, you will have to
      recreate one instead. The only update operation will be for the tags.

options:
    resource_group:
        description:
            - Name of a resource group where the availability set exists or will be created.
        required: true
    name:
        description:
            - Name of the availability set.
        required: true
    state:
        description:
            - Assert the state of the availability set. Use C(present) to create or update a availability set and
              C(absent) to delete a availability set.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
    platform_update_domain_count:
        description:
            - Update domains indicate groups of virtual machines and underlying physical hardware that can be rebooted at the same time. Default is 5.
        default: 5
    platform_fault_domain_count:
        description:
            - Fault domains define the group of virtual machines that share a common power source and network switch. Should be between 1 and 3. Default is 3
        default: 3
    sku:
        description:
            - Define if the availability set supports managed disks.
        default: Classic
        choices:
            - Classic
            - Aligned
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Julien Stroheker (@julienstroheker)"
'''

EXAMPLES = '''
    - name: Create an availability set with default options
      azure_rm_availabilityset:
        name: myavailabilityset
        location: eastus
        resource_group: myResourceGroup

    - name: Create an availability set with advanced options
      azure_rm_availabilityset:
        name: myavailabilityset
        location: eastus
        resource_group: myResourceGroup
        platform_update_domain_count: 5
        platform_fault_domain_count: 3
        sku: Aligned

    - name: Delete an availability set
      azure_rm_availabilityset:
        name: myavailabilityset
        location: eastus
        resource_group: myResourceGroup
        state: absent
'''

RETURN = '''
state:
    description: Current state of the availability set
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


def availability_set_to_dict(avaset):
    '''
    Serializing the availability set from the API to Dict
    :return: dict
    '''
    return dict(
        id=avaset.id,
        name=avaset.name,
        location=avaset.location,
        platform_update_domain_count=avaset.platform_update_domain_count,
        platform_fault_domain_count=avaset.platform_fault_domain_count,
        tags=avaset.tags,
        sku=avaset.sku.name
    )


class AzureRMAvailabilitySet(AzureRMModuleBase):
    """Configuration class for an Azure RM availability set resource"""

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
                default='present',
                choices=['present', 'absent']
            ),
            location=dict(
                type='str'
            ),
            platform_update_domain_count=dict(
                type='int',
                default=5
            ),
            platform_fault_domain_count=dict(
                type='int',
                default=3
            ),
            sku=dict(
                type='str',
                default='Classic',
                choices=['Classic', 'Aligned']
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.tags = None
        self.platform_update_domain_count = None
        self.platform_fault_domain_count = None
        self.sku = None
        self.state = None
        self.warning = False

        self.results = dict(changed=False, state=dict())

        super(AzureRMAvailabilitySet, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                     supports_check_mode=True,
                                                     supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        resource_group = None
        response = None
        to_be_updated = False

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        # Check if the AS already present in the RG
        if self.state == 'present':
            response = self.get_availabilityset()
            self.results['state'] = response

            if not response:
                to_be_updated = True
            else:
                update_tags, response['tags'] = self.update_tags(response['tags'])

                if update_tags:
                    self.log("Tags has to be updated")
                    to_be_updated = True

                if response['platform_update_domain_count'] != self.platform_update_domain_count:
                    self.faildeploy('platform_update_domain_count')

                if response['platform_fault_domain_count'] != self.platform_fault_domain_count:
                    self.faildeploy('platform_fault_domain_count')

                if response['sku'] != self.sku:
                    self.faildeploy('sku')

            if self.check_mode:
                return self.results

            if to_be_updated:
                self.results['state'] = self.create_or_update_availabilityset()
                self.results['changed'] = True

        elif self.state == 'absent':
            self.delete_availabilityset()
            self.results['changed'] = True

        return self.results

    def faildeploy(self, param):
        '''
        Helper method to push fail message in the console.
        Useful to notify that the users cannot change some values in a Availability Set

        :param: variable's name impacted
        :return: void
        '''
        self.fail("You tried to change {0} but is was unsuccessful. An Availability Set is immutable, except tags".format(str(param)))

    def create_or_update_availabilityset(self):
        '''
        Method calling the Azure SDK to create or update the AS.
        :return: void
        '''
        self.log("Creating availabilityset {0}".format(self.name))
        try:
            params_sku = self.compute_models.Sku(
                name=self.sku
            )
            params = self.compute_models.AvailabilitySet(
                location=self.location,
                tags=self.tags,
                platform_update_domain_count=self.platform_update_domain_count,
                platform_fault_domain_count=self.platform_fault_domain_count,
                sku=params_sku
            )
            response = self.compute_client.availability_sets.create_or_update(self.resource_group, self.name, params)
        except CloudError as e:
            self.log('Error attempting to create the availability set.')
            self.fail("Error creating the availability set: {0}".format(str(e)))

        return availability_set_to_dict(response)

    def delete_availabilityset(self):
        '''
        Method calling the Azure SDK to delete the AS.
        :return: void
        '''
        self.log("Deleting availabilityset {0}".format(self.name))
        try:
            response = self.compute_client.availability_sets.delete(self.resource_group, self.name)
        except CloudError as e:
            self.log('Error attempting to delete the availability set.')
            self.fail("Error deleting the availability set: {0}".format(str(e)))

        return True

    def get_availabilityset(self):
        '''
        Method calling the Azure SDK to get an AS.
        :return: void
        '''
        self.log("Checking if the availabilityset {0} is present".format(self.name))
        found = False
        try:
            response = self.compute_client.availability_sets.get(self.resource_group, self.name)
            found = True
        except CloudError as e:
            self.log('Did not find the Availability set.')
        if found is True:
            return availability_set_to_dict(response)
        else:
            return False


def main():
    """Main execution"""
    AzureRMAvailabilitySet()


if __name__ == '__main__':
    main()
