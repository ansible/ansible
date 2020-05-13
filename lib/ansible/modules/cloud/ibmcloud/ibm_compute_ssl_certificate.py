#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_compute_ssl_certificate
short_description: Configure IBM Cloud 'ibm_compute_ssl_certificate' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_compute_ssl_certificate' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    private_key:
        description:
            - (Required for new resource) SSL Private Key
        required: False
        type: str
    common_name:
        description:
            - Common name
        required: False
        type: str
    validity_days:
        description:
            - Validity days
        required: False
        type: int
    validity_end:
        description:
            - Validity ends before
        required: False
        type: str
    key_size:
        description:
            - SSL key size
        required: False
        type: int
    intermediate_certificate:
        description:
            - Intermediate certificate value
        required: False
        type: str
    organization_name:
        description:
            - Organization name
        required: False
        type: str
    validity_begin:
        description:
            - Validity begins from
        required: False
        type: str
    create_date:
        description:
            - certificate creation date
        required: False
        type: str
    modify_date:
        description:
            - certificate modificatiob date
        required: False
        type: str
    tags:
        description:
            - Tags set for resource
        required: False
        type: list
        elements: str
    certificate:
        description:
            - (Required for new resource) SSL Certifcate
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
    ('private_key', 'str'),
    ('certificate', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'private_key',
    'common_name',
    'validity_days',
    'validity_end',
    'key_size',
    'intermediate_certificate',
    'organization_name',
    'validity_begin',
    'create_date',
    'modify_date',
    'tags',
    'certificate',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    private_key=dict(
        required=False,
        type='str'),
    common_name=dict(
        required=False,
        type='str'),
    validity_days=dict(
        required=False,
        type='int'),
    validity_end=dict(
        required=False,
        type='str'),
    key_size=dict(
        required=False,
        type='int'),
    intermediate_certificate=dict(
        required=False,
        type='str'),
    organization_name=dict(
        required=False,
        type='str'),
    validity_begin=dict(
        required=False,
        type='str'),
    create_date=dict(
        required=False,
        type='str'),
    modify_date=dict(
        required=False,
        type='str'),
    tags=dict(
        required=False,
        elements='',
        type='list'),
    certificate=dict(
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
        resource_type='ibm_compute_ssl_certificate',
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
