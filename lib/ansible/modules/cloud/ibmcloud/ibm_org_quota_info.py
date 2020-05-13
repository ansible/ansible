#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_org_quota_info
short_description: Retrieve IBM Cloud 'ibm_org_quota' resource

version_added: "2.8"

description:
    - Retrieve an IBM Cloud 'ibm_org_quota' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    total_routes:
        description:
            - Defines the total route for organization.
        required: False
        type: int
    memory_limit:
        description:
            - Defines the total memory limit for organization.
        required: False
        type: int
    instance_memory_limit:
        description:
            - Defines the  total instance memory limit for organization.
        required: False
        type: int
    app_tasks_limit:
        description:
            - Defines the total app task limit for organization.
        required: False
        type: int
    total_service_keys:
        description:
            - Defines the total service keys for organization.
        required: False
        type: int
    total_services:
        description:
            - Defines the total services for organization.
        required: False
        type: int
    non_basic_services_allowed:
        description:
            - Define non basic services are allowed for organization.
        required: False
        type: bool
    trial_db_allowed:
        description:
            - Defines trial db are allowed for organization.
        required: False
        type: bool
    app_instance_limit:
        description:
            - Defines the total app instance limit for organization.
        required: False
        type: int
    total_private_domains:
        description:
            - Defines the total private domain limit for organization.v
        required: False
        type: int
    total_reserved_route_ports:
        description:
            - Defines the number of reserved route ports for organization.
        required: False
        type: int
    name:
        description:
            - Org quota name, for example qIBM
        required: True
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
    ('name', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'total_routes',
    'memory_limit',
    'instance_memory_limit',
    'app_tasks_limit',
    'total_service_keys',
    'total_services',
    'non_basic_services_allowed',
    'trial_db_allowed',
    'app_instance_limit',
    'total_private_domains',
    'total_reserved_route_ports',
    'name',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    total_routes=dict(
        required=False,
        type='int'),
    memory_limit=dict(
        required=False,
        type='int'),
    instance_memory_limit=dict(
        required=False,
        type='int'),
    app_tasks_limit=dict(
        required=False,
        type='int'),
    total_service_keys=dict(
        required=False,
        type='int'),
    total_services=dict(
        required=False,
        type='int'),
    non_basic_services_allowed=dict(
        required=False,
        type='bool'),
    trial_db_allowed=dict(
        required=False,
        type='bool'),
    app_instance_limit=dict(
        required=False,
        type='int'),
    total_private_domains=dict(
        required=False,
        type='int'),
    total_reserved_route_ports=dict(
        required=False,
        type='int'),
    name=dict(
        required=True,
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
        resource_type='ibm_org_quota',
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
