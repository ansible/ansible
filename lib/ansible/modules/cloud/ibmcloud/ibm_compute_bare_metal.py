#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_compute_bare_metal
short_description: Configure IBM Cloud 'ibm_compute_bare_metal' resource

version_added: "2.8"

description:
    - Create, update or destroy an IBM Cloud 'ibm_compute_bare_metal' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    domain:
        description:
            - (Required for new resource) Domain name
        required: False
        type: str
    process_key_name:
        description:
            - None
        required: False
        type: str
    os_key_name:
        description:
            - None
        required: False
        type: str
    restricted_network:
        description:
            - None
        required: False
        type: bool
        default: False
    memory:
        description:
            - None
        required: False
        type: int
    hostname:
        description:
            - Host name
        required: False
        type: str
    file_storage_ids:
        description:
            - None
        required: False
        type: list
        elements: int
    block_storage_ids:
        description:
            - None
        required: False
        type: list
        elements: int
    private_network_only:
        description:
            - only private network configured if is true
        required: False
        type: bool
        default: False
    software_guard_extensions:
        description:
            - None
        required: False
        type: bool
        default: False
    public_ipv4_address_id:
        description:
            - None
        required: False
        type: int
    global_identifier:
        description:
            - The unique global identifier of the bare metal server
        required: False
        type: str
    private_ipv4_address:
        description:
            - None
        required: False
        type: str
    redundant_power_supply:
        description:
            - None
        required: False
        type: bool
    package_key_name:
        description:
            - None
        required: False
        type: str
    gpu_key_name:
        description:
            - None
        required: False
        type: str
    gpu_secondary_key_name:
        description:
            - None
        required: False
        type: str
    disk_key_names:
        description:
            - None
        required: False
        type: list
        elements: str
    quote_id:
        description:
            - Quote ID for Quote based provisioning
        required: False
        type: int
    private_subnet:
        description:
            - None
        required: False
        type: str
    notes:
        description:
            - Optional notes info
        required: False
        type: str
    public_bandwidth:
        description:
            - None
        required: False
        type: int
    ipv6_static_enabled:
        description:
            - boolean value true if ipv6 static is enabled else false
        required: False
        type: bool
        default: False
    ssh_key_ids:
        description:
            - SSH KEY IDS list
        required: False
        type: list
        elements: int
    user_metadata:
        description:
            - User metadata info
        required: False
        type: str
    os_reference_code:
        description:
            - OS refernece code value
        required: False
        type: str
    extended_hardware_testing:
        description:
            - None
        required: False
        type: bool
        default: False
    secondary_ip_count:
        description:
            - Secondary IP addresses count
        required: False
        type: int
    ipv6_address:
        description:
            - None
        required: False
        type: str
    image_template_id:
        description:
            - OS image template ID
        required: False
        type: int
    datacenter:
        description:
            - None
        required: False
        type: str
    tcp_monitoring:
        description:
            - TCP monitoring enabled if set as true
        required: False
        type: bool
        default: False
    unbonded_network:
        description:
            - None
        required: False
        type: bool
        default: False
    public_subnet:
        description:
            - None
        required: False
        type: str
    private_ipv4_address_id:
        description:
            - None
        required: False
        type: int
    ipv6_enabled:
        description:
            - Boolean value true if IPV6 ia enabled or false
        required: False
        type: bool
        default: False
    ipv6_address_id:
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
    network_speed:
        description:
            - Network speed in MBPS
        required: False
        type: int
        default: 100
    storage_groups:
        description:
            - None
        required: False
        type: list
        elements: dict
    public_vlan_id:
        description:
            - None
        required: False
        type: int
    public_ipv4_address:
        description:
            - None
        required: False
        type: str
    post_install_script_uri:
        description:
            - None
        required: False
        type: str
    fixed_config_preset:
        description:
            - Fixed config preset value
        required: False
        type: str
    hourly_billing:
        description:
            - Enables hourly billing
        required: False
        type: bool
        default: True
    redundant_network:
        description:
            - None
        required: False
        type: bool
        default: False
    private_vlan_id:
        description:
            - None
        required: False
        type: int
    secondary_ip_addresses:
        description:
            - None
        required: False
        type: list
        elements: str
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
    ('domain', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'domain',
    'process_key_name',
    'os_key_name',
    'restricted_network',
    'memory',
    'hostname',
    'file_storage_ids',
    'block_storage_ids',
    'private_network_only',
    'software_guard_extensions',
    'public_ipv4_address_id',
    'global_identifier',
    'private_ipv4_address',
    'redundant_power_supply',
    'package_key_name',
    'gpu_key_name',
    'gpu_secondary_key_name',
    'disk_key_names',
    'quote_id',
    'private_subnet',
    'notes',
    'public_bandwidth',
    'ipv6_static_enabled',
    'ssh_key_ids',
    'user_metadata',
    'os_reference_code',
    'extended_hardware_testing',
    'secondary_ip_count',
    'ipv6_address',
    'image_template_id',
    'datacenter',
    'tcp_monitoring',
    'unbonded_network',
    'public_subnet',
    'private_ipv4_address_id',
    'ipv6_enabled',
    'ipv6_address_id',
    'tags',
    'network_speed',
    'storage_groups',
    'public_vlan_id',
    'public_ipv4_address',
    'post_install_script_uri',
    'fixed_config_preset',
    'hourly_billing',
    'redundant_network',
    'private_vlan_id',
    'secondary_ip_addresses',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    domain=dict(
        required=False,
        type='str'),
    process_key_name=dict(
        required=False,
        type='str'),
    os_key_name=dict(
        required=False,
        type='str'),
    restricted_network=dict(
        default=False,
        type='bool'),
    memory=dict(
        required=False,
        type='int'),
    hostname=dict(
        required=False,
        type='str'),
    file_storage_ids=dict(
        required=False,
        elements='',
        type='list'),
    block_storage_ids=dict(
        required=False,
        elements='',
        type='list'),
    private_network_only=dict(
        default=False,
        type='bool'),
    software_guard_extensions=dict(
        default=False,
        type='bool'),
    public_ipv4_address_id=dict(
        required=False,
        type='int'),
    global_identifier=dict(
        required=False,
        type='str'),
    private_ipv4_address=dict(
        required=False,
        type='str'),
    redundant_power_supply=dict(
        required=False,
        type='bool'),
    package_key_name=dict(
        required=False,
        type='str'),
    gpu_key_name=dict(
        required=False,
        type='str'),
    gpu_secondary_key_name=dict(
        required=False,
        type='str'),
    disk_key_names=dict(
        required=False,
        elements='',
        type='list'),
    quote_id=dict(
        required=False,
        type='int'),
    private_subnet=dict(
        required=False,
        type='str'),
    notes=dict(
        required=False,
        type='str'),
    public_bandwidth=dict(
        required=False,
        type='int'),
    ipv6_static_enabled=dict(
        default=False,
        type='bool'),
    ssh_key_ids=dict(
        required=False,
        elements='',
        type='list'),
    user_metadata=dict(
        required=False,
        type='str'),
    os_reference_code=dict(
        required=False,
        type='str'),
    extended_hardware_testing=dict(
        default=False,
        type='bool'),
    secondary_ip_count=dict(
        required=False,
        type='int'),
    ipv6_address=dict(
        required=False,
        type='str'),
    image_template_id=dict(
        required=False,
        type='int'),
    datacenter=dict(
        required=False,
        type='str'),
    tcp_monitoring=dict(
        default=False,
        type='bool'),
    unbonded_network=dict(
        default=False,
        type='bool'),
    public_subnet=dict(
        required=False,
        type='str'),
    private_ipv4_address_id=dict(
        required=False,
        type='int'),
    ipv6_enabled=dict(
        default=False,
        type='bool'),
    ipv6_address_id=dict(
        required=False,
        type='int'),
    tags=dict(
        required=False,
        elements='',
        type='list'),
    network_speed=dict(
        default=100,
        type='int'),
    storage_groups=dict(
        required=False,
        elements='',
        type='list'),
    public_vlan_id=dict(
        required=False,
        type='int'),
    public_ipv4_address=dict(
        required=False,
        type='str'),
    post_install_script_uri=dict(
        required=False,
        type='str'),
    fixed_config_preset=dict(
        required=False,
        type='str'),
    hourly_billing=dict(
        default=True,
        type='bool'),
    redundant_network=dict(
        default=False,
        type='bool'),
    private_vlan_id=dict(
        required=False,
        type='int'),
    secondary_ip_addresses=dict(
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
        resource_type='ibm_compute_bare_metal',
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
