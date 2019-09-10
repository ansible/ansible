#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_virtualmachineimage_info

version_added: "2.9"

short_description: Get virtual machine image facts

description:
    - Get facts for virtual machine images.

options:
    location:
        description:
            - Azure location value, for example C(westus), C(eastus), C(eastus2), C(northcentralus), etc.
            - Supplying only a location value will yield a list of available publishers for the location.
        required: true
    publisher:
        description:
            - Name of an image publisher. List image offerings associated with a particular publisher.
    offer:
        description:
            - Name of an image offering. Combine with SKU to see a list of available image versions.
    sku:
        description:
            - Image offering SKU. Combine with offer to see a list of available versions.
    version:
        description:
            - Specific version number of an image.

extends_documentation_fragment:
    - azure

author:
    - Chris Houseknecht (@chouseknecht)
    - Matt Davis (@nitzmahone)

'''

EXAMPLES = '''
    - name: Get facts for a specific image
      azure_rm_virtualmachineimage_info:
        location: eastus
        publisher: OpenLogic
        offer: CentOS
        sku: '7.1'
        version: '7.1.20160308'

    - name: List available versions
      azure_rm_virtualmachineimage_info:
        location: eastus
        publisher: OpenLogic
        offer: CentOS
        sku: '7.1'

    - name: List available offers
      azure_rm_virtualmachineimage_info:
        location: eastus
        publisher: OpenLogic

    - name: List available publishers
      azure_rm_virtualmachineimage_info:
        location: eastus

'''

RETURN = '''
azure_vmimages:
    description:
        - List of image dicts.
    returned: always
    type: list
    example: [ {
                "id": "/Subscriptions/xxx...xxx/Providers/Microsoft.Compute/Locations/eastus/
                Publishers/OpenLogic/ArtifactTypes/VMImage/Offers/CentOS/Skus/7.1/Versions/7.1.20150410",
                "location": "eastus",
                "name": "7.1.20150410"
            },
            {
                "id": "/Subscriptions/xxx...xxx/Providers/Microsoft.Compute/Locations/eastus/
                Publishers/OpenLogic/ArtifactTypes/VMImage/Offers/CentOS/Skus/7.1/Versions/7.1.20150605",
                "location": "eastus",
                "name": "7.1.20150605"
            },
            {
                "id": "/Subscriptions/xxx...xxx/Providers/Microsoft.Compute/Locations/eastus/
                 Publishers/OpenLogic/ArtifactTypes/VMImage/Offers/CentOS/Skus/7.1/Versions/7.1.20150731",
                "location": "eastus",
                "name": "7.1.20150731"
            },
            {
                "id": "/Subscriptions/xxx...xxx/Providers/Microsoft.Compute/Locations/eastus/
                Publishers/OpenLogic/ArtifactTypes/VMImage/Offers/CentOS/Skus/7.1/Versions/7.1.20160308",
                "location": "eastus",
                "name": "7.1.20160308"
            }
           ]
'''

try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


AZURE_ENUM_MODULES = ['azure.mgmt.compute.models']


class AzureRMVirtualMachineImageInfo(AzureRMModuleBase):

    def __init__(self, **kwargs):

        self.module_arg_spec = dict(
            location=dict(type='str', required=True),
            publisher=dict(type='str'),
            offer=dict(type='str'),
            sku=dict(type='str'),
            version=dict(type='str')
        )

        self.results = dict(
            changed=False,
        )

        self.location = None
        self.publisher = None
        self.offer = None
        self.sku = None
        self.version = None

        super(AzureRMVirtualMachineImageInfo, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        is_old_facts = self.module._name == 'azure_rm_virtualmachineimage_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_virtualmachineimage_facts' module has been renamed to 'azure_rm_virtualmachineimage_info'", version='2.13')

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if is_old_facts:
            self.results['ansible_facts'] = dict()
            if self.location and self.publisher and self.offer and self.sku and self.version:
                self.results['ansible_facts']['azure_vmimages'] = self.get_item()
            elif self.location and self.publisher and self.offer and self.sku:
                self.results['ansible_facts']['azure_vmimages'] = self.list_images()
            elif self.location and self.publisher:
                self.results['ansible_facts']['azure_vmimages'] = self.list_offers()
            elif self.location:
                self.results['ansible_facts']['azure_vmimages'] = self.list_publishers()
        else:
            if self.location and self.publisher and self.offer and self.sku and self.version:
                self.results['vmimages'] = self.get_item()
            elif self.location and self.publisher and self.offer and self.sku:
                self.results['vmimages'] = self.list_images()
            elif self.location and self.publisher:
                self.results['vmimages'] = self.list_offers()
            elif self.location:
                self.results['vmimages'] = self.list_publishers()

        return self.results

    def get_item(self):
        item = None
        result = []

        try:
            item = self.compute_client.virtual_machine_images.get(self.location,
                                                                  self.publisher,
                                                                  self.offer,
                                                                  self.sku,
                                                                  self.version)
        except CloudError:
            pass

        if item:
            result = [self.serialize_obj(item, 'VirtualMachineImage', enum_modules=AZURE_ENUM_MODULES)]

        return result

    def list_images(self):
        response = None
        results = []
        try:
            response = self.compute_client.virtual_machine_images.list(self.location,
                                                                       self.publisher,
                                                                       self.offer,
                                                                       self.sku,)
        except CloudError:
            pass
        except Exception as exc:
            self.fail("Failed to list images: {0}".format(str(exc)))

        if response:
            for item in response:
                results.append(self.serialize_obj(item, 'VirtualMachineImageResource',
                                                  enum_modules=AZURE_ENUM_MODULES))
        return results

    def list_offers(self):
        response = None
        results = []
        try:
            response = self.compute_client.virtual_machine_images.list_offers(self.location,
                                                                              self.publisher)
        except CloudError:
            pass
        except Exception as exc:
            self.fail("Failed to list offers: {0}".format(str(exc)))

        if response:
            for item in response:
                results.append(self.serialize_obj(item, 'VirtualMachineImageResource',
                                                  enum_modules=AZURE_ENUM_MODULES))
        return results

    def list_publishers(self):
        response = None
        results = []
        try:
            response = self.compute_client.virtual_machine_images.list_publishers(self.location)
        except CloudError:
            pass
        except Exception as exc:
            self.fail("Failed to list publishers: {0}".format(str(exc)))

        if response:
            for item in response:
                results.append(self.serialize_obj(item, 'VirtualMachineImageResource',
                                                  enum_modules=AZURE_ENUM_MODULES))
        return results


def main():
    AzureRMVirtualMachineImageInfo()


if __name__ == '__main__':
    main()
