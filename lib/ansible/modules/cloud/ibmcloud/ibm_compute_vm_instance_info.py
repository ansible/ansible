#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_compute_vm_instance_info
short_description: Retrieve IBM Cloud 'ibm_compute_vm_instance' resource

version_added: "2.8"

description:
    - Retrieve an IBM Cloud 'ibm_compute_vm_instance' resource

requirements:
    - IBM-Cloud terraform-provider-ibm v1.5.2
    - Terraform v0.12.20

options:
    hostname:
        description:
            - The hostname of the virtual guest
        required: True
        type: str
    datacenter:
        description:
            - Datacenter in which the virtual guest is deployed
        required: False
        type: str
    cores:
        description:
            - Number of cpu cores
        required: False
        type: int
    power_state:
        description:
            - The current power state of a virtual guest.
        required: False
        type: str
    public_ipv6_subnet:
        description:
            - None
        required: False
        type: str
    private_interface_id:
        description:
            - None
        required: False
        type: int
    ipv4_address_private:
        description:
            - None
        required: False
        type: str
    ip_address_id:
        description:
            - None
        required: False
        type: int
    ipv6_address:
        description:
            - None
        required: False
        type: str
    secondary_ip_count:
        description:
            - None
        required: False
        type: int
    domain:
        description:
            - The domain of the virtual guest
        required: True
        type: str
    last_known_power_state:
        description:
            - The last known power state of a virtual guest in the event the guest is turned off outside of IMS or has gone offline.
        required: False
        type: str
    public_subnet_id:
        description:
            - None
        required: False
        type: int
    private_subnet_id:
        description:
            - None
        required: False
        type: int
    ipv4_address:
        description:
            - None
        required: False
        type: str
    ip_address_id_private:
        description:
            - None
        required: False
        type: int
    public_ipv6_subnet_id:
        description:
            - None
        required: False
        type: str
    status:
        description:
            - The VSI status
        required: False
        type: str
    public_interface_id:
        description:
            - None
        required: False
        type: int
    most_recent:
        description:
            - If true and multiple entries are found, the most recently created virtual guest is used. If false, an error is returned
        required: False
        type: bool
        default: False
    ipv6_address_id:
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
    ('hostname', 'str'),
    ('domain', 'str'),
]

# All top level parameter keys supported by Terraform module
TL_ALL_PARAMETERS = [
    'hostname',
    'datacenter',
    'cores',
    'power_state',
    'public_ipv6_subnet',
    'private_interface_id',
    'ipv4_address_private',
    'ip_address_id',
    'ipv6_address',
    'secondary_ip_count',
    'domain',
    'last_known_power_state',
    'public_subnet_id',
    'private_subnet_id',
    'ipv4_address',
    'ip_address_id_private',
    'public_ipv6_subnet_id',
    'status',
    'public_interface_id',
    'most_recent',
    'ipv6_address_id',
    'secondary_ip_addresses',
]

# define available arguments/parameters a user can pass to the module
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ibmcloud_utils.ibmcloud import Terraform, ibmcloud_terraform
module_args = dict(
    hostname=dict(
        required=True,
        type='str'),
    datacenter=dict(
        required=False,
        type='str'),
    cores=dict(
        required=False,
        type='int'),
    power_state=dict(
        required=False,
        type='str'),
    public_ipv6_subnet=dict(
        required=False,
        type='str'),
    private_interface_id=dict(
        required=False,
        type='int'),
    ipv4_address_private=dict(
        required=False,
        type='str'),
    ip_address_id=dict(
        required=False,
        type='int'),
    ipv6_address=dict(
        required=False,
        type='str'),
    secondary_ip_count=dict(
        required=False,
        type='int'),
    domain=dict(
        required=True,
        type='str'),
    last_known_power_state=dict(
        required=False,
        type='str'),
    public_subnet_id=dict(
        required=False,
        type='int'),
    private_subnet_id=dict(
        required=False,
        type='int'),
    ipv4_address=dict(
        required=False,
        type='str'),
    ip_address_id_private=dict(
        required=False,
        type='int'),
    public_ipv6_subnet_id=dict(
        required=False,
        type='str'),
    status=dict(
        required=False,
        type='str'),
    public_interface_id=dict(
        required=False,
        type='int'),
    most_recent=dict(
        default=False,
        type='bool'),
    ipv6_address_id=dict(
        required=False,
        type='int'),
    secondary_ip_addresses=dict(
        required=False,
        elements='',
        type='list'),
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
        resource_type='ibm_compute_vm_instance',
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
