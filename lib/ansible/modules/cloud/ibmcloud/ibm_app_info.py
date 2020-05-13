#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_app_info
short_description: Retrieve IBM Cloud 'ibm_app' resource

version_added: "2.8"

description:
    - Retrieve an IBM Cloud 'ibm_app' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    space_guid:
        description:
            - Define space guid to which app belongs
        required: True
        type: str
    buildpack:
        description:
            - Buildpack to build the app. 3 options: a) Blank means autodetection; b) A Git Url pointing to a buildpack; c) Name of an installed buildpack.
        required: False
        type: str
    environment_json:
        description:
            - Key/value pairs of all the environment variables to run in your app. Does not include any system or service variables.
        required: False
        type: dict
    route_guid:
        description:
            - Define the route guids which should be bound to the application.
        required: False
        type: list
        elements: str
    health_check_type:
        description:
            - Type of health check to perform.
        required: False
        type: str
    name:
        description:
            - The name for the app
        required: True
        type: str
    package_state:
        description:
            - The state of the application package whether staged, pending etc
        required: False
        type: str
    health_check_http_endpoint:
        description:
            - Endpoint called to determine if the app is healthy.
        required: False
        type: str
    memory:
        description:
            - The amount of memory each instance should have. In megabytes.
        required: False
        type: int
    disk_quota:
        description:
            - The maximum amount of disk available to an instance of an app. In megabytes.
        required: False
        type: int
    service_instance_guid:
        description:
            - Define the service instance guids that should be bound to this application.
        required: False
        type: list
        elements: str
    health_check_timeout:
        description:
            - Timeout in seconds for health checking of an staged app when starting up.
        required: False
        type: int
    instances:
        description:
            - The number of instances
        required: False
        type: int
    state:
        description:
            - The state of the application
        required: False
        type: str
    iaas_classic_username:
        description:
            - (Required when generation = 1) The IBM Cloud Classic
              Infrastructure (SoftLayer) user name. This can also be provided
              via the environment variable 'IAAS_CLASSIC_USERNAME'.
        required: False
    iaas_classic_api_key:
        description:
            - (Required when generation = 1) The IBM Cloud Classic
              Infrastructure API key. This can also be provided via the
              environment variable 'IAAS_CLASSIC_API_KEY'.
        required: False
    region:
        description:
            - The IBM Cloud region where you want to create your
              resources. If this value is not specified, us-south is
              used by default. This can also be provided via the
              environment variable 'IC_REGION'.
        default: us-south
        required: False
    ibmcloud_api_key:
        description:
            - The IBM Cloud API key to authenticate with the IBM Cloud
              platform. This can also be provided via the environment
              variable 'IC_API_KEY'.
        required: True

author:
    - Jay Carman (@jaywcarman)
'''

# Top level parameter keys required by Terraform module
TL_REQUIRED_PARAMETERS = [
    ('space_guid', 'str'),
    ('name', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'space_guid',
    'buildpack',
    'environment_json',
    'route_guid',
    'health_check_type',
    'name',
    'package_state',
    'health_check_http_endpoint',
    'memory',
    'disk_quota',
    'service_instance_guid',
    'health_check_timeout',
    'instances',
    'state',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    space_guid=dict(
        required=True,
        type='str'),
    buildpack=dict(
        required=False,
        type='str'),
    environment_json=dict(
        required=False,
        type='dict'),
    route_guid=dict(
        required=False,
        elements='',
        type='list'),
    health_check_type=dict(
        required=False,
        type='str'),
    name=dict(
        required=True,
        type='str'),
    package_state=dict(
        required=False,
        type='str'),
    health_check_http_endpoint=dict(
        required=False,
        type='str'),
    memory=dict(
        required=False,
        type='int'),
    disk_quota=dict(
        required=False,
        type='int'),
    service_instance_guid=dict(
        required=False,
        elements='',
        type='list'),
    health_check_timeout=dict(
        required=False,
        type='int'),
    instances=dict(
        required=False,
        type='int'),
    state=dict(
        required=False,
        type='str'),
    iaas_classic_username=dict(
        type='str',
        no_log=True,
        fallback=(env_fallback, ['IAAS_CLASSIC_USERNAME']),
        required=False),
    iaas_classic_api_key=dict(
        type='str',
        no_log=True,
        fallback=(env_fallback, ['IAAS_CLASSIC_API_KEY']),
        required=False),
    region=dict(
        type='str',
        fallback=(env_fallback, ['IC_REGION']),
        default='us-south'),
    ibmcloud_api_key=dict(
        type='str',
        no_log=True,
        fallback=(env_fallback, ['IC_API_KEY']),
        required=True)
)


def run_module():
    from ansible.module_utils.basic import AnsibleModule

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    result = ibmcloud_terraform(
        resource_type='ibm_app',
        tf_type='data',
        parameters=module.params,
        ibm_provider_version='1.5.2',
        tl_required_params=TL_REQUIRED_PARAMETERS,
        tl_all_params=TL_ALL_PARAMETERS)

    if result['rc'] > 0:
        module.fail_json(
            msg=Terraform.parse_stderr(result['stderr']), **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
