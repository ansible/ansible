#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_multi_vlan_firewall
short_description: Configure IBM Cloud 'ibm_multi_vlan_firewall' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_multi_vlan_firewall' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    password:
        description:
            - Password
        required: False
        type: str
    pod:
        description:
            - (Required for new resource) POD name
        required: False
        type: str
    name:
        description:
            - (Required for new resource) name
        required: False
        type: str
    public_vlan_id:
        description:
            - Public VLAN id
        required: False
        type: int
    private_vlan_id:
        description:
            - Private VLAN id
        required: False
        type: int
    firewall_type:
        description:
            - (Required for new resource) Firewall type
        required: False
        type: str
    private_ip:
        description:
            - Private IP Address
        required: False
        type: str
    datacenter:
        description:
            - (Required for new resource) Datacenter name
        required: False
        type: str
    public_ip:
        description:
            - Public IP Address
        required: False
        type: str
    public_ipv6:
        description:
            - Public IPV6 IP
        required: False
        type: str
    username:
        description:
            - User name
        required: False
        type: str
    addon_configuration:
        description:
            - High Availability - [Web Filtering Add-on, NGFW Add-on, AV Add-on] or [Web Filtering Add-on, NGFW Add-on, AV Add-on]
        required: False
        type: list
        elements: str
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
    ('pod', 'str'),
    ('name', 'str'),
    ('firewall_type', 'str'),
    ('datacenter', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'password',
    'pod',
    'name',
    'public_vlan_id',
    'private_vlan_id',
    'firewall_type',
    'private_ip',
    'datacenter',
    'public_ip',
    'public_ipv6',
    'username',
    'addon_configuration',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    password=dict(
        required=False,
        type='str'),
    pod=dict(
        required=False,
        type='str'),
    name=dict(
        required=False,
        type='str'),
    public_vlan_id=dict(
        required=False,
        type='int'),
    private_vlan_id=dict(
        required=False,
        type='int'),
    firewall_type=dict(
        required=False,
        type='str'),
    private_ip=dict(
        required=False,
        type='str'),
    datacenter=dict(
        required=False,
        type='str'),
    public_ip=dict(
        required=False,
        type='str'),
    public_ipv6=dict(
        required=False,
        type='str'),
    username=dict(
        required=False,
        type='str'),
    addon_configuration=dict(
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
        resource_type='ibm_multi_vlan_firewall',
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
