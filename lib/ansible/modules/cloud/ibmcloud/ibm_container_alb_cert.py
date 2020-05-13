#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_container_alb_cert
short_description: Configure IBM Cloud 'ibm_container_alb_cert' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_container_alb_cert' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    expires_on:
        description:
            - Certificate expaire on date
        required: False
        type: str
    issuer_name:
        description:
            - certificate issuer name
        required: False
        type: str
    cluster_crn:
        description:
            - cluster CRN
        required: False
        type: str
    region:
        description:
            - region name
        required: False
        type: str
    cert_crn:
        description:
            - (Required for new resource) Certificate CRN id
        required: False
        type: str
    cluster_id:
        description:
            - (Required for new resource) Cluster ID
        required: False
        type: str
    secret_name:
        description:
            - (Required for new resource) Secret name
        required: False
        type: str
    domain_name:
        description:
            - Domain name
        required: False
        type: str
    cloud_cert_instance_id:
        description:
            - cloud cert instance ID
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
    ('cert_crn', 'str'),
    ('cluster_id', 'str'),
    ('secret_name', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'expires_on',
    'issuer_name',
    'cluster_crn',
    'region',
    'cert_crn',
    'cluster_id',
    'secret_name',
    'domain_name',
    'cloud_cert_instance_id',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    expires_on=dict(
        required=False,
        type='str'),
    issuer_name=dict(
        required=False,
        type='str'),
    cluster_crn=dict(
        required=False,
        type='str'),
    region=dict(
        required=False,
        type='str'),
    cert_crn=dict(
        required=False,
        type='str'),
    cluster_id=dict(
        required=False,
        type='str'),
    secret_name=dict(
        required=False,
        type='str'),
    domain_name=dict(
        required=False,
        type='str'),
    cloud_cert_instance_id=dict(
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
        resource_type='ibm_container_alb_cert',
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
