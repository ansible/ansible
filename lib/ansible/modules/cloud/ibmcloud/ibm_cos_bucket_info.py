#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_cos_bucket_info
short_description: Retrieve IBM Cloud 'ibm_cos_bucket' resource

version_added: "2.8"

description:
    - Retrieve an IBM Cloud 'ibm_cos_bucket' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    bucket_type:
        description:
            - None
        required: True
        type: str
    bucket_region:
        description:
            - None
        required: True
        type: str
    resource_instance_id:
        description:
            - None
        required: True
        type: str
    cross_region_location:
        description:
            - None
        required: False
        type: str
    storage_class:
        description:
            - None
        required: False
        type: str
    s3_endpoint_public:
        description:
            - Public endpoint for the COS bucket
        required: False
        type: str
    bucket_name:
        description:
            - None
        required: True
        type: str
    crn:
        description:
            - CRN of resource instance
        required: False
        type: str
    key_protect:
        description:
            - CRN of the key you want to use data at rest encryption
        required: False
        type: str
    single_site_location:
        description:
            - None
        required: False
        type: str
    region_location:
        description:
            - None
        required: False
        type: str
    s3_endpoint_private:
        description:
            - Private endpoint for the COS bucket
        required: False
        type: str
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
    ('bucket_type', 'str'),
    ('bucket_region', 'str'),
    ('resource_instance_id', 'str'),
    ('bucket_name', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'bucket_type',
    'bucket_region',
    'resource_instance_id',
    'cross_region_location',
    'storage_class',
    's3_endpoint_public',
    'bucket_name',
    'crn',
    'key_protect',
    'single_site_location',
    'region_location',
    's3_endpoint_private',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    bucket_type=dict(
        required=True,
        type='str'),
    bucket_region=dict(
        required=True,
        type='str'),
    resource_instance_id=dict(
        required=True,
        type='str'),
    cross_region_location=dict(
        required=False,
        type='str'),
    storage_class=dict(
        required=False,
        type='str'),
    s3_endpoint_public=dict(
        required=False,
        type='str'),
    bucket_name=dict(
        required=True,
        type='str'),
    crn=dict(
        required=False,
        type='str'),
    key_protect=dict(
        required=False,
        type='str'),
    single_site_location=dict(
        required=False,
        type='str'),
    region_location=dict(
        required=False,
        type='str'),
    s3_endpoint_private=dict(
        required=False,
        type='str'),
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

    result = ibmcloud_terraform(
        resource_type='ibm_cos_bucket',
        tf_type='data',
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
