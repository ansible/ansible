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
module: vorteil_provision_injection_config

short_description: Create the actual configuration TOML for injection URI for provisioned disk

version_added: "2.10"

description:
    - Inject a configuration into the URI to be used for the provisioning disk building process
    - The configuration can be passed as a JSON object, it will be converted to the appropriate TOML configurations
    - For a sample JSON/TOML configuration, use the vorteil_get_sample_vcfg call which will pass back a example
     vcfg [Vorteil Configuration].
    - This is step 2 out of 2 in the disk build process with injection
    - Once this module is completed the built disk will provision to a configured Vorteil.io provisioner

options:
    use_default_kernel:
        description:
            - Boolean value, uses the repo configured default kernel (default=True)
        required: false
        default: true
        type: bool
    injection_json:
        description:
            - Configuration to inject into the URI - can be passed as JSON
        required: true
        type: dict
    injection_uuiduri:
        description:
            - Dict object created using the vorteil_create_injection_uri call
        required: true
        type: dict

extends_documentation_fragment:
    - vorteil

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
- name: insert the configuration into the injection URI
  vorteil_provision_injection_config:
    repo_key: "{{ var_repo_key }}"
    repo_address: "{{ var_repo_address }}"
    repo_port: "{{ var_repo_port }}"
    repo_proto: "{{ var_repo_proto }}"
    use_default_kernel: False
    injection_json: {
                            'program' : [
                                {
                                    'args' : "-XzaArgs",
                                    'binary' : "/usr/bin/java",
                                    'env' : ["HOME=/export/home/java", "JAVA_HOME=/usr/lib/jre/"]
                                },
                                {
                                    'args' : "-QyRArgs",
                                    'binary' : "/acme",
                                    'env' : ["HOME=/export/home/acme", "ACME_HOME=/usr/bin/"]
                                }
                            ],
                            'info' : {
                                'author' : "Ansible Test Script",
                                'url' : "www.vorteil.io",
                                'version' : "1.0.1"
                            },
                            'vm' : {
                                'cpus' : 1,
                                'disk-size' : "512 MiB",
                                'ram' : "128 MiB"
                            },
                            'network' : [
                                {
                                    'gateway' : "192.168.1.1",
                                    'ip' : "192.168.1.10",
                                    'mask' : "255.255.255.0",
                                },
                                {
                                    'gateway' : "10.1.1.1",
                                    'ip' : "10.1.1.10",
                                    'mask' : "255.255.255.0",
                                }
                            ],
                            'route' : [
                                {
                                    'destination' : "192.0.0.0/8",
                                    'gateway' : "192.168.1.1",
                                    'interface' : "eth0"
                                },
                                {
                                    'destination' : "10.0.0.0/8",
                                    'gateway' : "10.1.1.1",
                                    'interface' : "eth1"
                                }
                            ]
                        }
    injection_uuiduri: "{{ geturicreateresponse }}"
'''

RETURN = r'''
results:
    description:
    - A status message which indicates whether or not the configuration injection was successfull
    returned: success
    type: str
    sample: "Success"
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
        use_default_kernel=dict(type='bool', default=True, required=False),
        injection_json=dict(type='dict', required=True),
        injection_uuiduri=dict(type='dict', required=True)
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
    config_response, is_error = vorteil_client.provision_injection_config()

    if is_error:
        module.fail_json(msg="Failed to push the configuration to the URI", meta=config_response)
    else:
        module.exit_json(changed=False, response=config_response)


if __name__ == '__main__':
    main()
