#!/usr/bin/python
#
# Copyright (c) 2017 Emma Laurijssens van Engelenhoven, <emma@talwyn-esp.nl>
#
#  GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
author: Emma Laurijssens van Engelenhoven (@elaurijssens)
description:
  - Show information about VM images in a given subscription in Azure.
  - Depends on pip azure module 2.0.0 or above and azure-mgmt-compute 2.1.0 and above.
module: azure_rm_image_facts
options:
  name:
    description:
      - The name of the image being queried.
  resource_group:
    description:
      - The name of the resource group to search in

extends_documentation_fragment:
  - azure
  - azure_tags

short_description: "Show information about available Azure Virtual Machine Images"
version_added: "2.6"

'''

EXAMPLES = '''
  - name: List all images in subscription
    azure_rm_image_facts:
      subscription_id: dee31f9f-1b6d-408b-aadf-720486bd766c
      client_id: 46a522a7-ff6d-4e04-a89f-2c6882c8b483
      tenant_id: b497b8d9-2bab-4acb-bbc3-fec05692409d
      client_secret: R0gwWU93MGp5TVowR2FvOGhc4NDYwMUpRQzVZWT0=

  - name: List facts about given image name
    azure_rm_image_facts:
      name: win2016-1

'''

RETURN = '''
azure_images:
    description: A list of matching image dicts
    returned: always
    type: list
exists:
    description: Whether or not the requested image was found
    returned: always
    type: bool
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
except:
    pass


class AzureRMImageFacts(AzureRMModuleBase):
    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(
                type='str',
                required=False
            ),
            resource_group=dict(
                type='str',
                required=False
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.tags = None

        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_images=None)
        )

        super(AzureRMImageFacts, self).__init__(
            derived_arg_spec=self.module_arg_spec,
            supports_check_mode=True,
            supports_tags=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        self.results['ansible_facts'] = (
            self.get_item() if (self.name or self.resource_group)
            else self.list_items())

        return self.results

    def _list_images(self):
        try:
            images = self.compute_client.images
            image_list = images.list()
        except CloudError:
            self.fail("No images found!")
        except Exception as e:
            self.fail("An exception occurred: {0}".format(str(e)))

        named_images = []

        for image in image_list:

            data_disks = []

            for disks in image.storage_profile.data_disks:
                data_disks.append(dict(lun=disks.lun,
                                       disk_size_gb=disks.disk_size_gb,
                                       managed_disk=(not (disks.managed_disk is None))))

            os_disk = dict(disk_size_gb=image.storage_profile.os_disk.disk_size_gb,
                           managed_disk=(not (image.storage_profile.os_disk.managed_disk is None)))

            image_info = dict(name=image.name,
                              location=image.location,
                              resource_group=image.id.split("/")[4],
                              managed=(not (image.storage_profile.os_disk.managed_disk is None)),
                              id=image.id,
                              storage_profile=dict(os_disk=os_disk,
                                                   data_disks=data_disks))
            named_images.append(image_info)

        return named_images

    def list_items(self):

        image_names = self._list_images()

        exists = not (not image_names)

        return dict(azure_images=image_names,
                    exists=exists,
                    changed=False)

    def get_item(self):

        image_names = self._list_images()
        image_item = []

        found = False

        for image in image_names:
            if self.name and self.resource_group:
                if (image['name'] == self.name) and (image['resource_group'].lower() == self.resource_group.lower()):
                    image_item.append(image)
                    found = True
            elif self.name:
                if image['name'] == self.name:
                    image_item.append(image)
                    found = True
            elif self.resource_group:
                if image['resource_group'].lower() == self.resource_group.lower():
                    image_item.append(image)
                    found = True

        return dict(azure_images=image_item,
                    exists=found,
                    changed=False)


def main():
    AzureRMImageFacts()


if __name__ == '__main__':
    main()
