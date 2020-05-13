#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_lb_vpx_service
short_description: Configure IBM Cloud 'ibm_lb_vpx_service' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_lb_vpx_service' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    tags:
        description:
            - list of tags associated with the resource
        required: False
        type: list
        elements: str
    destination_port:
        description:
            - (Required for new resource) Destination Port number
        required: False
        type: int
    connection_limit:
        description:
            - (Required for new resource) Number of connections limit
        required: False
        type: int
    destination_ip_address:
        description:
            - (Required for new resource) Destination IP Address
        required: False
        type: str
    weight:
        description:
            - (Required for new resource) Weight value
        required: False
        type: int
    health_check:
        description:
            - (Required for new resource) Health check info
        required: False
        type: str
    usip:
        description:
            - usip info
        required: False
        type: str
        default: NO
    vip_id:
        description:
            - (Required for new resource) VIP id
        required: False
        type: str
    name:
        description:
            - (Required for new resource) name
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
    ('destination_port', 'int'),
    ('connection_limit', 'int'),
    ('destination_ip_address', 'str'),
    ('weight', 'int'),
    ('health_check', 'str'),
    ('vip_id', 'str'),
    ('name', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'tags',
    'destination_port',
    'connection_limit',
    'destination_ip_address',
    'weight',
    'health_check',
    'usip',
    'vip_id',
    'name',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    tags=dict(
        required=False,
        elements='',
        type='list'),
    destination_port=dict(
        required=False,
        type='int'),
    connection_limit=dict(
        required=False,
        type='int'),
    destination_ip_address=dict(
        required=False,
        type='str'),
    weight=dict(
        required=False,
        type='int'),
    health_check=dict(
        required=False,
        type='str'),
    usip=dict(
        default='NO',
        type='str'),
    vip_id=dict(
        required=False,
        type='str'),
    name=dict(
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
        resource_type='ibm_lb_vpx_service',
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
