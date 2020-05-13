#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_compute_vm_instance
short_description: Configure IBM Cloud 'ibm_compute_vm_instance' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_compute_vm_instance' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    private_security_group_ids:
        description:
            - None
        required: False
        type: list
        elements: int
    ipv4_address_private:
        description:
            - None
        required: False
        type: str
    file_storage_ids:
        description:
            - None
        required: False
        type: list
        elements: int
    hostname:
        description:
            - None
        required: False
        type: str
    placement_group_name:
        description:
            - The placement group name
        required: False
        type: str
    ssh_key_ids:
        description:
            - None
        required: False
        type: list
        elements: int
    user_metadata:
        description:
            - None
        required: False
        type: str
    public_bandwidth_limited:
        description:
            - None
        required: False
        type: int
    resource_name:
        description:
            - The name of the resource
        required: False
        type: str
    public_vlan_id:
        description:
            - None
        required: False
        type: int
    ipv4_address:
        description:
            - None
        required: False
        type: str
    placement_group_id:
        description:
            - The placement group id
        required: False
        type: int
    image_id:
        description:
            - None
        required: False
        type: int
    notes:
        description:
            - None
        required: False
        type: str
    private_network_only:
        description:
            - None
        required: False
        type: bool
        default: False
    datacenter_choice:
        description:
            - The user provided datacenter options
        required: False
        type: list
        elements: dict
    resource_status:
        description:
            - The status of the resource
        required: False
        type: str
    datacenter:
        description:
            - None
        required: False
        type: str
    ip_address_id:
        description:
            - None
        required: False
        type: int
    private_subnet_id:
        description:
            - None
        required: False
        type: int
    ip_address_id_private:
        description:
            - None
        required: False
        type: int
    block_storage_ids:
        description:
            - None
        required: False
        type: list
        elements: int
    public_subnet_id:
        description:
            - None
        required: False
        type: int
    public_security_group_ids:
        description:
            - None
        required: False
        type: list
        elements: int
    public_ipv6_subnet:
        description:
            - None
        required: False
        type: str
    secondary_ip_addresses:
        description:
            - None
        required: False
        type: list
        elements: str
    hourly_billing:
        description:
            - None
        required: False
        type: bool
        default: True
    transient:
        description:
            - None
        required: False
        type: bool
    flavor_key_name:
        description:
            - Flavor key name used to provision vm.
        required: False
        type: str
    private_vlan_id:
        description:
            - None
        required: False
        type: int
    disks:
        description:
            - None
        required: False
        type: list
        elements: int
    ipv6_enabled:
        description:
            - None
        required: False
        type: bool
        default: False
    ipv6_address:
        description:
            - None
        required: False
        type: str
    public_bandwidth_unlimited:
        description:
            - None
        required: False
        type: bool
        default: False
    domain:
        description:
            - None
        required: False
        type: str
    bulk_vms:
        description:
            - None
        required: False
        type: list
        elements: dict
    dedicated_host_id:
        description:
            - None
        required: False
        type: int
    public_subnet:
        description:
            - None
        required: False
        type: str
    local_disk:
        description:
            - None
        required: False
        type: bool
        default: True
    post_install_script_uri:
        description:
            - None
        required: False
        type: str
    dedicated_acct_host_only:
        description:
            - None
        required: False
        type: bool
    ipv6_static_enabled:
        description:
            - None
        required: False
        type: bool
        default: False
    wait_time_minutes:
        description:
            - None
        required: False
        type: int
        default: 90
    evault:
        description:
            - None
        required: False
        type: int
    cores:
        description:
            - None
        required: False
        type: int
    memory:
        description:
            - None
        required: False
        type: int
    secondary_ip_count:
        description:
            - None
        required: False
        type: int
    tags:
        description:
            - None
        required: False
        type: list
        elements: str
    os_reference_code:
        description:
            - None
        required: False
        type: str
    public_ipv6_subnet_id:
        description:
            - None
        required: False
        type: str
    ipv6_address_id:
        description:
            - None
        required: False
        type: int
    resource_controller_url:
        description:
            - The URL of the IBM Cloud dashboard that can be used to explore and view details about this instance
        required: False
        type: str
    dedicated_host_name:
        description:
            - None
        required: False
        type: str
    network_speed:
        description:
            - None
        required: False
        type: int
        default: 100
    private_subnet:
        description:
            - None
        required: False
        type: str
    public_interface_id:
        description:
            - None
        required: False
        type: int
    private_interface_id:
        description:
            - None
        required: False
        type: int
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
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'private_security_group_ids',
    'ipv4_address_private',
    'file_storage_ids',
    'hostname',
    'placement_group_name',
    'ssh_key_ids',
    'user_metadata',
    'public_bandwidth_limited',
    'resource_name',
    'public_vlan_id',
    'ipv4_address',
    'placement_group_id',
    'image_id',
    'notes',
    'private_network_only',
    'datacenter_choice',
    'resource_status',
    'datacenter',
    'ip_address_id',
    'private_subnet_id',
    'ip_address_id_private',
    'block_storage_ids',
    'public_subnet_id',
    'public_security_group_ids',
    'public_ipv6_subnet',
    'secondary_ip_addresses',
    'hourly_billing',
    'transient',
    'flavor_key_name',
    'private_vlan_id',
    'disks',
    'ipv6_enabled',
    'ipv6_address',
    'public_bandwidth_unlimited',
    'domain',
    'bulk_vms',
    'dedicated_host_id',
    'public_subnet',
    'local_disk',
    'post_install_script_uri',
    'dedicated_acct_host_only',
    'ipv6_static_enabled',
    'wait_time_minutes',
    'evault',
    'cores',
    'memory',
    'secondary_ip_count',
    'tags',
    'os_reference_code',
    'public_ipv6_subnet_id',
    'ipv6_address_id',
    'resource_controller_url',
    'dedicated_host_name',
    'network_speed',
    'private_subnet',
    'public_interface_id',
    'private_interface_id',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    private_security_group_ids=dict(
        required=False,
        elements='',
        type='list'),
    ipv4_address_private=dict(
        required=False,
        type='str'),
    file_storage_ids=dict(
        required=False,
        elements='',
        type='list'),
    hostname=dict(
        required=False,
        type='str'),
    placement_group_name=dict(
        required=False,
        type='str'),
    ssh_key_ids=dict(
        required=False,
        elements='',
        type='list'),
    user_metadata=dict(
        required=False,
        type='str'),
    public_bandwidth_limited=dict(
        required=False,
        type='int'),
    resource_name=dict(
        required=False,
        type='str'),
    public_vlan_id=dict(
        required=False,
        type='int'),
    ipv4_address=dict(
        required=False,
        type='str'),
    placement_group_id=dict(
        required=False,
        type='int'),
    image_id=dict(
        required=False,
        type='int'),
    notes=dict(
        required=False,
        type='str'),
    private_network_only=dict(
        default=False,
        type='bool'),
    datacenter_choice=dict(
        required=False,
        elements='',
        type='list'),
    resource_status=dict(
        required=False,
        type='str'),
    datacenter=dict(
        required=False,
        type='str'),
    ip_address_id=dict(
        required=False,
        type='int'),
    private_subnet_id=dict(
        required=False,
        type='int'),
    ip_address_id_private=dict(
        required=False,
        type='int'),
    block_storage_ids=dict(
        required=False,
        elements='',
        type='list'),
    public_subnet_id=dict(
        required=False,
        type='int'),
    public_security_group_ids=dict(
        required=False,
        elements='',
        type='list'),
    public_ipv6_subnet=dict(
        required=False,
        type='str'),
    secondary_ip_addresses=dict(
        required=False,
        elements='',
        type='list'),
    hourly_billing=dict(
        default=True,
        type='bool'),
    transient=dict(
        required=False,
        type='bool'),
    flavor_key_name=dict(
        required=False,
        type='str'),
    private_vlan_id=dict(
        required=False,
        type='int'),
    disks=dict(
        required=False,
        elements='',
        type='list'),
    ipv6_enabled=dict(
        default=False,
        type='bool'),
    ipv6_address=dict(
        required=False,
        type='str'),
    public_bandwidth_unlimited=dict(
        default=False,
        type='bool'),
    domain=dict(
        required=False,
        type='str'),
    bulk_vms=dict(
        required=False,
        elements='',
        type='list'),
    dedicated_host_id=dict(
        required=False,
        type='int'),
    public_subnet=dict(
        required=False,
        type='str'),
    local_disk=dict(
        default=True,
        type='bool'),
    post_install_script_uri=dict(
        required=False,
        type='str'),
    dedicated_acct_host_only=dict(
        required=False,
        type='bool'),
    ipv6_static_enabled=dict(
        default=False,
        type='bool'),
    wait_time_minutes=dict(
        default=90,
        type='int'),
    evault=dict(
        required=False,
        type='int'),
    cores=dict(
        required=False,
        type='int'),
    memory=dict(
        required=False,
        type='int'),
    secondary_ip_count=dict(
        required=False,
        type='int'),
    tags=dict(
        required=False,
        elements='',
        type='list'),
    os_reference_code=dict(
        required=False,
        type='str'),
    public_ipv6_subnet_id=dict(
        required=False,
        type='str'),
    ipv6_address_id=dict(
        required=False,
        type='int'),
    resource_controller_url=dict(
        required=False,
        type='str'),
    dedicated_host_name=dict(
        required=False,
        type='str'),
    network_speed=dict(
        default=100,
        type='int'),
    private_subnet=dict(
        required=False,
        type='str'),
    public_interface_id=dict(
        required=False,
        type='int'),
    private_interface_id=dict(
        required=False,
        type='int'),
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
        resource_type='ibm_compute_vm_instance',
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
