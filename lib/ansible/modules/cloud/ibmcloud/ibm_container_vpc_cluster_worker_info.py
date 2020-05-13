#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_container_vpc_cluster_worker_info
short_description: Retrieve IBM Cloud 'ibm_container_vpc_cluster_worker' resource

version_added: "2.8"

description:
    - Retrieve an IBM Cloud 'ibm_container_vpc_cluster_worker' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    state:
        description:
            - State of the worker
        required: False
        type: str
    pool_id:
        description:
            - worker pool id
        required: False
        type: str
    resource_group_id:
        description:
            - ID of the resource group.
        required: False
        type: str
    worker_id:
        description:
            - ID of the worker
        required: True
        type: str
    cluster_name_id:
        description:
            - Name or ID of the cluster
        required: True
        type: str
    pool_name:
        description:
            - worker pool name
        required: False
        type: str
    network_interfaces:
        description:
            - None
        required: False
        type: list
        elements: dict
    resource_controller_url:
        description:
            - The URL of the IBM Cloud dashboard that can be used to explore and view details about this cluster
        required: False
        type: str
    flavor:
        description:
            - flavor of the worker
        required: False
        type: str
    kube_version:
        description:
            - kube version of the worker
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
    ('worker_id', 'str'),
    ('cluster_name_id', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'state',
    'pool_id',
    'resource_group_id',
    'worker_id',
    'cluster_name_id',
    'pool_name',
    'network_interfaces',
    'resource_controller_url',
    'flavor',
    'kube_version',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    state=dict(
        required=False,
        type='str'),
    pool_id=dict(
        required=False,
        type='str'),
    resource_group_id=dict(
        required=False,
        type='str'),
    worker_id=dict(
        required=True,
        type='str'),
    cluster_name_id=dict(
        required=True,
        type='str'),
    pool_name=dict(
        required=False,
        type='str'),
    network_interfaces=dict(
        required=False,
        elements='',
        type='list'),
    resource_controller_url=dict(
        required=False,
        type='str'),
    flavor=dict(
        required=False,
        type='str'),
    kube_version=dict(
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
        resource_type='ibm_container_vpc_cluster_worker',
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
