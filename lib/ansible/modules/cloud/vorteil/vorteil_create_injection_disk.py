#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019 Wilhelm, Wonigkeit (wilhelm.wonigkeit@vorteil.io)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vorteil_create_injection_disk

short_description: Create the actual disk and store to location or return location only

version_added: "2.10"

description:
    - Create the disk image or location of disk
    - This is step 3 out of 3 in the disk build process with injection

options:
    injection_uuiduri:
        description:
            - Dict object created using the vorteil_create_injection_uri call
        required: true
        type: dict
    repo_disktype:
        description:
            - Disk type to be built
        required: true
        type: str
        choices: ["gcp", "ova", "raw", "stream-optimized-disk", "vhd", "vmdk"]
    disk_directory:
        description:
            - Directory where the disk is going to be stored
        required: true
        type: str
notes:
    - The built disk image will be saved to {disk_directory}/{repo_bucket}-{repo_app}-{timestamp()}-.{repo_disktype}
    - Vorteil.io repos that require permission will require a authentication key to login
    - Please set your repo_key to login.

extends_documentation_fragment:
    - vorteil
    - vorteil.bucket
    - vorteil.app

author:
    - Wilhelm Wonigkeit (@bigwonig)
    - Jon Alfaro (@jalfvort)

requirements: 
    - requests
    - toml
    - Vorteil >=3.0.6
'''

EXAMPLES = r'''
- name: get the disk from the injection URI
  vorteil_create_injection_disk:
    repo_key: "{{ var_repo_key }}"
    repo_address: "{{ var_repo_address }}"
    repo_port: "{{ var_repo_port }}"
    repo_proto: "{{ var_repo_proto }}"
    repo_bucket: '{{ var_bucket }}'
    repo_app: '{{ var_app }}'
    injection_uuiduri: '{{ geturicreateresponse }}'
    repo_disktype: "{{ var_repo_disktype }}"
    inject_directory: "/tmp/"
'''

RETURN = r'''
results:
    description:
    - Returns two properties
    - 1) The file location of the built disk
    - 2) The file name of the built disk
    returned: success
    type: dict
    sample:
        {
            "file_location": "/tmp/Vorteil-gnatsd-1573182184.8061945.ova",
            "file_name": "Vorteil-gnatsd-1573182184.8061652.ova"
        }
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vorteil import VorteilClient


def main():

    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        repo_key=dict(type='str', required=False),
        repo_address=dict(type='str', required=True),
        repo_proto=dict(type='str', choices=['http', 'https'], default='http'),
        repo_port=dict(type='str', required=False),
        repo_bucket=dict(type='str', required=True),
        repo_app=dict(type='str', required=True),
        injection_uuiduri=dict(type='dict', required=True),
        repo_disktype=dict(
            type='str',
            choices=['gcp', 'ova', 'raw', 'stream-optimized-disk', 'vhd', 'vmdk'],
            required=True),
        disk_directory=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    # Init vorteil client
    vorteil_client = VorteilClient(module)

    # set repo_cookie if repo_key is provided
    if module.params['repo_key'] is not None:
        cookie_response, is_error = vorteil_client.set_repo_cookie()
        if is_error:
            module.fail_json(msg="Failed to retrieve cookie", meta=cookie_response)

    # Create the injection URI
    disk_response, is_error = vorteil_client.create_injection_disk()

    if is_error:
        module.fail_json(msg="Failed to create the disk from the URI", meta=disk_response)
    else:
        module.exit_json(changed=False, response=disk_response)


if __name__ == '__main__':
    main()
