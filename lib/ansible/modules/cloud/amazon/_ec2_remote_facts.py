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
deprecated: Deprecated in 2.4. Use M(ec2_instance_facts) instead.
description:
    - Gather facts about ec2 instances in AWS
version_added: "2.0"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html) for possible filters.
    required: false
    default: null
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
