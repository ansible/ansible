#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_is_vpn_gateway_connection
short_description: Configure IBM Cloud 'ibm_is_vpn_gateway_connection' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_is_vpn_gateway_connection' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    name:
        description:
            - (Required for new resource) VPN Gateway connection name
        required: False
        type: str
    vpn_gateway:
        description:
            - (Required for new resource) VPN Gateway info
        required: False
        type: str
    admin_state_up:
        description:
            - VPN gateway connection admin state
        required: False
        type: bool
        default: False
    local_cidrs:
        description:
            - VPN gateway connection local CIDRs
        required: False
        type: list
        elements: str
    action:
        description:
            - Action detection for dead peer detection action
        required: False
        type: str
        default: none
    peer_address:
        description:
            - (Required for new resource) VPN gateway connection peer address
        required: False
        type: str
    preshared_key:
        description:
            - (Required for new resource) vpn gateway
        required: False
        type: str
    peer_cidrs:
        description:
            - VPN gateway connection peer CIDRs
        required: False
        type: list
        elements: str
    interval:
        description:
            - Interval for dead peer detection interval
        required: False
        type: int
        default: 30
    timeout:
        description:
            - Timeout for dead peer detection
        required: False
        type: int
        default: 120
    ipsec_policy:
        description:
            - IP security policy for vpn gateway connection
        required: False
        type: str
    ike_policy:
        description:
            - VPN gateway connection IKE Policy
        required: False
        type: str
    status:
        description:
            - VPN gateway connection status
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
    ('name', 'str'),
    ('vpn_gateway', 'str'),
    ('peer_address', 'str'),
    ('preshared_key', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'name',
    'vpn_gateway',
    'admin_state_up',
    'local_cidrs',
    'action',
    'peer_address',
    'preshared_key',
    'peer_cidrs',
    'interval',
    'timeout',
    'ipsec_policy',
    'ike_policy',
    'status',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    name=dict(
        required=False,
        type='str'),
    vpn_gateway=dict(
        required=False,
        type='str'),
    admin_state_up=dict(
        default=False,
        type='bool'),
    local_cidrs=dict(
        required=False,
        elements='',
        type='list'),
    action=dict(
        default='none',
        type='str'),
    peer_address=dict(
        required=False,
        type='str'),
    preshared_key=dict(
        required=False,
        type='str'),
    peer_cidrs=dict(
        required=False,
        elements='',
        type='list'),
    interval=dict(
        default=30,
        type='int'),
    timeout=dict(
        default=120,
        type='int'),
    ipsec_policy=dict(
        required=False,
        type='str'),
    ike_policy=dict(
        required=False,
        type='str'),
    status=dict(
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
        resource_type='ibm_is_vpn_gateway_connection',
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
