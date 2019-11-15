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
module: vorteil_list_buckets

short_description: List all of the buckets configured in the repository

version_added: "2.10"

description:
    - Gets a list of all the buckets within the Vorteil repo.

extends_documentation_fragment:
    - vorteil

author:
    - Wilhelm Wonigkeit (@bigwonig)
    - Jon Alfaro (@jalfvort)
    
notes:
    - Vorteil.io repos that require permission will require a authentication key to login
    - Please set your repo_key to login.

requirements: 
    - requests
    - toml
    - Vorteil >=3.0.6
'''

EXAMPLES = r'''
- name: List Vorteil repo buckets
  vorteil_list_buckets:
    repo_key: "{{ var_repo_key }}"
    repo_address: "{{ var_repo_address }}"
    repo_port : "{{ var_repo_port }}"
    repo_proto : "{{ var_repo_proto }}"
'''

RETURN = r'''
buckets:
    description:
    - List of buckets in the Vorteil repository
    returned: success
    type: list
    sample:
        [
            {
                "node": {
                    "name": "blog"
                }
            },
            {
                "node": {
                    "name": "vorteil"
                }
            },
            {
                "node": {
                    "name": "Sandbox"
                }
            },
            {
                "node": {
                    "name": "Testing"
                }
            }
        ]
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vorteil import VorteilClient
from ansible.module_utils._text import to_native


def main():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        repo_key=dict(type='str', required=False),
        repo_address=dict(type='str', required=True),
        repo_proto=dict(type='str', choices=['http', 'https'], default='http'),
        repo_port=dict(type='str', required=False)
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

    # Get the list of buckets in the repository
    bucket_response, is_error = vorteil_client.list_buckets()
    if is_error:
        module.fail_json(
            msg="Failed to retrieve bucket list",
            meta=bucket_response,
            exception=traceback.format_exc())
    else:
        module.exit_json(changed=False, response=bucket_response)


if __name__ == '__main__':
    main()
