#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: ec2_remote_facts
short_description: Gather facts about ec2 instances in AWS
deprecated:
  removed_in: "2.8"
  why: Replaced with boto3 version.
  alternative: Use M(ec2_instance_facts) instead.
description:
    - Gather facts about ec2 instances in AWS
version_added: "2.0"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html) for possible filters.
author:
    - "Michael Schuett (@michaeljs1990)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all ec2 instances
- ec2_remote_facts:

# Gather facts about all running ec2 instances with a tag of Name:Example
- ec2_remote_facts:
    filters:
      instance-state-name: running
      "tag:Name": Example

# Gather facts about instance i-123456
- ec2_remote_facts:
    filters:
      instance-id: i-123456

# Gather facts about all instances in vpc-123456 that are t2.small type
- ec2_remote_facts:
    filters:
      vpc-id: vpc-123456
      instance-type: t2.small

'''

RETURN = '''
instances:
    description: provides details about EC2 instance(s) found in AWS region
    returned: when EC2 instances are found in AWS region otherwise empty
    type: complex
    contains:
        ami_launch_index:
            description: >
                if more than one instance is started at the same time, this value indicates the order in which the instance was launched,
                the value of the first instance launched is 0
            returned: success
            type: string
            sample: "0"
        architecture:
            description: the instance architecture
            returned: success
            type: string
            sample: "x86_64"
        block_device_mapping:
            description: a structure describing the attached volumes to instance
            returned: success
            type: complex
            contains:
                attach_time:
                    description: the attach time for an EBS volume mapped to the instance
                    returned: success
                    type: string
                    sample: "2017-01-03T15:19:52.000Z"
                delete_on_termination:
                    description: indicates whether the EBS volume is deleted on instance termination
                    returned: success
                    type: boolean
                    sample: "true"
                device_name:
                    description: the device name for the EBS volume
                    returned: success
                    type: string
                    sample: "/dev/sda1"
                status:
                    description: the status for the EBS volume
                    returned: success
                    type: string
                    sample: "attaching"
                volume_id:
                    description: the volume id of the EBS volume
                    returned: success
                    type: string
                    sample: "vol-3160f90df06b24080"
        client_token:
            description: the idempotency token provided when instance was launched
            returned: success
            type: string
            sample: "Sample-awsmp-DFNBSML8ZMJ9"
        ebs_optimized:
            description: whether instance class has EBS optimized flag turned on
            returned: success
            type: boolean
            sample: "true"
        groups:
            description: a list security groups to which the network interface belongs
            returned: success
            type: complex
            contains:
                id:
                    description: security group id
                    returned: success
                    type: string
                    sample: "sg-e203cf94"
                name:
                    descriptipn: security group name
                    returned: success
                    type: string
                    sample: "Sample-Common-Sg"
        hypervisor:
            description: the hypervisor type of the instance
            returned: success
            type: string
            sample: "xen"
        id:
            description: the id of the instance
            returned: success
            type: string
            sample: "i-09275d68c04c1a16c"
        image_id:
            description: the id of the image used to launch the instance
            returned: success
            type: string
            sample: "ami-1748d2f5"
        instance_profile:
            description: the instance profile associated with the instance
            returned: success
            type: complex
            contains:
                arn:
                    description: specifies an ARN of instance profile
                    returned: success
                    type: string
                    sample: "arn:aws:iam::171455704129:instance-profile/Sample-IamProfile"
                id:
                    description: instance profile id
                    returned: success
                    type: string
                    sample: "AIPAD5WIZGNR9TH6LBFE4"
        interfaces:
            description: a list of ENI associated to instance
            returned: success
            type: complex
            contains:
                id:
                    description: the id of ENI
                    returned: success
                    type: string
                    sample: "eni-cf96b081"
                mac_address:
                    description: the MAC address of ENI
                    returned: success
                    type: string
                    sample: "06:c4:fd:90:dc:61"
        kernel:
            description: the kernel id
            returned: success
            type: string
            sample: "null"
        key_name:
            description: the name of the key pair used when the instance was launched
            returned: success
            type: string
            sample: "MyKey"
        launch_time":
            description: the time when the instance was launched
            returned: success
            type: string
            sample: "2017-06-16T15:44:54.000Z"
        monitoring_state:
            description: indicates whether detailed monitoring is enabled
            returned: success
            type: string
            sample: "disabled"
        private_dns_name:
            description: the private IPv4 DNS name of the instance
            returned: success
            type: string
            sample: "ip-10-21-39-23.ag-net.com"
        private_ip_address:
            description: the private IPv4 address of the instance
            returned: success
            type: string
            sample: "10.216.139.23"
        public_dns_name:
            description: the public DNS name of the instance
            returned: success
            type: string
            sample: "ec2-54-194-252-215.eu-west-1.compute.amazonaws.com"
        public_ip_address:
            description: the public IPv4 address of the instance
            returned: success
            type: string
            sample: "54.194.252.215"
        ramdisk:
            description: the RAM disk id
            returned: success
            type: string
            sample: "null"
        region:
            description: the AWS region in which instance is running in
            returned: success
            type: string
            sample: "eu-west-1"
        requester_id:
            description: the id of the entity that launched the instance on your behalf
            returned: success
            type: string
            sample: "null"
        root_device_type:
            description: the type of root device that the instance uses
            returned: success
            type: string
            sample: "ebs"
        source_destination_check:
            description: indicates whether the instance performs source/destination checking
            returned: success
            type: boolean
            sample: "true"
        spot_instance_request_id:
            description: the id of the spot instance request
            returned: success
            type: string
            sample: "null"
        state:
            description: a message that describes the state change
            returned: success
            type: string
            sample: "running"
        tags:
            description: a dictionary of key/value pairs assigned to the resource
            returned: success
            type: complex
            contains:
                key:
                    description: the key of a tag assigned to the resource
                    returned: success
                    type: string
                    sample: "Environment"
        virtualization_type:
            description: the virtualization type of the instance
            returned: success
            type: string
            sample: "hvm"
        vpc_id:
            description: the id of the VPC that the instance is running in
            returned: success
            type: string
            sample: "vpc-12c9ae4f"
'''

try:
    import boto.ec2
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import AnsibleAWSError, connect_to_aws, ec2_argument_spec, get_aws_connection_info


def get_instance_info(instance):

    # Get groups
    groups = []
    for group in instance.groups:
        groups.append({'id': group.id, 'name': group.name}.copy())

    # Get interfaces
    interfaces = []
    for interface in instance.interfaces:
        interfaces.append({'id': interface.id, 'mac_address': interface.mac_address}.copy())

    # If an instance is terminated, sourceDestCheck is no longer returned
    try:
        source_dest_check = instance.sourceDestCheck
    except AttributeError:
        source_dest_check = None

    # Get block device mapping
    try:
        bdm_dict = []
        bdm = getattr(instance, 'block_device_mapping')
        for device_name in bdm.keys():
            bdm_dict.append({
                'device_name': device_name,
                'status': bdm[device_name].status,
                'volume_id': bdm[device_name].volume_id,
                'delete_on_termination': bdm[device_name].delete_on_termination,
                'attach_time': bdm[device_name].attach_time
            })
    except AttributeError:
        pass

    instance_profile = dict(instance.instance_profile) if instance.instance_profile is not None else None

    instance_info = {'id': instance.id,
                     'kernel': instance.kernel,
                     'instance_profile': instance_profile,
                     'root_device_type': instance.root_device_type,
                     'private_dns_name': instance.private_dns_name,
                     'public_dns_name': instance.public_dns_name,
                     'ebs_optimized': instance.ebs_optimized,
                     'client_token': instance.client_token,
                     'virtualization_type': instance.virtualization_type,
                     'architecture': instance.architecture,
                     'ramdisk': instance.ramdisk,
                     'tags': instance.tags,
                     'key_name': instance.key_name,
                     'source_destination_check': source_dest_check,
                     'image_id': instance.image_id,
                     'groups': groups,
                     'interfaces': interfaces,
                     'spot_instance_request_id': instance.spot_instance_request_id,
                     'requester_id': instance.requester_id,
                     'monitoring_state': instance.monitoring_state,
                     'placement': {
                         'tenancy': instance._placement.tenancy,
                         'zone': instance._placement.zone
                     },
                     'ami_launch_index': instance.ami_launch_index,
                     'launch_time': instance.launch_time,
                     'hypervisor': instance.hypervisor,
                     'region': instance.region.name,
                     'persistent': instance.persistent,
                     'private_ip_address': instance.private_ip_address,
                     'public_ip_address': instance.ip_address,
                     'state': instance._state.name,
                     'vpc_id': instance.vpc_id,
                     'block_device_mapping': bdm_dict,
                     }

    return instance_info


def list_ec2_instances(connection, module):

    filters = module.params.get("filters")
    instance_dict_array = []

    try:
        all_instances = connection.get_only_instances(filters=filters)
    except BotoServerError as e:
        module.fail_json(msg=e.message)

    for instance in all_instances:
        instance_dict_array.append(get_instance_info(instance))

    module.exit_json(instances=instance_dict_array)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters=dict(default=None, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.ec2, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    list_ec2_instances(connection, module)


if __name__ == '__main__':
    main()
