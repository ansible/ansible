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
module: vorteil_create_injection_uri

short_description: Create the configuration injection URI for disk build

version_added: "2.10"

description:
    - Create an injection URI to be used for disk building process
    - This is step 1 out of 3 in the disk build process with injection
    - A build process will be created and returned with a uri, that can be used for injections.
    - A uuid will also be created and returned to so that the injection can be identified by the build process.
    - A build process is only satisfied when they have been injected at there created uuid.


options:
    repo_disktype:
        description:
            - Disk type to be built
        required: true
        type: str
        choices: ["gcp", "ova", "raw", "stream-optimized-disk", "vhd", "vmdk"]

notes:
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
- name: create the injection URI
  vorteil_create_injection_uri:
    repo_key: "{{ var_repo_key }}"
    repo_address: "{{ var_repo_address }}"
    repo_port: "{{ var_repo_port }}"
    repo_proto: "{{ var_repo_proto }}"
    repo_bucket: '{{ var_bucket }}'
    repo_app: '{{ var_app }}'
    repo_disktype: "ova"
'''

RETURN = r'''
results:
    description:
    - Returns the uri, uuid of the initialized built process, and the job id of this process
    - uri is the endpoint of where to inject to and pull from.
    - uuid is the unique identifer used to set the target of where to inject a configuration to.
    returned: success
    type: dict
    sample:
        {
            "build": {
                "job": {
                    "id": "job-ieiqpk"
                },
                "uri": "GOpJCKylkDcUrdtEtRbyxFyXLcxFVXAhHLQfaXWRKhTHwCAtpuRDznaIDAFRyiWP",
                "uuid": "8a2e2f16-6591-4773-b2ac-e6c2a2ff52c7"
            }
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
        repo_disktype=dict(
            type='str',
            choices=['gcp', 'ova', 'raw', 'stream-optimized-disk', 'vhd', 'vmdk'],
            required=True)
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
    uri_repsonse, is_error = vorteil_client.create_injection_uri()

    if is_error:
        module.fail_json(msg="Failed to create the injection URI", meta=uri_repsonse)
    else:
        module.exit_json(changed=False, response=uri_repsonse)


if __name__ == '__main__':
    main()
