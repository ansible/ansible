#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_eni_facts
short_description: Gather facts about ec2 ENI interfaces in AWS
description:
    - Gather facts about ec2 ENI interfaces in AWS
version_added: "2.0"
author: "Rob White (@wimnat)"
options:
  network_interface_ids:
    description:
      - If you specify one or more network interface IDs, only interfaces that have the specified IDs are returned.
    required: false
    version_added: 2.4
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See
        U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeNetworkInterfaces.html) for possible filters. Filter
        names and values are case sensitive.
    required: false
    default: {}

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all ENIs
- ec2_eni_facts:

# Gather facts about a particular ENI
- ec2_eni_facts:
    network_interface_ids:
      - eni-xxxxxxx

# Gather facts about an ENI associated with a particular security group name
- ec2_eni_facts:
    filters:
      group-name: my-security-group


'''

RETURN = '''
network_interfaces:
    description: a list of ec2 network interfaces
    returned: always
    type: complex
    contains:
        attachment:
            description: The network interface attachment.
            returned: always
            type: complex
            contains:
                attach_time:
                    description: The time stamp when the attachment initiated.
                    returned: always
                    type: string
                    sample: "2017-03-23T22:51:24+00:00"
                attachment_id:
                    description: The ID of the network interface attachment.
                    returned: always
                    type: string
                    sample: eni-attach-3aff3f
                delete_on_termination:
                    description: Indicates whether the network interface is deleted when the instance is terminated.
                    returned: always
                    type: bool
                    sample: true
                device_index:
                    description: The index of the device on the instance for the network interface attachment.
                    returned: always
                    type: int
                    sample: 0
                instance_id:
                    description: The ID of the instance.
                    returned: always
                    type: string
                    sample: i-3244532
                instance_id_owner:
                    description: The AWS account ID of the owner of the instance.
                    returned: always
                    type: string
                    sample: 0123456789
                status:
                    description: The attachment state.
                    returned: always
                    type: string
                    sample: attached
        availability_zone:
            description: The Availability Zone of the instance.
            returned: always
            type: string
            sample: ap-southeast-2a
        description:
            description: The description.
            returned: always
            type: string
            sample: My interface
        groups:
            description: One or more security groups.
            returned: always
            type: complex
            contains:
                - group_id:
                      description: The ID of the security group.
                      returned: always
                      type: string
                      sample: sg-abcdef12
                  group_name:
                      description: The name of the security group.
                      returned: always
                      type: string
                      sample: mygroup
        ipv6_addresses:
            description: One or more IPv6 addresses associated with the network interface.
            returned: always
            type: complex
            contains:
                - ipv6_address:
                      description: The IPv6 address.
                      returned: always
                      type: string
                      sample: "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        mac_address:
            description: The MAC address.
            returned: always
            type: string
            sample: "00:11:22:33:44:55"
        network_interface_id:
            description: The ID of the network interface.
            returned: always
            type: string
            sample: eni-01234567
        owner_id:
            description: The AWS account ID of the owner of the network interface.
            returned: always
            type: string
            sample: 01234567890
        private_ip_address:
            description: The IPv4 address of the network interface within the subnet.
            returned: always
            type: string
            sample: 10.0.0.1
        private_ip_addresses:
            description: The private IPv4 addresses associated with the network interface.
            returned: always
            type: complex
            contains:
                - association:
                      description: The association information for an Elastic IP address (IPv4) associated with the network interface.
                      returned: when EIP associated
                      type: complex
                      contains:
                          allocation_id:
                              description: The allocation ID.
                              returned: always
                              type: string
                              sample: alloc0id-324245
                          association_id:
                              description: The association ID.
                              returned: always
                              type: string
                              sample: assoc-id-345346
                          ip_owner_id:
                              description: The ID of the owner of the Elastic IP address.
                              returned: always
                              type: string
                              sample: amazon
                          public_dns_name:
                              description: The public DNS name.
                              returned: always
                              type: string
                              sample: ""
                          public_ip:
                              description: The public IP address or Elastic IP address bound to the network interface.
                              returned: always
                              type: string
                              sample: 1.2.3.4
                  primary:
                      description: Indicates whether this IPv4 address is the primary private IP address of the network interface.
                      returned: always
                      type: bool
                      sample: true
                  private_ip_address:
                      description: The private IPv4 address of the network interface.
                      returned: always
                      type: string
                      sample: 10.0.0.1
        requester_id:
            description: The ID of the entity that launched the instance on your behalf (for example, AWS Management Console or Auto Scaling).
            returned: always
            type: string
            sample: ASGFIO40340GDN0233DSA
        requester_managed:
            description: Indicates whether the network interface is being managed by AWS.
            returned: always
            type: bool
            sample: true
        source_dest_check:
            description: Indicates whether source/destination checking is enabled.
            returned: always
            type: bool
            sample: true
        status:
            description: The status of the network interface.
            returned: always
            type: string
            sample: in-use
        subnet_id:
            description: The ID of the subnet for the network interface.
            returned: always
            type: string
            sample: subnet-0123456
        tags:
            description: Any tags assigned to the interface.
            returned: always
            type: dict
            sample:
        vpc_id:
            description: The ID of the VPC for the network interface.
            returned: always
            type: string
            sample: vpc-0123456

'''

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

import copy
import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (ansible_dict_to_boto3_filter_list,
                                      boto3_conn, boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict,
                                      ec2_argument_spec, get_aws_connection_info)


def list_ec2_network_interfaces(connection, module):

    network_interface_ids = module.params.get("network_interface_ids")
    filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))

    try:
        network_interfaces = connection.describe_network_interfaces(NetworkInterfaceIds=network_interface_ids, Filters=filters)['NetworkInterfaces']
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_network_interfaces = []
    for network_interface in network_interfaces:
        # Copy the tags because we don't want to snake these
        if 'TagSet' in network_interface:
            tag_set_copy = copy.copy(network_interface['TagSet'])
        else:
            tag_set_copy = []

        snaked_network_interfaces.append(camel_dict_to_snake_dict(network_interface))
        network_interface['tags'] = boto3_tag_list_to_ansible_dict(tag_set_copy)
        del network_interface['tag_set']

    module.exit_json(network_interfaces=snaked_network_interfaces)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            network_interface_ids=dict(default=[], type='list'),
            filters=dict(default={}, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[
                               ['network_interface_ids', 'filters']
                           ],
                           supports_check_mode=True
                           )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    list_ec2_network_interfaces(connection, module)


if __name__ == '__main__':
    main()
