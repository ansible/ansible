#!/usr/bin/python
#
# Copyright (c) 2019 Liu Qingyi, (@smile37773)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_galleryimageversion_info
version_added: '2.9'
short_description: Get Azure SIG Image Version info.
description:
  - Get info of Azure SIG Image Version.
options:
  resource_group:
    description:
      - The name of the resource group.
    type: str
    required: true
  gallery_name:
    description:
      - >-
        The name of the Shared Image Gallery in which the Image Definition
        resides.
    type: str
    required: true
  gallery_image_name:
    description:
      - >-
        The name of the gallery Image Definition in which the Image Version
        resides.
    type: str
    required: true
  name:
    description:
      - Resource name
    type: str
extends_documentation_fragment:
  - azure
author:
  - Liu Qingyi (@smile37773)

'''

EXAMPLES = '''
- name: List gallery image versions in a gallery image definition.
  azure_rm_galleryimageversion_info:
    resource_group: myResourceGroup
    gallery_name: myGallery
    gallery_image_name: myImage
- name: Get a gallery image version.
  azure_rm_galleryimageversion_info:
    resource_group: myResourceGroup
    gallery_name: myGallery
    gallery_image_name: myImage
    name: myVersion

'''

RETURN = '''
versions:
  description: >-
    A list of dict results where the key is the name of the version
    and the values are the info for that version.
  returned: always
  type: complex
  contains:
    id:
      description:
        - Resource Id
      returned: always
      type: str
      sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups
      /myResourceGroup/providers/Microsoft.Compute/galleries/myGallery/
      images/myImage/versions/myVersion"
    name:
      description:
        - Resource name
      returned: always
      type: str
      sample: "myVersion"
    location:
      description:
        - Resource location
      returned: always
      type: str
      sample: "eastus"
    tags:
      description:
        - Resource tags
      returned: always
      type: dict
      sample: { "tag": "value" }
    publishing_profile:
      description:
        - The publishing profile of a gallery image version.
      type: dict
    provisioning_state:
      description:
        - The current state of the gallery.
      type: str
      sample: "Succeeded"

'''

import time
import json
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.azure_rm_common_rest import GenericRestClient
from copy import deepcopy
try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # handled in azure_rm_common
    pass


class AzureRMGalleryImageVersionsInfo(AzureRMModuleBase):
    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            gallery_name=dict(
                type='str',
                required=True
            ),
            gallery_image_name=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            )
        )

        self.resource_group = None
        self.gallery_name = None
        self.gallery_image_name = None
        self.name = None

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.url = None
        self.status_code = [200]

        self.query_parameters = {}
        self.query_parameters['api-version'] = '2019-03-01'
        self.header_parameters = {}
        self.header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        self.mgmt_client = None
        super(AzureRMGalleryImageVersionsInfo, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        self.mgmt_client = self.get_mgmt_svc_client(GenericRestClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if (self.resource_group is not None and
                self.gallery_name is not None and
                self.gallery_image_name is not None and
                self.name is not None):
            self.results['versions'] = self.get()
        elif (self.resource_group is not None and
              self.gallery_name is not None and
              self.gallery_image_name is not None):
            self.results['versions'] = self.listbygalleryimage()
        return self.results

    def get(self):
        response = None
        results = {}
        # prepare url
        self.url = ('/subscriptions' +
                    '/{{ subscription_id }}' +
                    '/resourceGroups' +
                    '/{{ resource_group }}' +
                    '/providers' +
                    '/Microsoft.Compute' +
                    '/galleries' +
                    '/{{ gallery_name }}' +
                    '/images' +
                    '/{{ image_name }}' +
                    '/versions' +
                    '/{{ version_name }}')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)
        self.url = self.url.replace('{{ gallery_name }}', self.gallery_name)
        self.url = self.url.replace('{{ image_name }}', self.gallery_image_name)
        self.url = self.url.replace('{{ version_name }}', self.name)

        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
            results = json.loads(response.text)
            # self.log('Response : {0}'.format(response))
        except CloudError as e:
            self.log('Could not get info for @(Model.ModuleOperationNameUpper).')

        return self.format_item(results)

    def listbygalleryimage(self):
        response = None
        results = {}
        # prepare url
        self.url = ('/subscriptions' +
                    '/{{ subscription_id }}' +
                    '/resourceGroups' +
                    '/{{ resource_group }}' +
                    '/providers' +
                    '/Microsoft.Compute' +
                    '/galleries' +
                    '/{{ gallery_name }}' +
                    '/images' +
                    '/{{ image_name }}' +
                    '/versions')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)
        self.url = self.url.replace('{{ gallery_name }}', self.gallery_name)
        self.url = self.url.replace('{{ image_name }}', self.gallery_image_name)

        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
            results = json.loads(response.text)
            # self.log('Response : {0}'.format(response))
        except CloudError as e:
            self.log('Could not get info for @(Model.ModuleOperationNameUpper).')

        return [self.format_item(x) for x in results['value']] if results['value'] else []

    def format_item(self, item):
        d = {
            'id': item['id'],
            'name': item['name'],
            'location': item['location'],
            'tags': item.get('tags'),
            'publishing_profile': item['properties']['publishingProfile'],
            'provisioning_state': item['properties']['provisioningState']
        }
        return d


def main():
    AzureRMGalleryImageVersionsInfo()


if __name__ == '__main__':
    main()
