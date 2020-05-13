#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_ipsec_vpn
short_description: Configure IBM Cloud 'ibm_ipsec_vpn' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_ipsec_vpn' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    phase_two:
        description:
            - None
        required: False
        type: list
        elements: dict
    preshared_key:
        description:
            - Preshared Key data
        required: False
        type: str
    remote_subnet_id:
        description:
            - Remote subnet ID value
        required: False
        type: int
    remote_subnet:
        description:
            - None
        required: False
        type: list
        elements: dict
    datacenter:
        description:
            - (Required for new resource) Datacenter name
        required: False
        type: str
    name:
        description:
            - None
        required: False
        type: str
    phase_one:
        description:
            - None
        required: False
        type: list
        elements: dict
    internal_subnet_id:
        description:
            - Internal subnet ID value
        required: False
        type: int
    service_subnet_id:
        description:
            - Service subnet ID value
        required: False
        type: int
    internal_peer_ip_address:
        description:
            - None
        required: False
        type: str
    address_translation:
        description:
            - None
        required: False
        type: list
        elements: dict
    customer_peer_ip:
        description:
            - Customer Peer IP Address
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
    ('datacenter', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'phase_two',
    'preshared_key',
    'remote_subnet_id',
    'remote_subnet',
    'datacenter',
    'name',
    'phase_one',
    'internal_subnet_id',
    'service_subnet_id',
    'internal_peer_ip_address',
    'address_translation',
    'customer_peer_ip',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    phase_two=dict(
        required=False,
        elements='',
        type='list'),
    preshared_key=dict(
        required=False,
        type='str'),
    remote_subnet_id=dict(
        required=False,
        type='int'),
    remote_subnet=dict(
        required=False,
        elements='',
        type='list'),
    datacenter=dict(
        required=False,
        type='str'),
    name=dict(
        required=False,
        type='str'),
    phase_one=dict(
        required=False,
        elements='',
        type='list'),
    internal_subnet_id=dict(
        required=False,
        type='int'),
    service_subnet_id=dict(
        required=False,
        type='int'),
    internal_peer_ip_address=dict(
        required=False,
        type='str'),
    address_translation=dict(
        required=False,
        elements='',
        type='list'),
    customer_peer_ip=dict(
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
        resource_type='ibm_ipsec_vpn',
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
