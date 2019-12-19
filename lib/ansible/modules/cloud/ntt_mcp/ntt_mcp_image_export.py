#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Ken Sinfield <ken.sinfield@cis.ntt.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ntt_mcp_image_export
short_description: Export a customer image to an OVF
description:
    - Export a customer image in Cloud Control to an OVF for download
    - For large images, set a higher wait_time to ensure Ansible will wait for the complete export or set wait == False
    - https://docs.mcp-services.net/x/rgMk
version_added: "2.10"
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
        required: true
        type: str
    name:
        description:
            - The name of the image in Cloud Control
        required: true
        type: str
    ovf_name:
        description:
            - The name to be used for the exported OVF packacge
            - The OVF will be available on the FTPS server for this GEO
        required: true
        type: str
    wait:
        description:
            - Should Ansible wait for the task to complete before continuing
        required: false
        type: bool
        default: true
    wait_time:
        description: The maximum time the Ansible should wait for the task to complete in seconds
        required: false
        type: int
        default: 3600
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

  - name: Export an image from NA9
    ntt_mcp_image_export:
      region: na
      datacenter: NA9
      name: myImage
      ovf_name: myImage_export
'''

RETURN = '''
msg:
    description: A helpful message
    returned: always
    type: str
    sample: The image was successfully exported with the export ID 71a365c4-f702-4e3c-ac11-34924aa36bf5
'''

from time import sleep
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def wait_for_image_export(module, client, datacenter, image_name):
    """
    Wait for an image to export. Polls based on wait_time and wait_poll_interval values.

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg datacenter: The datacenter/MCP ID e.g. NA9
    :arg image_id: The UUID of the image being polled
    :returns: The exported image object
    """
    actual_state = False
    image = None
    wait_time = module.params.get('wait_time')
    time = 0
    while not actual_state and time < wait_time:
        # Find the image
        try:
            images = client.list_customer_image(datacenter_id=datacenter, image_name=image_name).get('customerImage')
            if images:
                image = [x for x in images if x.get('name') == image_name][0]
                if not image:
                    module.fail_json(msg='Could not find the image {0}'.format(image_name))
        except (KeyError, AttributeError, IndexError, NTTMCPAPIException) as e:
            module.fail_json(msg='The was an error finding the image: {0}'.format(e))
        try:
            if not image.get('progress'):
                actual_state = True
        except (KeyError, IndexError):
            pass
        sleep(module.params.get('wait_poll_interval'))
        time = time + module.params.get('wait_poll_interval')

    if not image and time >= wait_time:
        module.fail_json(msg='Timeout waiting for the image to be exported')
    return True


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
            ovf_name=dict(required=True, type='str'),
            wait=dict(required=False, default=True, type='bool'),
            wait_time=dict(required=False, default=3600, type='int'),
            wait_poll_interval=dict(required=False, default=15, type='int')
        ),
        supports_check_mode=True
    )

    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))

    image_name = module.params.get('name')
    datacenter = module.params.get('datacenter')
    image = None

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    # Create the API client
    try:
        client = NTTMCPClient(credentials, module.params.get('region'))
    except NTTMCPAPIException as e:
        module.fail_json(msg=e.msg)

    # Check if the image already exists
    try:
        images = client.list_customer_image(datacenter_id=datacenter, image_name=image_name).get('customerImage')
        if images:
            image = [x for x in images if x.get('name') == image_name][0]
            if not image:
                module.fail_json(msg='Could not find the image {0}'.format(image_name))
    except (KeyError, AttributeError, IndexError, NTTMCPAPIException) as e:
        module.fail_json(msg='The was an error finding the image: {0}'.format(e))

    if module.check_mode:
        module.exit_json(msg='The image with ID {0} can be exported to the OVF named {1}'.format(image.get('id'), module.params.get('ovf_name')))

    # Attempt to export
    try:
        result = client.export_image(image_id=image.get('id'), ovf_name=module.params.get('ovf_name'))
        if module.params.get('wait'):
            wait_for_image_export(module, client, datacenter, image_name)
        module.exit_json(changed=True, msg='The image was successfully exported with the export ID {0}'.format(result))
    except NTTMCPAPIException as e:
        module.fail_json(msg='Error exporting the image: {0}'.format(e).replace('"', '\''))


if __name__ == '__main__':
    main()
