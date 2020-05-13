#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_container_cluster_config_info
short_description: Retrieve IBM Cloud 'ibm_container_cluster_config' resource

version_added: "2.8"

description:
    - Retrieve an IBM Cloud 'ibm_container_cluster_config' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    admin_key:
        description:
            - None
        required: False
        type: str
    host:
        description:
            - None
        required: False
        type: str
    download:
        description:
            - If set to false will not download the config, otherwise they are downloaded each time but onto the same path for a given cluster name/id
        required: False
        type: bool
        default: True
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
    cluster_name_id:
        description:
            - The name/id of the cluster
        required: True
        type: str
    admin_certificate:
        description:
            - None
        required: False
        type: str
    token:
        description:
            - None
        required: False
        type: str
    org_guid:
        description:
            - The bluemix organization guid this cluster belongs to
        required: False
        type: str
    resource_group_id:
        description:
            - ID of the resource group.
        required: False
        type: str
    config_dir:
        description:
            - The directory where the cluster config to be downloaded. Default is home directory
        required: False
        type: str
    network:
        description:
            - If set to true will download the Calico network config with the Admin config
        required: False
        type: bool
        default: False
    calico_config_file_path:
        description:
            - The absolute path to the calico network config file
        required: False
        type: str
    space_guid:
        description:
            - The bluemix space guid this cluster belongs to
        required: False
        type: str
    config_file_path:
        description:
            - The absolute path to the kubernetes config yml file
        required: False
        type: str
    ca_certificate:
        description:
            - None
        required: False
        type: str
    admin:
        description:
            - If set to true will download the config for admin
        required: False
        type: bool
        default: False
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
    ('cluster_name_id', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'admin_key',
    'host',
    'download',
    'account_guid',
    'region',
    'cluster_name_id',
    'admin_certificate',
    'token',
    'org_guid',
    'resource_group_id',
    'config_dir',
    'network',
    'calico_config_file_path',
    'space_guid',
    'config_file_path',
    'ca_certificate',
    'admin',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    admin_key=dict(
        required=False,
        type='str'),
    host=dict(
        required=False,
        type='str'),
    download=dict(
        default=True,
        type='bool'),
    account_guid=dict(
        required=False,
        type='str'),
    region=dict(
        required=False,
        type='str'),
    cluster_name_id=dict(
        required=True,
        type='str'),
    admin_certificate=dict(
        required=False,
        type='str'),
    token=dict(
        required=False,
        type='str'),
    org_guid=dict(
        required=False,
        type='str'),
    resource_group_id=dict(
        required=False,
        type='str'),
    config_dir=dict(
        required=False,
        type='str'),
    network=dict(
        default=False,
        type='bool'),
    calico_config_file_path=dict(
        required=False,
        type='str'),
    space_guid=dict(
        required=False,
        type='str'),
    config_file_path=dict(
        required=False,
        type='str'),
    ca_certificate=dict(
        required=False,
        type='str'),
    admin=dict(
        default=False,
        type='bool'),
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
        resource_type='ibm_container_cluster_config',
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
