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
module: vorteil_get_app
short_description: Get the configuration settings for a specific application in a bucket
description:
    - Get the configuration settings for a specific application in a bucket
    - Configuration settings are passed as an Array in the playbook
    - Configuration settings can be ['app', 'author', 'programs', 'cpus', 'description',
     'diskSize', 'kernel', 'memory', 'summary', 'totalNICs', 'url', 'version']
    - If no configuration parameters are passed, all are returned
version_added: "2.10"
options:
    repo_app_attr:
        description:
            - App configuration attributes to return.
            - Configuration settings can be ['app', 'author', 'programs', 'cpus', 'description',
             'diskSize', 'kernel', 'memory', 'summary', 'totalNICs', 'url', 'version'].
        required: false
        type: list

extends_documentation_fragment:
    - vorteil
    - vorteil.bucket
    - vorteil.app
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
- name: Get the configuration for an application in the repo
  vorteil_get_app:
    repo_key: "{{ var_repo_key }}"
    repo_address: "{{ var_repo_address }}"
    repo_port : "{{ var_repo_port }}"
    repo_proto : "{{ var_repo_proto }}"
    repo_bucket : "{{ var_bucket }}"
    repo_app : "{{ var_app }}"

- name: Get the configuration for an application in the repo
  vorteil_get_app:
    repo_key: "{{ var_repo_key }}"
    repo_address: "{{ var_repo_address }}"
    repo_port : "{{ var_repo_port }}"
    repo_proto : "{{ var_repo_proto }}"
    repo_bucket : "{{ var_bucket }}"
    repo_app : "{{ var_app }}"
    repo_app_attr: ['app', 'author', 'programs', 'cpus', 'diskSize', 'kernel', 'memory', 'summary']
'''

RETURN = r'''
results:
    description:
    - dict with the list of configuration settings for the app in the specific bucket in the Vorteil repository
    returned: success
    type: dict
    sample:
        {
            "packageConfig": {
                "info": {
                    "app": "CockroachDB",
                    "author": "vorteil.io",
                    "binaryArgs": null,
                    "cpus": 1,
                    "diskSize": 1024,
                    "kernel": "1.0.2",
                    "memory": 512,
                    "summary": "CockroachDB. Keep your services running and your customers happy with a database that
                    automatically scales, rebalances, and repairs itself. And with CockroachDB\u2019s distributed SQL
                    engine and ACID transactions, your business can grow without ever manually sharding.",
                    "totalNICs": 0,
                    "url": "https://www.cockroachlabs.com",
                    "version": "1.1.5"
                }
            },
            "bucket": "Development",
            "app": "cockroachdb"
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
        repo_app_attr=dict(type='list', required=False)
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

    # Get the list of applications in a specific bucket in the repository
    app_repsonse, is_error = vorteil_client.get_app()

    if is_error:
        module.fail_json(msg="Failed to retrieve application list", meta=app_repsonse)
    else:
        module.exit_json(changed=False, response=app_repsonse)


if __name__ == '__main__':
    main()
