#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_eip_facts
short_description: List EC2 EIP details
description:
    - List details of EC2 Elastic IP addresses.
version_added: "2.6"
author: "Brad Macpherson (@iiibrad)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and filter
        value.  See U(https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-addresses.html#options)
        for possible filters. Filter names and values are case sensitive.
    required: false
    default: {}
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details or the AWS region,
# see the AWS Guide for details.

# List all EIP addresses in the current region.
- ec2_eip_facts:
  register: regional_eip_addresses

# List all EIP addresses for a VM.
- ec2_eip_facts:
    filters:
       instance-id: i-123456789
  register: my_vm_eips

- debug: msg="{{ my_vm_eips.addresses | json_query(\"[?private_ip_address=='10.0.0.5']\") }}"

# List all EIP addresses for several VMs.
- ec2_eip_facts:
    filters:
       instance-id:
         - i-123456789
         - i-987654321
  register: my_vms_eips

# List all EIP addresses using the 'Name' tag as a filter.
- ec2_eip_facts:
    filters:
      tag:Name: www.example.com
  register: my_vms_eips

# List all EIP addresses using the Allocation-id as a filter
- ec2_eip_facts:
    filters:
      allocation-id: eipalloc-64de1b01
  register: my_vms_eips

# Set the variable eip_alloc to the value of the first allocation_id
# and set the variable my_pub_ip to the value of the first public_ip
- set_fact:
    eip_alloc: my_vms_eips.addresses[0].allocation_id
    my_pub_ip: my_vms_eips.addresses[0].public_ip

'''


RETURN = '''
addresses:
  description: Properties of all Elastic IP addresses matching the provided filters. Each element is a dict with all the information related to an EIP.
  returned: on success
  type: list
  sample: [{
        "allocation_id": "eipalloc-64de1b01",
        "association_id": "eipassoc-0fe9ce90d6e983e97",
        "domain": "vpc",
        "instance_id": "i-01020cfeb25b0c84f",
        "network_interface_id": "eni-02fdeadfd4beef9323b",
        "network_interface_owner_id": "0123456789",
        "private_ip_address": "10.0.0.1",
        "public_ip": "54.81.104.1",
        "tags": {
            "Name": "test-vm-54.81.104.1"
        }
    }]

'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (ansible_dict_to_boto3_filter_list,
                                      boto3_tag_list_to_ansible_dict,
                                      camel_dict_to_snake_dict)
try:
    from botocore.exceptions import (BotoCoreError, ClientError)
except ImportError:
    pass  # caught by imported AnsibleAWSModule


def get_eips_details(module):
    connection = module.client('ec2')
    filters = module.params.get("filters")
    try:
        response = connection.describe_addresses(
            Filters=ansible_dict_to_boto3_filter_list(filters)
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(
            e,
            msg="Error retrieving EIPs")

    addresses = camel_dict_to_snake_dict(response)['addresses']
    for address in addresses:
        if 'tags' in address:
            address['tags'] = boto3_tag_list_to_ansible_dict(address['tags'])
    return addresses


def main():
    module = AnsibleAWSModule(
        argument_spec=dict(
            filters=dict(type='dict', default={})
        ),
        supports_check_mode=True
    )

    module.exit_json(changed=False, addresses=get_eips_details(module))


if __name__ == '__main__':
    main()
