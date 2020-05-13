#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_database
short_description: Configure IBM Cloud 'ibm_database' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_database' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    members_memory_allocation_mb:
        description:
            - Memory allocation required for cluster
        required: False
        type: int
    remote_leader_id:
        description:
            - The CRN of leader database
        required: False
        type: str
    tags:
        description:
            - None
        required: False
        type: list
        elements: str
    key_protect_key:
        description:
            - The CRN of Key protect key
        required: False
        type: str
    members_disk_allocation_mb:
        description:
            - Disk allocation required for cluster
        required: False
        type: int
    groups:
        description:
            - None
        required: False
        type: list
        elements: dict
    whitelist:
        description:
            - None
        required: False
        type: list
        elements: dict
    status:
        description:
            - The resource instance status
        required: False
        type: str
    service_endpoints:
        description:
            - Types of the service endpoints. Possible values are 'public', 'private', 'public-and-private'.
        required: False
        type: str
        default: public
    users:
        description:
            - None
        required: False
        type: list
        elements: dict
    resource_name:
        description:
            - The name of the resource
        required: False
        type: str
    resource_crn:
        description:
            - The crn of the resource
        required: False
        type: str
    resource_group_name:
        description:
            - The resource group name in which resource is provisioned
        required: False
        type: str
    guid:
        description:
            - Unique identifier of resource instance
        required: False
        type: str
    adminuser:
        description:
            - The admin user id for the instance
        required: False
        type: str
    adminpassword:
        description:
            - The admin user password for the instance
        required: False
        type: str
    point_in_time_recovery_deployment_id:
        description:
            - The CRN of source instance
        required: False
        type: str
    resource_status:
        description:
            - The status of the resource
        required: False
        type: str
    resource_group_id:
        description:
            - The id of the resource group in which the Database instance is present
        required: False
        type: str
    plan:
        description:
            - (Required for new resource) The plan type of the Database instance
        required: False
        type: str
    backup_id:
        description:
            - The CRN of backup source database
        required: False
        type: str
    members_cpu_allocation_count:
        description:
            - CPU allocation required for cluster
        required: False
        type: int
    key_protect_instance:
        description:
            - The CRN of Key protect instance
        required: False
        type: str
    connectionstrings:
        description:
            - None
        required: False
        type: list
        elements: dict
    version:
        description:
            - The database version to provision if specified
        required: False
        type: str
    point_in_time_recovery_time:
        description:
            - The point in time recovery time stamp of the deployed instance
        required: False
        type: str
    resource_controller_url:
        description:
            - The URL of the IBM Cloud dashboard that can be used to explore and view details about the resource
        required: False
        type: str
    name:
        description:
            - (Required for new resource) Resource instance name for example, my Database instance
        required: False
        type: str
    location:
        description:
            - (Required for new resource) The location or the region in which Database instance exists
        required: False
        type: str
    service:
        description:
            - (Required for new resource) The name of the Cloud Internet database service
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
    ('plan', 'str'),
    ('name', 'str'),
    ('location', 'str'),
    ('service', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'members_memory_allocation_mb',
    'remote_leader_id',
    'tags',
    'key_protect_key',
    'members_disk_allocation_mb',
    'groups',
    'whitelist',
    'status',
    'service_endpoints',
    'users',
    'resource_name',
    'resource_crn',
    'resource_group_name',
    'guid',
    'adminuser',
    'adminpassword',
    'point_in_time_recovery_deployment_id',
    'resource_status',
    'resource_group_id',
    'plan',
    'backup_id',
    'members_cpu_allocation_count',
    'key_protect_instance',
    'connectionstrings',
    'version',
    'point_in_time_recovery_time',
    'resource_controller_url',
    'name',
    'location',
    'service',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    members_memory_allocation_mb=dict(
        required=False,
        type='int'),
    remote_leader_id=dict(
        required=False,
        type='str'),
    tags=dict(
        required=False,
        elements='',
        type='list'),
    key_protect_key=dict(
        required=False,
        type='str'),
    members_disk_allocation_mb=dict(
        required=False,
        type='int'),
    groups=dict(
        required=False,
        elements='',
        type='list'),
    whitelist=dict(
        required=False,
        elements='',
        type='list'),
    status=dict(
        required=False,
        type='str'),
    service_endpoints=dict(
        default='public',
        type='str'),
    users=dict(
        required=False,
        elements='',
        type='list'),
    resource_name=dict(
        required=False,
        type='str'),
    resource_crn=dict(
        required=False,
        type='str'),
    resource_group_name=dict(
        required=False,
        type='str'),
    guid=dict(
        required=False,
        type='str'),
    adminuser=dict(
        required=False,
        type='str'),
    adminpassword=dict(
        required=False,
        type='str'),
    point_in_time_recovery_deployment_id=dict(
        required=False,
        type='str'),
    resource_status=dict(
        required=False,
        type='str'),
    resource_group_id=dict(
        required=False,
        type='str'),
    plan=dict(
        required=False,
        type='str'),
    backup_id=dict(
        required=False,
        type='str'),
    members_cpu_allocation_count=dict(
        required=False,
        type='int'),
    key_protect_instance=dict(
        required=False,
        type='str'),
    connectionstrings=dict(
        required=False,
        elements='',
        type='list'),
    version=dict(
        required=False,
        type='str'),
    point_in_time_recovery_time=dict(
        required=False,
        type='str'),
    resource_controller_url=dict(
        required=False,
        type='str'),
    name=dict(
        required=False,
        type='str'),
    location=dict(
        required=False,
        type='str'),
    service=dict(
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
        resource_type='ibm_database',
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
