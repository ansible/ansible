#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_container_cluster_versions_info
short_description: Retrieve IBM Cloud 'ibm_container_cluster_versions' resource

version_added: "2.8"

description:
    - Retrieve an IBM Cloud 'ibm_container_cluster_versions' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    resource_group_id:
        description:
            - ID of the resource group.
        required: False
        type: str
    valid_kube_versions:
        description:
            - List supported kube-versions
        required: False
        type: list
        elements: str
    valid_openshift_versions:
        description:
            - List of supported openshift-versions
        required: False
        type: list
        elements: str
    org_guid:
        description:
            - The bluemix organization guid this cluster belongs to
        required: False
        type: str
    space_guid:
        description:
            - The bluemix space guid this cluster belongs to
        required: False
        type: str
    account_guid:
        description:
            - The bluemix account guid this cluster belongs to
        required: False
        type: str
    region:
        description:
            - The cluster region
        required: False
        type: str
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
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'resource_group_id',
    'valid_kube_versions',
    'valid_openshift_versions',
    'org_guid',
    'space_guid',
    'account_guid',
    'region',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    resource_group_id=dict(
        required=False,
        type='str'),
    valid_kube_versions=dict(
        required=False,
        elements='',
        type='list'),
    valid_openshift_versions=dict(
        required=False,
        elements='',
        type='list'),
    org_guid=dict(
        required=False,
        type='str'),
    space_guid=dict(
        required=False,
        type='str'),
    account_guid=dict(
        required=False,
        type='str'),
    region=dict(
        required=False,
        type='str'),
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
        resource_type='ibm_container_cluster_versions',
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
