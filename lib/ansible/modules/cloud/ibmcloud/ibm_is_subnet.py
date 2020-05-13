#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_is_subnet
short_description: Configure IBM Cloud 'ibm_is_subnet' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_is_subnet' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    network_acl:
        description:
            - None
        required: False
        type: str
    vpc:
        description:
            - (Required for new resource) VPC instance ID
        required: False
        type: str
    ipv4_cidr_block:
        description:
            - IPV4 subnet - CIDR block
        required: False
        type: str
    public_gateway:
        description:
            - Public Gateway of the subnet
        required: False
        type: str
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
    resource_name:
        description:
            - The name of the resource
        required: False
        type: str
    resource_crn:
        description:
            - The crn of the resource
        required: False
        type: str
    resource_status:
        description:
            - The status of the resource
        required: False
        type: str
    ipv6_cidr_block:
        description:
            - None
        required: False
        type: str
    available_ipv4_address_count:
        description:
            - None
        required: False
        type: str
    total_ipv4_address_count:
        description:
            - None
        required: False
        type: int
    name:
        description:
            - (Required for new resource) Subnet name
        required: False
        type: str
    zone:
        description:
            - (Required for new resource) Subnet zone info
        required: False
        type: str
    resource_group:
        description:
            - None
        required: False
        type: str
    ip_version:
        description:
            - Subnet IP version
        required: False
        type: str
        default: ipv4
    resource_group_name:
        description:
            - The resource group name in which resource is provisioned
        required: False
        type: str
    id:
        description:
            - (Required when updating or destroying existing resource) IBM Cloud Resource ID.
        required: False
        type: str
    state:
        description:
            - State of resource
        choices:
            - available
            - absent
        default: available
        required: False
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
    ('vpc', 'str'),
    ('name', 'str'),
    ('zone', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'network_acl',
    'vpc',
    'ipv4_cidr_block',
    'public_gateway',
    'status',
    'resource_controller_url',
    'resource_name',
    'resource_crn',
    'resource_status',
    'ipv6_cidr_block',
    'available_ipv4_address_count',
    'total_ipv4_address_count',
    'name',
    'zone',
    'resource_group',
    'ip_version',
    'resource_group_name',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    network_acl=dict(
        required=False,
        type='str'),
    vpc=dict(
        required=False,
        type='str'),
    ipv4_cidr_block=dict(
        required=False,
        type='str'),
    public_gateway=dict(
        required=False,
        type='str'),
    status=dict(
        required=False,
        type='str'),
    resource_controller_url=dict(
        required=False,
        type='str'),
    resource_name=dict(
        required=False,
        type='str'),
    resource_crn=dict(
        required=False,
        type='str'),
    resource_status=dict(
        required=False,
        type='str'),
    ipv6_cidr_block=dict(
        required=False,
        type='str'),
    available_ipv4_address_count=dict(
        required=False,
        type='str'),
    total_ipv4_address_count=dict(
        required=False,
        type='int'),
    name=dict(
        required=False,
        type='str'),
    zone=dict(
        required=False,
        type='str'),
    resource_group=dict(
        required=False,
        type='str'),
    ip_version=dict(
        default='ipv4',
        type='str'),
    resource_group_name=dict(
        required=False,
        type='str'),
    id=dict(
        required=False,
        type='str'),
    state=dict(
        type='str',
        required=False,
        default='available',
        choices=(['available', 'absent'])),
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

    # New resource required arguments checks
    missing_args = []
    if module.params['id'] is None:
        for arg, _ in TL_REQUIRED_PARAMETERS:
            if module.params[arg] is None:
                missing_args.append(arg)
        if missing_args:
            module.fail_json(msg=(
                "missing required arguments: " + ", ".join(missing_args)))

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
        resource_type='ibm_is_subnet',
        tf_type='resource',
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
