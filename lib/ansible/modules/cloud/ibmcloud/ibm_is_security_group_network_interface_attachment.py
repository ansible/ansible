#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_is_security_group_network_interface_attachment
short_description: Configure IBM Cloud 'ibm_is_security_group_network_interface_attachment' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_is_security_group_network_interface_attachment' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    subnet:
        description:
            - security group network interface attachment subnet
        required: False
        type: str
    type:
        description:
            - security group network interface attachment type
        required: False
        type: str
    floating_ips:
        description:
            - None
        required: False
        type: list
        elements: dict
    security_groups:
        description:
            - None
        required: False
        type: list
        elements: dict
    instance_network_interface:
        description:
            - security group network interface attachment network interface ID
        required: False
        type: str
    port_speed:
        description:
            - security group network interface attachment port speed
        required: False
        type: int
    status:
        description:
            - security group network interface attachment status
        required: False
        type: str
    secondary_address:
        description:
            - security group network interface attachment secondary address
        required: False
        type: list
        elements: str
    security_group:
        description:
            - (Required for new resource) security group network interface attachment group ID
        required: False
        type: str
    network_interface:
        description:
            - (Required for new resource) security group network interface attachment NIC ID
        required: False
        type: str
    name:
        description:
            - security group network interface attachment name
        required: False
        type: str
    primary_ipv4_address:
        description:
            - security group network interface attachment Primary IPV4 address
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
    ('security_group', 'str'),
    ('network_interface', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'subnet',
    'type',
    'floating_ips',
    'security_groups',
    'instance_network_interface',
    'port_speed',
    'status',
    'secondary_address',
    'security_group',
    'network_interface',
    'name',
    'primary_ipv4_address',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    subnet=dict(
        required=False,
        type='str'),
    type=dict(
        required=False,
        type='str'),
    floating_ips=dict(
        required=False,
        elements='',
        type='list'),
    security_groups=dict(
        required=False,
        elements='',
        type='list'),
    instance_network_interface=dict(
        required=False,
        type='str'),
    port_speed=dict(
        required=False,
        type='int'),
    status=dict(
        required=False,
        type='str'),
    secondary_address=dict(
        required=False,
        elements='',
        type='list'),
    security_group=dict(
        required=False,
        type='str'),
    network_interface=dict(
        required=False,
        type='str'),
    name=dict(
        required=False,
        type='str'),
    primary_ipv4_address=dict(
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
        resource_type='ibm_is_security_group_network_interface_attachment',
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
