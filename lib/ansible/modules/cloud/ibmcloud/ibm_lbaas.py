#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_lbaas
short_description: Configure IBM Cloud 'ibm_lbaas' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_lbaas' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    description:
        description:
            - Description of a load balancer.
        required: False
        type: str
    name:
        description:
            - (Required for new resource) The load balancer's name.
        required: False
        type: str
    subnets:
        description:
            - (Required for new resource) The subnet where this Load Balancer will be provisioned.
        required: False
        type: list
        elements: int
    status:
        description:
            - The operation status 'ONLINE' or 'OFFLINE' of a load balancer.
        required: False
        type: str
    datacenter:
        description:
            - None
        required: False
        type: str
    ssl_ciphers:
        description:
            - None
        required: False
        type: list
        elements: str
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
    resource_status:
        description:
            - The status of the resource
        required: False
        type: str
    type:
        description:
            - Specifies if a load balancer is public or private
        required: False
        type: str
        default: PUBLIC
    vip:
        description:
            - The virtual ip address of this load balancer
        required: False
        type: str
    use_system_public_ip_pool:
        description:
            - "in public loadbalancer - Public IP address allocation done by system public IP pool or public subnet."
        required: False
        type: bool
    protocols:
        description:
            - Protocols to be assigned to this load balancer.
        required: False
        type: list
        elements: dict
    wait_time_minutes:
        description:
            - None
        required: False
        type: int
        default: 90
    health_monitors:
        description:
            - None
        required: False
        type: list
        elements: dict
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
    ('subnets', 'list'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'description',
    'name',
    'subnets',
    'status',
    'datacenter',
    'ssl_ciphers',
    'resource_controller_url',
    'resource_name',
    'resource_status',
    'type',
    'vip',
    'use_system_public_ip_pool',
    'protocols',
    'wait_time_minutes',
    'health_monitors',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    description=dict(
        required=False,
        type='str'),
    name=dict(
        required=False,
        type='str'),
    subnets=dict(
        required=False,
        elements='',
        type='list'),
    status=dict(
        required=False,
        type='str'),
    datacenter=dict(
        required=False,
        type='str'),
    ssl_ciphers=dict(
        required=False,
        elements='',
        type='list'),
    resource_controller_url=dict(
        required=False,
        type='str'),
    resource_name=dict(
        required=False,
        type='str'),
    resource_status=dict(
        required=False,
        type='str'),
    type=dict(
        default='PUBLIC',
        type='str'),
    vip=dict(
        required=False,
        type='str'),
    use_system_public_ip_pool=dict(
        required=False,
        type='bool'),
    protocols=dict(
        required=False,
        elements='',
        type='list'),
    wait_time_minutes=dict(
        default=90,
        type='int'),
    health_monitors=dict(
        required=False,
        elements='',
        type='list'),
    id=dict(
        required=False,
        type='str'),
    state=dict(
        type='str',
        required=False,
        default='available',
        choices=(['available', 'absent'])),
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

    # New resource required arguments checks
    missing_args = []
    if module.params['id'] is None:
        for arg, _ in TL_REQUIRED_PARAMETERS:
            if module.params[arg] is None:
                missing_args.append(arg)
        if missing_args:
            module.fail_json(msg=(
                "missing required arguments: " + ", ".join(missing_args)))

    result = ibmcloud_terraform(
        resource_type='ibm_lbaas',
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
