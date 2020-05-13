#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_container_vpc_alb
short_description: Configure IBM Cloud 'ibm_container_vpc_alb' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_container_vpc_alb' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    enable:
        description:
            - Enable the ALB instance in the cluster
        required: False
        type: bool
    name:
        description:
            - ALB name
        required: False
        type: str
    resize:
        description:
            - boolean value to resize the albs
        required: False
        type: bool
    state_:
        description:
            - ALB state
        required: False
        type: str
    status:
        description:
            - Status of the ALB
        required: False
        type: str
    zone:
        description:
            - Zone info.
        required: False
        type: str
    alb_id:
        description:
            - (Required for new resource) ALB ID
        required: False
        type: str
    cluster:
        description:
            - cluster id
        required: False
        type: str
    load_balancer_hostname:
        description:
            - Load balancer host name
        required: False
        type: str
    alb_type:
        description:
            - Type of the ALB
        required: False
        type: str
    disable_deployment:
        description:
            - Disable the ALB instance in the cluster
        required: False
        type: bool
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
    ('alb_id', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'enable',
    'name',
    'resize',
    'state_',
    'status',
    'zone',
    'alb_id',
    'cluster',
    'load_balancer_hostname',
    'alb_type',
    'disable_deployment',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    enable=dict(
        required=False,
        type='bool'),
    name=dict(
        required=False,
        type='str'),
    resize=dict(
        required=False,
        type='bool'),
    state_=dict(
        required=False,
        type='str'),
    status=dict(
        required=False,
        type='str'),
    zone=dict(
        required=False,
        type='str'),
    alb_id=dict(
        required=False,
        type='str'),
    cluster=dict(
        required=False,
        type='str'),
    load_balancer_hostname=dict(
        required=False,
        type='str'),
    alb_type=dict(
        required=False,
        type='str'),
    disable_deployment=dict(
        required=False,
        type='bool'),
    id=dict(
        required=False,
        type='str'),
    state=dict(
        type='str',
        required=False,
        default='available',
        choices=(['available', 'absent'])),
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
        resource_type='ibm_container_vpc_alb',
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
