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
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ntt_mcp_image
short_description: Import a custom OVF into Cloud Control
description:
    - Import a custom OVF into Cloud Control or delete an existing imported OVF
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: false
        type: str
        default: na
    datacenter:
        description:
            - The datacenter name
        required: false
        type: str
    name:
        description:
            - The name of the infrastructure entity
        required: false
        type: str
    ovf_package:
        description:
            - The name of the manfifest (.mf) file for the OVF package to be imported
            - Note this must exist on the region FTPS server prior to import
            - This is required for 'present' but not for 'absent'
        required: false
        type: str
    guest_customization:
        description:
            - Should guest OS cusomtizations occur. This requires VMWare Tools be installed in the OVF
            - This should be set to False when importing virtual appliances or VNFs
        required: false
        type: bool
        default: true
    description:
        description:
            - The description to be applied in Cloud Control for the image
        required: false
        type: str
    state:
        description:
            - The action to be performed
        required: true
        type: str
        default: present
        choices:
            - present
            - absent
    wait:
        description:
            - Should Ansible wait for the task to complete before continuing
        required: false
        type: bool
        default: true
    wait_time:
        description: The maximum time the Ansible should wait for the task
                     to complete in seconds
        required: false
        type: int
        default: 600
    wait_poll_interval:
        description:
            - The time in between checking the status of the task in seconds
        required: false
        type: int
        default: 15
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: Import an image into NA9
    ntt_mcp_image:
      region: na
      datacenter: NA9
      name: myImage
      ovf_package: "myImage.mf"
      guest_customization: False
      state: present

  - name: Remove an image into NA9
    ntt_mcp_image:
      region: na
      datacenter: NA9
      name: myImage
      state: absent
'''

RETURN = '''
results:
    description: The imported image object
    returned: state == present
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

from time import sleep
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def import_image(module, client):
    """
    Import an image into a data center

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :returns: The import image object
    """
    return_data = return_object('image')
    image_name = module.params['name']
    description = module.params['description']
    ovf_package = module.params['ovf_package']
    datacenter = module.params['datacenter']
    guest_customization = module.params['guest_customization']
    wait = module.params['wait']

    image_id = ''

    if image_name is None or ovf_package is None or datacenter is None:
        module.fail_json(msg='An image name, OVF Package name and datacenter are required.')

    try:
        result = client.import_customer_image(datacenter, ovf_package, image_name, description, guest_customization)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not import the OVF package - {0}'.format(e))

    try:
        image_id = result['info'][0]['value']
    except (KeyError, IndexError) as e:
        module.fail_json(msg='Could not import the OVF package - {0}'.format(result))

    if wait:
        wait_result = wait_for_image_import(module, client, image_id, 'NORMAL')
        if wait_result is None:
            module.fail_json(msg='Could not verify the image import was successful. Check manually')
        return_data['image'].append(wait_result)

    module.exit_json(changed=True, results=return_data.get('image'))


def delete_image(module, client, image):
    """
    Delete an image from a data center

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg image: The image to be deleted
    :returns: A message
    """
    image_exists = True
    time = 0
    wait_time = module.params.get('wait_time')
    wait_poll_interval = module.params.get('wait_poll_interval')
    datacenter = module.params.get('datacenter')
    image_name = image.get('name')

    try:
        client.delete_customer_image(image_id=image.get('id'))
    except NTTMCPAPIException as e:
        module.fail_json(msg='Error deleting the image - {0}'.format(e))

    if module.params['wait']:
        while image_exists and time < wait_time:
            try:
                images = client.list_customer_image(datacenter_id=datacenter, image_name=image_name)
                image_exists = [image for image in images if image.get('name') == image_name]
            except (KeyError, AttributeError, NTTMCPAPIException) as e:
                pass
            sleep(wait_poll_interval)
            time = time + wait_poll_interval

        if image_exists and time >= wait_time:
            module.fail_json(msg='Timeout waiting for the image to be deleted')

    module.exit_json(changed=True, msg='Image {0} has been successfully removed in {1}'.format(image_name, datacenter))


def wait_for_image_import(module, client, image_id, state):
    """
    Wait for an image to import. Polls based on wait_time and wait_poll_interval values.

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg image_id: The UUID of the image being polled
    :arg state: The desired state to wait
    :returns: The import image object
    """
    actual_state = ''
    image = None
    wait_time = module.params['wait_time']
    time = 0
    while actual_state != state and time < wait_time:
        try:
            image = client.get_customer_image(image_id=image_id)
        except NTTMCPAPIException as e:
            module.fail_json(msg='Error: Failed to get the image - %s' % e)
        try:
            actual_state = image['state']
        except (KeyError, IndexError) as e:
            pass
        sleep(module.params['wait_poll_interval'])
        time = time + module.params['wait_poll_interval']

    if not image and time >= wait_time:
        module.fail_json(msg='Timeout waiting for the image to be imported')
    return image


def main():
    """
    Main function

    :returns: Image Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            description=dict(required=False, type='str'),
            ovf_package=dict(required=False, type='str'),
            guest_customization=dict(required=False, default=True, type='bool'),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(required=False, default=True, type='bool'),
            wait_time=dict(required=False, default=600, type='int'),
            wait_poll_interval=dict(required=False, default=15, type='int')
        ),
        supports_check_mode=True
    )

    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))

    image_name = module.params['name']
    datacenter = module.params['datacenter']
    image_exists = None

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    # Create the API client
    client = NTTMCPClient((credentials[0], credentials[1]), module.params['region'])

    # Check if the image already exists
    try:
        images = client.list_customer_image(datacenter_id=datacenter, image_name=image_name)
        if images:
            image_exists = [image for image in images if image.get('name') == image_name][0]
    except (KeyError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='There was an issue connecting to the API: {0}'.format(e))
    except IndexError:
        pass
    if module.params['state'] == 'present':
        if image_exists:
            # Implement check_mode
            if module.check_mode:
                module.exit_json(msg='An image with this name already exists. Existing image is included', data=image_exists)
            module.fail_json(msg='Image name {0} already exists'.format(module.params['name']))
        # Implement check_mode
        if module.check_mode:
            module.exit_json(msg='The image will be imported into Cloud Control')
        import_image(module=module, client=client)
    elif module.params['state'] == 'absent':
        if not image_exists:
            module.exit_json(msg='Image name {0} does not exist'.format(module.params.get('name')))
        # Implement check_mode
        if module.check_mode:
            module.exit_json(msg='This image will be removed from Cloud Control', data=image_exists)
        delete_image(module=module, client=client, image=image_exists)


if __name__ == '__main__':
    main()
