#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_container_worker_pool
short_description: Configure IBM Cloud 'ibm_container_worker_pool' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_container_worker_pool' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    machine_type:
        description:
            - (Required for new resource) worker nodes machine type
        required: False
        type: str
    entitlement:
        description:
            - Entitlement option reduces additional OCP Licence cost in Openshift Clusters
        required: False
        type: str
    hardware:
        description:
            - Hardware type
        required: False
        type: str
        default: shared
    disk_encryption:
        description:
            - worker node disk encrypted if set to true
        required: False
        type: bool
        default: True
    labels:
        description:
            - list of labels to worker pool
        required: False
        type: dict
        elements: str
    resource_group_id:
        description:
            - ID of the resource group.
        required: False
        type: str
    resource_controller_url:
        description:
            - The URL of the IBM Cloud dashboard that can be used to explore and view details about this cluster
        required: False
        type: str
    cluster:
        description:
            - (Required for new resource) Cluster name
        required: False
        type: str
    worker_pool_name:
        description:
            - (Required for new resource) worker pool name
        required: False
        type: str
    size_per_zone:
        description:
            - (Required for new resource) Number of nodes per zone
        required: False
        type: int
    state_:
        description:
            - worker pool state
        required: False
        type: str
    zones:
        description:
            - None
        required: False
        type: list
        elements: dict
    region:
        description:
            - The worker pool region
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
    ('machine_type', 'str'),
    ('cluster', 'str'),
    ('worker_pool_name', 'str'),
    ('size_per_zone', 'int'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'machine_type',
    'entitlement',
    'hardware',
    'disk_encryption',
    'labels',
    'resource_group_id',
    'resource_controller_url',
    'cluster',
    'worker_pool_name',
    'size_per_zone',
    'state_',
    'zones',
    'region',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    machine_type=dict(
        required=False,
        type='str'),
    entitlement=dict(
        required=False,
        type='str'),
    hardware=dict(
        default='shared',
        type='str'),
    disk_encryption=dict(
        default=True,
        type='bool'),
    labels=dict(
        required=False,
        elements='',
        type='dict'),
    resource_group_id=dict(
        required=False,
        type='str'),
    resource_controller_url=dict(
        required=False,
        type='str'),
    cluster=dict(
        required=False,
        type='str'),
    worker_pool_name=dict(
        required=False,
        type='str'),
    size_per_zone=dict(
        required=False,
        type='int'),
    state_=dict(
        required=False,
        type='str'),
    zones=dict(
        required=False,
        elements='',
        type='list'),
    region=dict(
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
        resource_type='ibm_container_worker_pool',
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
