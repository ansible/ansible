#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019 Jon, Alfaro (jon.alfaro@vorteil.io)
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
module: vorteil_provision_injection_uri

short_description: Create the configuration injection URI for the provsioning disk build

version_added: "2.10"

description:
    - Create an injection URI to be used for the provisioning disk building process
    - This is step 1 out of 2 in provisioning the output of disk build process with injection
    - A build process will be created and returned with a uri, that can be used for injections.
    - A uuid will also be created and returned to so that the injection can be identified by the build process.
    - A build process is only satisfied when they have been injected at there created uuid.


options:
    repo_provisioner:
        description:
            - Vorteil provisioner configured at Vorteil Repo
            - Disk will be provisioned to this provisioner
        required: true
        type: str
    repo_image_name:
        description:
            - The name of the built disk that will be provisioned.
        required: true
        type: str

extends_documentation_fragment:
    - vorteil
    - vorteil.bucket
    - vorteil.app

author:
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
- name: provision the injection URI
  vorteil_provision_injection_uri:
      repo_address: "{{ var_repo_address }}"
      repo_port: "{{ var_repo_port }}"
      repo_proto: "{{ var_repo_proto }}"
      repo_bucket: '{{ var_bucket }}'
      repo_app: '{{ var_app }}'
      repo_provisioner: "{{ var_repo_provisioner }}"
      repo_image_name: '{{ var_provisioned_image_name }}'
'''

RETURN = r'''
results:
    description:
    - Returns the uri, uuid of the initialized provisioning process, and the job id of this process
    - uri is the endpoint of where to inject to and pull from.
    - uuid is the unique identifer used to set the target of where to inject a configuration to.
    returned: success
    type: dict
    sample:
        {
            "provision": {
                "job": {
                    "id": "job-sqtonz"
                },
                "uri": "eqiefQJhbpwxvtCPqIxeVCsqPsSBzyWWyOTIWjjDLujhVBGYnEBGTQFusIZuzUqX",
                "uuid": "d8b43d43-d9b1-4f21-8397-74347022edcf"
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
        repo_provisioner=dict(type='str', required=True),
        repo_image_name=dict(type='str', required=True)
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

    # Provision the injection URI
    uri_response, is_error = vorteil_client.provision_injection_uri()

    if is_error:
        module.fail_json(msg="Failed to create the injection URI", meta=uri_response)
    else:
        module.exit_json(changed=False, response=uri_response)


if __name__ == '__main__':
    main()
