#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ec2_instance_facts
short_description: Gather facts about ec2 instances in AWS
description:
    - Gather facts about ec2 instances in AWS
version_added: "2.4"
author:
  - Michael Schuett (@michaeljs1990)
  - Rob White (@wimnat)
requirements: [ "boto3", "botocore" ]
options:
  instance_ids:
    description:
      - If you specify one or more instance IDs, only instances that have the specified IDs are returned.
    required: false
    version_added: 2.4
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See
        U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html) for possible filters. Filter
        names and values are case sensitive.
    required: false
    default: {}

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all instances
- ec2_instance_facts:

# Gather facts about all instances in AZ ap-southeast-2a
- ec2_instance_facts:
    filters:
      availability-zone: ap-southeast-2a

# Gather facts about a particular instance using ID
- ec2_instance_facts:
    instance_ids:
      - i-12345678

# Gather facts about any instance with a tag key Name and value Example
- ec2_instance_facts:
    filters:
      "tag:Name": Example

# Gather facts about any instance in states "shutting-down", "stopping", "stopped"
- ec2_instance_facts:
    filters:
      instance-state-name: [ "shutting-down", "stopping", "stopped" ]

'''

RETURN = '''
instances:
    description: a list of ec2 instances
    returned: always
    type: complex
    contains:
        ami_launch_index:
            description: The AMI launch index, which can be used to find this instance in the launch group.
            returned: always
            type: int
            sample: 0
        architecture:
            description: The architecture of the image
            returned: always
            type: str
            sample: x86_64
        block_device_mappings:
            description: Any block device mapping entries for the instance.
            returned: always
            type: complex
            contains:
                device_name:
                    description: The device name exposed to the instance (for example, /dev/sdh or xvdh).
                    returned: always
                    type: str
                    sample: /dev/sdh
                ebs:
                    description: Parameters used to automatically set up EBS volumes when the instance is launched.
                    returned: always
                    type: complex
                    contains:
                        attach_time:
                            description: The time stamp when the attachment initiated.
                            returned: always
                            type: str
                            sample: "2017-03-23T22:51:24+00:00"
                        delete_on_termination:
                            description: Indicates whether the volume is deleted on instance termination.
                            returned: always
                            type: bool
                            sample: true
                        status:
                            description: The attachment state.
                            returned: always
                            type: str
                            sample: attached
                        volume_id:
                            description: The ID of the EBS volume
                            returned: always
                            type: str
                            sample: vol-12345678
        cpu_options:
            description: The CPU options set for the instance.
            returned: always if botocore version >= 1.10.16
            type: complex
            contains:
                core_count:
                     description: The number of CPU cores for the instance.
                     returned: always
                     type: int
                     sample: 1
                threads_per_core:
                     description: The number of threads per CPU core. On supported instance, a value of 1 means Intel Hyper-Threading Technology is disabled.
                     returned: always
                     type: int
                     sample: 1
        client_token:
            description: The idempotency token you provided when you launched the instance, if applicable.
            returned: always
            type: str
            sample: mytoken
        ebs_optimized:
            description: Indicates whether the instance is optimized for EBS I/O.
            returned: always
            type: bool
            sample: false
        hypervisor:
            description: The hypervisor type of the instance.
            returned: always
            type: str
            sample: xen
        iam_instance_profile:
            description: The IAM instance profile associated with the instance, if applicable.
            returned: always
            type: complex
            contains:
                arn:
                    description: The Amazon Resource Name (ARN) of the instance profile.
                    returned: always
                    type: str
                    sample: "arn:aws:iam::000012345678:instance-profile/myprofile"
                id:
                    description: The ID of the instance profile
                    returned: always
                    type: str
                    sample: JFJ397FDG400FG9FD1N
        image_id:
            description: The ID of the AMI used to launch the instance.
            returned: always
            type: str
            sample: ami-0011223344
        instance_id:
            description: The ID of the instance.
            returned: always
            type: str
            sample: i-012345678
        instance_type:
            description: The instance type size of the running instance.
            returned: always
            type: str
            sample: t2.micro
        key_name:
            description: The name of the key pair, if this instance was launched with an associated key pair.
            returned: always
            type: str
            sample: my-key
        launch_time:
            description: The time the instance was launched.
            returned: always
            type: str
            sample: "2017-03-23T22:51:24+00:00"
        monitoring:
            description: The monitoring for the instance.
            returned: always
            type: complex
            contains:
                state:
                    description: Indicates whether detailed monitoring is enabled. Otherwise, basic monitoring is enabled.
                    returned: always
                    type: str
                    sample: disabled
        network_interfaces:
            description: One or more network interfaces for the instance.
            returned: always
            type: complex
            contains:
                association:
                    description: The association information for an Elastic IPv4 associated with the network interface.
                    returned: always
                    type: complex
                    contains:
                        ip_owner_id:
                            description: The ID of the owner of the Elastic IP address.
                            returned: always
                            type: str
                            sample: amazon
                        public_dns_name:
                            description: The public DNS name.
                            returned: always
                            type: str
                            sample: ""
                        public_ip:
                            description: The public IP address or Elastic IP address bound to the network interface.
                            returned: always
                            type: str
                            sample: 1.2.3.4
                attachment:
                    description: The network interface attachment.
                    returned: always
                    type: complex
                    contains:
                        attach_time:
                            description: The time stamp when the attachment initiated.
                            returned: always
                            type: str
                            sample: "2017-03-23T22:51:24+00:00"
                        attachment_id:
                            description: The ID of the network interface attachment.
                            returned: always
                            type: str
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
                        status:
                            description: The attachment state.
                            returned: always
                            type: str
                            sample: attached
                description:
                    description: The description.
                    returned: always
                    type: str
                    sample: My interface
                groups:
                    description: One or more security groups.
                    returned: always
                    type: list of complex
                    contains:
                        group_id:
                            description: The ID of the security group.
                            returned: always
                            type: str
                            sample: sg-abcdef12
                        group_name:
                            description: The name of the security group.
                            returned: always
                            type: str
                            sample: mygroup
                ipv6_addresses:
                    description: One or more IPv6 addresses associated with the network interface.
                    returned: always
                    type: complex
                    contains:
                        - ipv6_address:
                              description: The IPv6 address.
                              returned: always
                              type: str
                              sample: "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
                mac_address:
                    description: The MAC address.
                    returned: always
                    type: str
                    sample: "00:11:22:33:44:55"
                network_interface_id:
                    description: The ID of the network interface.
                    returned: always
                    type: str
                    sample: eni-01234567
                owner_id:
                    description: The AWS account ID of the owner of the network interface.
                    returned: always
                    type: str
                    sample: 01234567890
                private_ip_address:
                    description: The IPv4 address of the network interface within the subnet.
                    returned: always
                    type: str
                    sample: 10.0.0.1
                private_ip_addresses:
                    description: The private IPv4 addresses associated with the network interface.
                    returned: always
                    type: list of complex
                    contains:
                        association:
                            description: The association information for an Elastic IP address (IPv4) associated with the network interface.
                            returned: always
                            type: complex
                            contains:
                                ip_owner_id:
                                    description: The ID of the owner of the Elastic IP address.
                                    returned: always
                                    type: str
                                    sample: amazon
                                public_dns_name:
                                    description: The public DNS name.
                                    returned: always
                                    type: str
                                    sample: ""
                                public_ip:
                                    description: The public IP address or Elastic IP address bound to the network interface.
                                    returned: always
                                    type: str
                                    sample: 1.2.3.4
                        primary:
                            description: Indicates whether this IPv4 address is the primary private IP address of the network interface.
                            returned: always
                            type: bool
                            sample: true
                        private_ip_address:
                            description: The private IPv4 address of the network interface.
                            returned: always
                            type: str
                            sample: 10.0.0.1
                source_dest_check:
                    description: Indicates whether source/destination checking is enabled.
                    returned: always
                    type: bool
                    sample: true
                status:
                    description: The status of the network interface.
                    returned: always
                    type: str
                    sample: in-use
                subnet_id:
                    description: The ID of the subnet for the network interface.
                    returned: always
                    type: str
                    sample: subnet-0123456
                vpc_id:
                    description: The ID of the VPC for the network interface.
                    returned: always
                    type: str
                    sample: vpc-0123456
        placement:
            description: The location where the instance launched, if applicable.
            returned: always
            type: complex
            contains:
                availability_zone:
                    description: The Availability Zone of the instance.
                    returned: always
                    type: str
                    sample: ap-southeast-2a
                group_name:
                    description: The name of the placement group the instance is in (for cluster compute instances).
                    returned: always
                    type: str
                    sample: ""
                tenancy:
                    description: The tenancy of the instance (if the instance is running in a VPC).
                    returned: always
                    type: str
                    sample: default
        private_dns_name:
            description: The private DNS name.
            returned: always
            type: str
            sample: ip-10-0-0-1.ap-southeast-2.compute.internal
        private_ip_address:
            description: The IPv4 address of the network interface within the subnet.
            returned: always
            type: str
            sample: 10.0.0.1
        product_codes:
            description: One or more product codes.
            returned: always
            type: list of complex
            contains:
                product_code_id:
                    description: The product code.
                    returned: always
                    type: str
                    sample: aw0evgkw8ef3n2498gndfgasdfsd5cce
                product_code_type:
                    description: The type of product code.
                    returned: always
                    type: str
                    sample: marketplace
        public_dns_name:
            description: The public DNS name assigned to the instance.
            returned: always
            type: str
            sample:
        public_ip_address:
            description: The public IPv4 address assigned to the instance
            returned: always
            type: str
            sample: 52.0.0.1
        root_device_name:
            description: The device name of the root device
            returned: always
            type: str
            sample: /dev/sda1
        root_device_type:
            description: The type of root device used by the AMI.
            returned: always
            type: str
            sample: ebs
        security_groups:
            description: One or more security groups for the instance.
            returned: always
            type: list of complex
            contains:
                group_id:
                    description: The ID of the security group.
                    returned: always
                    type: str
                    sample: sg-0123456
                group_name:
                    description: The name of the security group.
                    returned: always
                    type: str
                    sample: my-security-group
        source_dest_check:
            description: Indicates whether source/destination checking is enabled.
            returned: always
            type: bool
            sample: true
        state:
            description: The current state of the instance.
            returned: always
            type: complex
            contains:
                code:
                    description: The low byte represents the state.
                    returned: always
                    type: int
                    sample: 16
                name:
                    description: The name of the state.
                    returned: always
                    type: str
                    sample: running
        state_transition_reason:
            description: The reason for the most recent state transition.
            returned: always
            type: str
            sample:
        subnet_id:
            description: The ID of the subnet in which the instance is running.
            returned: always
            type: str
            sample: subnet-00abcdef
        tags:
            description: Any tags assigned to the instance.
            returned: always
            type: dict
            sample:
        virtualization_type:
            description: The type of virtualization of the AMI.
            returned: always
            type: str
            sample: hvm
        vpc_id:
            description: The ID of the VPC the instance is in.
            returned: always
            type: dict
            sample: vpc-0011223344
'''

import traceback

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (ansible_dict_to_boto3_filter_list,
                                      boto3_conn, boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict,
                                      ec2_argument_spec, get_aws_connection_info)


def list_ec2_instances(connection, module):

    instance_ids = module.params.get("instance_ids")
    filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))

    try:
        reservations_paginator = connection.get_paginator('describe_instances')
        reservations = reservations_paginator.paginate(InstanceIds=instance_ids, Filters=filters).build_full_result()
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    # Get instances from reservations
    instances = []
    for reservation in reservations['Reservations']:
        instances = instances + reservation['Instances']

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_instances = [camel_dict_to_snake_dict(instance) for instance in instances]

    # Turn the boto3 result in to ansible friendly tag dictionary
    for instance in snaked_instances:
        instance['tags'] = boto3_tag_list_to_ansible_dict(instance.get('tags', []), 'key', 'value')

    module.exit_json(instances=snaked_instances)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            instance_ids=dict(default=[], type='list'),
            filters=dict(default={}, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[
                               ['instance_ids', 'filters']
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

    list_ec2_instances(connection, module)


if __name__ == '__main__':
    main()
