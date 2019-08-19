#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 NTT Communications Cloud Infrastructure Services
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ntt_mcp_image_info
short_description: Get available server images information
description:
    - Get available server images information
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: false
        default: na
        choices:
          - Valid values can be found in module_utils/ntt_mcp_config.py under APIENDPOINTS
    datacenter:
        description:
            - The datacenter name e.g NA9
        required: false
    id:
        description:
            - The GUID of the image, supports wildcard matching with "*" e.g. "*ffff*"
        required: false
    name:
        description:
            - The name of the infrastructure entity, supports wildcard matching with "*" e.g. "*Centos*"
        required: false
    family:
        description:
            - The OS family name of the infrastructure entity
        required: false
        choices:
            - UNIX, WINDOWS
    custom_image:
        description:
            - Is this a customer import image
        required: false
        default: false
        choices: [true, false]
notes:
    - N/A
'''

EXAMPLES = '''
# List all available Centos operating systems
- name: Get a list of all Centos VM images in NA9
  ntt_mcp_image_facts:
    region: na
    datacenter: NA9
    name: "*CENTOS*"
# Get all customer images in the NA9 MCP
- name: Get a list of the VM images in NA9
  ntt_mcp_image_facts:
    region: na
    datacenter: NA9
    customer_image: True
'''

RETURN = '''
data:
    description: dict of returned Objects
    type: complex
    returned: success
    contains:
        count:
            description: The total count of found/returned objects
            returned: success
            type: int
            sample: 5
        image:
            description: A list of images
            returned: success
            type: complex
            contains:
                cpu:
                    description: The default CPU specifications for the image
                    type: complex
                    contains:
                        coresPerSocket:
                            description: # of cores per CPU socket
                            type: int
                            sample: 1
                        count:
                            description: The number of CPUs
                            type: int
                            sample: 2
                        speed:
                            description: The CPU reservation to be applied
                            type: str
                            sample: "STANDARD"
                createTime:
                    description: The creation date of the image
                    type: str
                    sample: "2019-01-14T11:12:31.000Z"
                datacenterId:
                    description: The MCP id for this image
                    type: str
                    sample: "NA9"
                description:
                    description: The description for the image
                    type: str
                    sample: "My OS Image"
                guest:
                    description: Custom VM attributes for the image
                    type: complex
                    contains:
                        operatingSystem:
                            description: The operating system attributes for this image
                            type: complex
                            contains:
                                displayName:
                                    description: The name of the OS
                                    type: str
                                    sample: "CENTOS7/64"
                                family:
                                    description: The OS family e.g. UNIX or WINDOWS
                                    type: str
                                    sample: "UNIX"
                                id:
                                    description: OS ID
                                    type: str
                                    sample: "CENTOS764"
                                osUnitsGroupId:
                                    description: The OS billing group
                                    type: str
                                    sample: "CENTOS"
                        osCustomization:
                            description:  Does this OS support guest OS cusomtizations
                            type: bool
                            sample: true
                id:
                    description: OS ID
                    type: str
                    sample: "CENTOS764"
                memoryGb:
                    description: The default memory setting for this image in GB
                    type: int
                    sample: 4
                name:
                    description: The common name for the Image
                    type: str
                    sample: "CentOS 7 64-bit 2 CPU"
                osImageKey:
                    description: Internal image identifier
                    type: str
                    sample: "T-CENT-7-64-2-4-10"
                scsiController:
                    description: SCSI controller and disk configuration for the image
                    type: complex
                    contains:
                        adapterType:
                            description: The name of the adapter
                            type: str
                            sample: "LSI_LOGIC_SAS"
                        busNumber:
                            description: The SCSI bus number
                            type: int
                            sample: 1
                        disk:
                            description: List of disks associated with this image
                            type: complex
                            contains:
                                id:
                                    description: The disk id
                                    type: str
                                    sample: "112b7faa-ffff-ffff-ffff-dc273085cbe4"
                                scsiId:
                                    description: The id of the disk on the SCSI controller
                                    type: int
                                    sample: 0
                                sizeGb:
                                    description: The initial size of the disk in GB
                                    type: int
                                    sample: 10
                                speed:
                                    description: The disk speed
                                    type: str
                                    sample: "STANDARD"
                        id:
                            description: The SCSI controller id
                            type: str
                            sample: "112b7faa-ffff-ffff-ffff-dc273085cbe4"
                        key:
                            description: Internal use
                            type: int
                            sample: 1000
                softwareLabel:
                    description:  List of associated labels
                    type: complex
                    contains:
                        type: str
                        sample: "MSSQL2012R2E"
                tag:
                    description: List of associated tags
                    type: complex
                    contains:
                        tagKeyId:
                            description: GUID of the tag
                            type: str
                            sample: "112b7faa-ffff-ffff-ffff-dc273085cbe4"
                        tagKeyName:
                            description: Human readable key name
                            type: str
                            sample: "Owner"
                        value:
                            description: The value of the key
                            type: str
                            sample: "Someone"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def get_image(module, client):
    """
    List images filtered by optional parameters from the Ansible arguments
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: List of image objects
    """
    return_data = return_object('image')
    image_id = module.params['id']
    image_name = module.params['name']
    os_family = module.params['family']
    datacenter = module.params['datacenter']
    customer_image = module.params['customer_image']

    try:
        if customer_image:
            result = client.list_customer_image(datacenter_id=datacenter, image_id=image_id, image_name=image_name, os_family=os_family)
        else:
            result = client.list_image(datacenter_id=datacenter, image_id=image_id, image_name=image_name, os_family=os_family)
    except NTTMCPAPIException as exc:
        module.fail_json(msg='Could not get a list of images - {0}'.format(exc.message))
    try:
        if customer_image:
            return_data['count'] = result['totalCount']
            return_data['image'] = result['customerImage']
        else:
            return_data['count'] = result['totalCount']
            return_data['image'] = result['osImage']
    except KeyError:
        pass

    module.exit_json(data=return_data)


def main():
    """
    Main function
    :returns: Image Information
    """
    ntt_mcp_regions = get_ntt_mcp_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=ntt_mcp_regions),
            datacenter=dict(required=False, type='str'),
            id=dict(required=False, type='str'),
            name=dict(required=False, type='str'),
            family=dict(required=False, choices=['UNIX', 'WINDOWS']),
            customer_image=dict(default=False, type='bool')
        ),
        supports_check_mode=True
    )

    credentials = get_credentials()

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    # Create the API client
    client = NTTMCPClient((credentials[0], credentials[1]), module.params['region'])

    get_image(module=module, client=client)


if __name__ == '__main__':
    main()
