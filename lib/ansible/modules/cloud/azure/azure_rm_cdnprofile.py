#!/usr/bin/python
#
# Copyright (c) 2018 Hai Cao, <t-haicao@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Hai Cao <t-haicao@microsoft.com>"

'''

EXAMPLES = '''
'''
RETURN = '''
'''
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.mgmt.cdn.models import Profile, Sku, ErrorResponseException
except ImportError:
    # This is handled in azure_rm_common
    pass


def cdnprofile_to_dict(cdnprofile):
    return dict(
        id=cdnprofile.id,
        name=cdnprofile.name,
        type=cdnprofile.type,
        location=cdnprofile.location,
        sku=cdnprofile.sku.name,
        resource_state=cdnprofile.resource_state,
        provisioning_state=cdnprofile.provisioning_state,
        tags=cdnprofile.tags
    )

class AzureRMCdnprofile(AzureRMModuleBase):

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
            location=dict(
                type='str'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            ),
            sku=dict(
                type='str',
                choices=['Standard_Verizon', 'Premium_Verizon', 'Custom_Verizon', 'Standard_Akamai', 'Standard_ChinaCdn']
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.state = None
        self.tags = None
        self.sku = None

        required_if = [
            ('state', 'present', ['sku'])
        ]


        self.results = dict(changed=False)

        super(AzureRMCdnprofile, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                    supports_check_mode=True,
                                                    supports_tags=True,
                                                    required_if=required_if)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        to_be_updated = False

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        response = self.get_cdnprofile()

        if self.state == 'present':

            if not response:
                self.log("Need to create the CDN profile")
                
                if not self.check_mode:
                    self.results = self.create_cdnprofile()
                    self.log("Creation done")

                self.results['changed'] = True
                return self.results

            else:
                self.log('Results : {0}'.format(response))
                update_tags, response['tags'] = self.update_tags(response['tags'])

                if response['provisioning_state'] == "Succeeded":
                    if update_tags:
                        to_be_updated = True

                if to_be_updated:
                    self.log("Need to update the CDN profile")

                    if not self.check_mode:
                        self.results = self.update_cdnprofile()
                        self.log("Update done")

                    self.results['changed'] = True
                    return self.results

        elif self.state == 'absent' and response:
            self.log("Need to delete the CDN profile")
            self.results['changed'] = True

            if not self.check_mode:
                self.delete_cdnprofile()
                self.log("CDN profile deleted")

            return self.results

        return self.results

    def create_cdnprofile(self):
        '''
        Creates a Azure CDN profile.

        :return: deserialized Azure CDN profile instance state dictionary
        '''
        self.log("Creating the Azure CDN profile instance {0}".format(self.name))

        parameters = Profile(
            location=self.location,
            sku=Sku(name=self.sku),
            tags=self.tags
        )

        try:
            poller = self.cdn_management_client.profiles.create(self.resource_group, self.name, parameters)
            response = self.get_poller_result(poller)
            return cdnprofile_to_dict(response)
        except ErrorResponseException as exc:
            self.log('Error attempting to create Azure CDN profile instance.')
            self.fail("Error creating Azure CDN profile instance: {0}".format(exc.message))

    def update_cdnprofile(self):
        '''
        Updates a Azure CDN profile.

        :return: deserialized Azure CDN profile instance state dictionary
        '''
        self.log("Updating the Azure CDN profile instance {0}".format(self.name))

        try:
            poller = self.cdn_management_client.profiles.update(self.resource_group, self.name, self.tags)
            response = self.get_poller_result(poller)
            return cdnprofile_to_dict(response)
        except ErrorResponseException as exc:
            self.log('Error attempting to update Azure CDN profile instance.')
            self.fail("Error updating Azure CDN profile instance: {0}".format(exc.message))

    def delete_cdnprofile(self):
        '''
        Deletes the specified Azure CDN profile in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the CDN profile {0}".format(self.name))
        try:
            poller = self.cdn_management_client.profiles.delete(
                self.resource_group, self.name)
            self.get_poller_result(poller)
            return True
        except ErrorResponseException as e:
            self.log('Error attempting to delete the CDN profile.')
            self.fail("Error deleting the CDN profile: {0}".format(e.message))
            return False

    def get_cdnprofile(self):
        '''
        Gets the properties of the specified CDN profile.

        :return: deserialized CDN profile state dictionary
        '''
        self.log(
            "Checking if the CDN profile {0} is present".format(self.name))
        try:
            response = self.cdn_management_client.profiles.get(self.resource_group, self.name)
            self.log("Response : {0}".format(response))
            self.log("CDN profile : {0} found".format(response.name))
            return cdnprofile_to_dict(response)
        except ErrorResponseException:
            self.log('Did not find the CDN profile.')
            return False


def main():
    """Main execution"""
    AzureRMCdnprofile()


if __name__ == '__main__':
    main()
