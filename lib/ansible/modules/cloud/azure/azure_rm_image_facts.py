#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_image_facts

version_added: "2.8"

short_description: Get facts about azure custom images.

description:
    - List azure custom images. The images can be listed where scope of listing can be based on subscription, resource group, name or tags.

options:
    resource_group:
        description:
            - Name of resource group.
    name:
        description:
            - Name of the image to filter from existing images.
    tags:
        description:
            - List of tags to be matched.

extends_documentation_fragment:
    - azure

author:
    - "Madhura Naniwadekar (@Madhura-CSI)"
'''


EXAMPLES = '''
- name: List images with name
  azure_rm_image_facts:
    name: test-image
    resource_group: myResourceGroup

- name: List images by resource group
  azure_rm_image_facts:
    resource_group: myResourceGroup
    tags:
      - testing
      - foo:bar

- name: List all available images under current subscription
  azure_rm_image_facts:
'''


RETURN = '''
images:
    description: List of image dicts.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Id of the image.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/images/xx
        name:
            description:
                - Name of the image.
            returned: always
            type: str
        resource_group:
            description:
                - Resource group of the image.
            returned: always
            type: str
            sample: myResourceGroup
        location:
            description:
                - Location of the image.
            returned: always
            type: str
        os_disk:
            description:
                - Id of os disk for image.
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/disks/xx
        os_disk_caching:
            description:
                - Specifies caching requirements for the image.
            returned: always
            type: str
        os_state:
            description:
                - Specifies image operating system state. Possible values are 'Generalized' or 'Specialized'.
            returned: always
            type: str
            sample: Generalized
        os_storage_account_type:
            description:
                - Specifies the storage account type for the managed disk.
            type: str
            sample: Standard_LRS
        os_type:
            description:
                - Type of OS for image.
            returned: always
            type: str
            sample: Linux
        provisioning_state:
            description:
                - State of image.
            returned: always
            type: str
            sample: Succeeded
        source:
            description:
                - Resource id of source VM from which the image is created
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/virtualMachines/xx
        tags:
            description:
                - Dictionary of tags associated with the image.
            type: complex
        data_disks:
            description:
                - List of data disks associated with the image.
            type: complex
            returned: always
            contains:
                caching:
                    description:
                        - Type of caching of data disk.
                    sample: read_only
                disk_size_gb:
                    description:
                        - Specifies the size of empty data disks in gigabytes.
                    returned: always
                    type: int
                    sample: 50
                lun:
                    description:
                        - Specifies the logical unit number of the data disk.
                    returned: always
                    type: int
                    sample: 0
                storage_account_type:
                    description:
                        - Specifies the storage account type for the managed disk data disk.
                    type: str
                    sample: Standard_LRS
                managed_disk_id:
                    description:
                        - Id of managed disk.
                    type: str
                    sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/disks/xx
                blob_uri:
                    description:
                        - The virtual hard disk.
'''


try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


AZURE_ENUM_MODULES = ['azure.mgmt.compute.models']


class AzureRMImageFacts(AzureRMModuleBase):

    def __init__(self, **kwargs):

        self.module_arg_spec = dict(
            resource_group=dict(type='str'),
            name=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False
        )

        self.resource_group = None
        self.name = None
        self.format = None
        self.tags = None

        super(AzureRMImageFacts, self).__init__(
            derived_arg_spec=self.module_arg_spec,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name and self.resource_group:
            self.results['images'] = self.get_image(self.resource_group, self.name)
        elif self.name and not self.resource_group:
            self.results['images'] = self.list_images(self.name)
        elif not self.name and self.resource_group:
            self.results['images'] = self.list_images_by_resource_group(self.resource_group)
        elif not self.name and not self.resource_group:
            self.results['images'] = self.list_images()
        return self.results

    def get_image(self, resource_group, image_name):
        '''
        Returns image details based on its name
        '''

        self.log('Get properties for {0}'.format(self.name))

        result = []
        item = None
        try:
            item = self.compute_client.images.get(resource_group, image_name)
        except CloudError as exc:
            self.fail('Failed to list images - {0}'.format(str(exc)))

        result = [self.format_item(item)]
        return result

    def list_images_by_resource_group(self, resource_group):
        '''
        Returns image details based on its resource group
        '''

        self.log('List images filtered by resource group')
        response = None
        try:
            response = self.compute_client.images.list_by_resource_group(resource_group)
        except CloudError as exc:
            self.fail("Failed to list images: {0}".format(str(exc)))

        return [self.format_item(x) for x in response if self.has_tags(x.tags, self.tags)] if response else []

    def list_images(self, image_name=None):
        '''
        Returns image details in current subscription
        '''

        self.log('List images within current subscription')
        response = None
        results = []
        try:
            response = self.compute_client.images.list()
        except CloudError as exc:
            self.fail("Failed to list all images: {0}".format(str(exc)))

        results = [self.format_item(x) for x in response if self.has_tags(x.tags, self.tags)] if response else []
        if image_name:
            results = [result for result in results if result['name'] == image_name]
        return results

    def format_item(self, item):
        d = item.as_dict()

        for data_disk in d['storage_profile']['data_disks']:
            if 'managed_disk' in data_disk.keys():
                data_disk['managed_disk_id'] = data_disk['managed_disk']['id']
                data_disk.pop('managed_disk', None)

        d = {
            'id': d['id'],
            'resource_group': d['id'].split('/')[4],
            'name': d['name'],
            'location': d['location'],
            'tags': d.get('tags'),
            'source': d['source_virtual_machine']['id'] if 'source_virtual_machine' in d.keys() else None,
            'os_type': d['storage_profile']['os_disk']['os_type'],
            'os_state': d['storage_profile']['os_disk']['os_state'],
            'os_disk_caching': d['storage_profile']['os_disk']['caching'],
            'os_storage_account_type': d['storage_profile']['os_disk']['storage_account_type'],
            'os_disk': d['storage_profile']['os_disk']['managed_disk']['id'] if 'managed_disk' in d['storage_profile']['os_disk'].keys() else None,
            'os_blob_uri': d['storage_profile']['os_disk']['blob_uri'] if 'blob_uri' in d['storage_profile']['os_disk'].keys() else None,
            'provisioning_state': d['provisioning_state'],
            'data_disks': d['storage_profile']['data_disks']
        }
        return d


def main():
    AzureRMImageFacts()


if __name__ == '__main__':
    main()
