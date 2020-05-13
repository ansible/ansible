#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_is_vpc_info
short_description: Retrieve IBM Cloud 'ibm_is_vpc' resource

version_added: "2.8"

description:
    - Retrieve an IBM Cloud 'ibm_is_vpc' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    classic_access:
        description:
            - None
        required: False
        type: bool
    status:
        description:
            - None
        required: False
        type: str
    resource_controller_url:
        description:
            - The URL of the IBM Cloud dashboard that can be used to explore and view details about this instance
        required: False
        type: str
    resource_group_name:
        description:
            - The resource group name in which resource is provisioned
        required: False
        type: str
    resource_group:
        description:
            - None
        required: False
        type: str
    resource_status:
        description:
            - The status of the resource
        required: False
        type: str
    cse_source_addresses:
        description:
            - None
        required: False
        type: list
        elements: dict
    subnets:
        description:
            - None
        required: False
        type: list
        elements: dict
    default_network_acl:
        description:
            - None
        required: False
        type: str
    name:
        description:
            - None
        required: True
        type: str
    tags:
        description:
            - None
        required: False
        type: list
        elements: str
    resource_name:
        description:
            - The name of the resource
        required: False
        type: str
    crn:
        description:
            - The crn of the resource
        required: False
        type: str
    resource_crn:
        description:
            - The crn of the resource
        required: False
        type: str
    generation:
        description:
            - The generation of Virtual Private Cloud infrastructure
              that you want to use. Supported values are 1 for VPC
              generation 1, and 2 for VPC generation 2 infrastructure.
              If this value is not specified, 2 is used by default. This
              can also be provided via the environment variable
              'IC_GENERATION'.
        default: 2
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
    'classic_access',
    'status',
    'resource_controller_url',
    'resource_group_name',
    'resource_group',
    'resource_status',
    'cse_source_addresses',
    'subnets',
    'default_network_acl',
    'name',
    'tags',
    'resource_name',
    'crn',
    'resource_crn',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    classic_access=dict(
        required=False,
        type='bool'),
    status=dict(
        required=False,
        type='str'),
    resource_controller_url=dict(
        required=False,
        type='str'),
    resource_group_name=dict(
        required=False,
        type='str'),
    resource_group=dict(
        required=False,
        type='str'),
    resource_status=dict(
        required=False,
        type='str'),
    cse_source_addresses=dict(
        required=False,
        elements='',
        type='list'),
    subnets=dict(
        required=False,
        elements='',
        type='list'),
    default_network_acl=dict(
        required=False,
        type='str'),
    name=dict(
        required=True,
        type='str'),
    tags=dict(
        required=False,
        elements='',
        type='list'),
    resource_name=dict(
        required=False,
        type='str'),
    crn=dict(
        required=False,
        type='str'),
    resource_crn=dict(
        required=False,
        type='str'),
    generation=dict(
        type='int',
        required=False,
        fallback=(env_fallback, ['IC_GENERATION']),
        default=2),
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

    # VPC required arguments checks
    if module.params['generation'] == 1:
        missing_args = []
        if module.params['iaas_classic_username'] is None:
            missing_args.append('iaas_classic_username')
        if module.params['iaas_classic_api_key'] is None:
            missing_args.append('iaas_classic_api_key')
        if missing_args:
            module.fail_json(msg=(
                "VPC generation=1 missing required arguments: " +
                ", ".join(missing_args)))
    elif module.params['generation'] == 2:
        if module.params['ibmcloud_api_key'] is None:
            module.fail_json(
                msg=("VPC generation=2 missing required argument: "
                     "ibmcloud_api_key"))

    result = ibmcloud_terraform(
        resource_type='ibm_is_vpc',
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
