#!/usr/bin/python
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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = '''
---
author: "Emma Laurijssens van Engelenhoven"
description:
  - "Capture an Azure Virtual Machine image for the deployment of other VMs in Azure 
     The VM should be generalized usimg sysprep. After this command runs, the Virtual Machine will be unusable.
     Depends on pip azure module 2.0.0 or above and azure-mgmt-compute 2.1.0 and above."
module: azure_rm_image_facts
options:
  name:
    description:
      - "The name of the image being queried."
    required: false

short_description: "Capture Azure Virtual Machine Images"
version_added: "2.9"

'''

EXAMPLES = '''
- name: Capture image
  hosts: 127.0.0.1
  connection: local

  tasks:
    - name: List all images in subscription
      azure_rm_image_facts:
        subscription_id: "{{ subscription_id }}"
        resource_group_name: "{{ resource_group_name }}"
        client_id: "{{ secrets.client_id }}"
        tenant_id: "{{ tenant_id }}"
        client_secret: "{{ secrets.client_secret }}"

    - name: List facts about given image name
      azure_rm_image_facts:
        subscription_id: "{{ subscription_id }}"
        resource_group_name: "{{ resource_group_name }}"
        client_id: "{{ secrets.client_id }}"
        tenant_id: "{{ tenant_id }}"
        client_secret: "{{ secrets.client_secret }}"
        name: win2016-1

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
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.tags = None

        self.results = dict(
            changed=False,
            status="None",
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
            self.get_item() if self.name
            else self.list_items())

        return self.results

    def _list_images(self):
        try:
            images = self.compute_client.images
            image_list = images.list()  # (resource_group_name=self.resource_group, name=self.name)
        except CloudError:
            self.fail("No images found!")
        except Exception as e:
            self.fail("An exception occurred: {}".format(str(e)))

        named_images = []

        for image in image_list:
            image_info = dict(name=image.name,
                              location=image.location,
                              resource_group=image.id.split("/")[4],
                              managed=(not (image.storage_profile.os_disk.managed_disk is None))
                              )
            named_images.append(image_info)

        return named_images

    def list_items(self):

        image_names = self._list_images()

        return dict(azure_images=image_names,
                    status="Found",
                    changed=False)

    def get_item(self):

        status = "Not found"
        image_names = self._list_images()
        image_item = []

        found = any(elem['name'] == self.name for elem in image_names)

        if found:
            for image in image_names:
                if image['name'] == self.name:
                    status = "Found"
                    image_item.append(image)

        return dict(azure_images=image_item,
                    status=status,
                    changed=False)


def main():
    AzureRMImageFacts()


if __name__ == '__main__':
    main()
