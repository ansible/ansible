#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_compute_autoscale_group
short_description: Configure IBM Cloud 'ibm_compute_autoscale_group' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_compute_autoscale_group' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    maximum_member_count:
        description:
            - (Required for new resource) Maximum member count
        required: False
        type: int
    cooldown:
        description:
            - (Required for new resource) Cooldown value
        required: False
        type: int
    termination_policy:
        description:
            - (Required for new resource) Termination policy
        required: False
        type: str
    virtual_server_id:
        description:
            - virtual server ID
        required: False
        type: int
    port:
        description:
            - Port number
        required: False
        type: int
    name:
        description:
            - (Required for new resource) Name
        required: False
        type: str
    regional_group:
        description:
            - (Required for new resource) regional group
        required: False
        type: str
    minimum_member_count:
        description:
            - (Required for new resource) Minimum member count
        required: False
        type: int
    health_check:
        description:
            - None
        required: False
        type: dict
        elements: dict
    virtual_guest_member_template:
        description:
            - (Required for new resource) Virtual guest member template
        required: False
        type: list
        elements: dict
    tags:
        description:
            - List of tags
        required: False
        type: list
        elements: str
    network_vlan_ids:
        description:
            - List of network VLAN ids
        required: False
        type: list
        elements: int
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
    ('maximum_member_count', 'int'),
    ('cooldown', 'int'),
    ('termination_policy', 'str'),
    ('name', 'str'),
    ('regional_group', 'str'),
    ('minimum_member_count', 'int'),
    ('virtual_guest_member_template', 'list'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'maximum_member_count',
    'cooldown',
    'termination_policy',
    'virtual_server_id',
    'port',
    'name',
    'regional_group',
    'minimum_member_count',
    'health_check',
    'virtual_guest_member_template',
    'tags',
    'network_vlan_ids',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    maximum_member_count=dict(
        required=False,
        type='int'),
    cooldown=dict(
        required=False,
        type='int'),
    termination_policy=dict(
        required=False,
        type='str'),
    virtual_server_id=dict(
        required=False,
        type='int'),
    port=dict(
        required=False,
        type='int'),
    name=dict(
        required=False,
        type='str'),
    regional_group=dict(
        required=False,
        type='str'),
    minimum_member_count=dict(
        required=False,
        type='int'),
    health_check=dict(
        required=False,
        elements='',
        type='dict'),
    virtual_guest_member_template=dict(
        required=False,
        elements='',
        type='list'),
    tags=dict(
        required=False,
        elements='',
        type='list'),
    network_vlan_ids=dict(
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
        resource_type='ibm_compute_autoscale_group',
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
