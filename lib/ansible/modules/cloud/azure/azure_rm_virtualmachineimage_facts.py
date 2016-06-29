#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
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


DOCUMENTATION = '''
---
module: azure_rm_virtualmachineimage_facts

version_added: "2.1"

short_description: Get virtual machine image facts.

description:
    - Get facts for virtual machine images.

options:
    name:
        description:
            - Only show results for a specific security group.
        default: null
        required: false
    location:
        description:
            - Azure location value (ie. westus, eastus, eastus2, northcentralus, etc.). Supplying only a
              location value will yield a list of available publishers for the location.
        required: true
    publisher:
        description:
            - Name of an image publisher. List image offerings associated with a particular publisher.
        default: null
        required: false
    offer:
        description:
            - Name of an image offering. Combine with sku to see a list of available image versions.
        default: null
        required: false
    sku:
        description:
            - Image offering SKU. Combine with offer to see a list of available versions.
        default: null
        required: false
    version:
        description:
            - Specific version number of an image.
        default: null
        required: false

extends_documentation_fragment:
    - azure

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"

'''

EXAMPLES = '''
    - name: Get facts for a specific image
      azure_rm_virtualmachineimage_facts:
        location: eastus
        publisher: OpenLogic
        offer: CentOS
        sku: '7.1'
        version: '7.1.20160308'

    - name: List available versions
      azure_rm_virtualmachineimage_facts:
        location: eastus
        publisher: OpenLogic
        offer: CentOS
        sku: '7.1'

    - name: List available offers
      azure_rm_virtualmachineimage_facts:
        location: eastus
        publisher: OpenLogic

    - name: List available publishers
      azure_rm_virtualmachineimage_facts:
        location: eastus

'''

RETURN = '''
azure_vmimages:
    description: List of image dicts.
    returned: always
    type: list
    example: []
'''

from ansible.module_utils.basic import *
from ansible.module_utils.azure_rm_common import *

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
except:
    # This is handled in azure_rm_common
    pass

AZURE_ENUM_MODULES = ['azure.mgmt.compute.models.compute_management_client_enums']

class AzureRMVirtualMachineImageFacts(AzureRMModuleBase):

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
            ansible_facts=dict(azure_vmimages=[])
        )

        self.location = None
        self.publisher = None
        self.offer = None
        self.sku = None
        self.version = None

        super(AzureRMVirtualMachineImageFacts, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.location and self.publisher and self.offer and self.sku and self.version:
            self.results['ansible_facts']['azure_vmimages'] = self.get_item()
        elif self.location and self.publisher and self.offer and self.sku:
            self.results['ansible_facts']['azure_vmimages'] = self.list_images()
        elif self.location and self.publisher:
            self.results['ansible_facts']['azure_vmimages'] = self.list_offers()
        elif self.location:
            self.results['ansible_facts']['azure_vmimages'] = self.list_publishers()

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
    AzureRMVirtualMachineImageFacts()

if __name__ == '__main__':
    main()

