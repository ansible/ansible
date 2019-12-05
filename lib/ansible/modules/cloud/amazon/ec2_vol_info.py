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
module: ec2_vol_info
short_description: Gather information about ec2 volumes in AWS
description:
    - Gather information about ec2 volumes in AWS
    - This module was called C(ec2_vol_facts) before Ansible 2.9. The usage did not change.
version_added: "2.1"
requirements: [ boto3 ]
author: "Rob White (@wimnat)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVolumes.html) for possible filters.
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all volumes
- ec2_vol_info:

# Gather information about a particular volume using volume ID
- ec2_vol_info:
    filters:
      volume-id: vol-00112233

# Gather information about any volume with a tag key Name and value Example
- ec2_vol_info:
    filters:
      "tag:Name": Example

# Gather information about any volume that is attached
- ec2_vol_info:
    filters:
      attachment.status: attached

'''

# TODO: Disabled the RETURN as it was breaking docs building. Someone needs to
# fix this
RETURN = '''# '''

import traceback

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass  # caught by imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn, HAS_BOTO3, boto3_tag_list_to_ansible_dict
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, camel_dict_to_snake_dict


def get_volume_info(volume, region):

    attachment = volume["attachments"]

    volume_info = {
        'create_time': volume["create_time"],
        'id': volume["volume_id"],
        'encrypted': volume["encrypted"],
        'iops': volume["iops"] if "iops" in volume else None,
        'size': volume["size"],
        'snapshot_id': volume["snapshot_id"],
        'status': volume["state"],
        'type': volume["volume_type"],
        'zone': volume["availability_zone"],
        'region': region,
        'attachment_set': {
            'attach_time': attachment[0]["attach_time"] if len(attachment) > 0 else None,
            'device': attachment[0]["device"] if len(attachment) > 0 else None,
            'instance_id': attachment[0]["instance_id"] if len(attachment) > 0 else None,
            'status': attachment[0]["state"] if len(attachment) > 0 else None,
            'delete_on_termination': attachment[0]["delete_on_termination"] if len(attachment) > 0 else None
        },
        'tags': boto3_tag_list_to_ansible_dict(volume['tags']) if "tags" in volume else None
    }

    return volume_info


def describe_volumes_with_backoff(connection, filters):
    paginator = connection.get_paginator('describe_volumes')
    return paginator.paginate(Filters=filters).build_full_result()


def list_ec2_volumes(connection, module, region):

    # Replace filter key underscores with dashes, for compatibility, except if we're dealing with tags
    sanitized_filters = module.params.get("filters")
    for key in list(sanitized_filters):
        if not key.startswith("tag:"):
            sanitized_filters[key.replace("_", "-")] = sanitized_filters.pop(key)
    volume_dict_array = []

    try:
        all_volumes = describe_volumes_with_backoff(connection, ansible_dict_to_boto3_filter_list(sanitized_filters))
    except ClientError as e:
        module.fail_json(msg=e.response, exception=traceback.format_exc())

    for volume in all_volumes["Volumes"]:
        volume = camel_dict_to_snake_dict(volume, ignore_list=['Tags'])
        volume_dict_array.append(get_volume_info(volume, region))
    module.exit_json(volumes=volume_dict_array)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters=dict(default={}, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)
    if module._name == 'ec2_vol_facts':
        module.deprecate("The 'ec2_vol_facts' module has been renamed to 'ec2_vol_info'", version='2.13')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    connection = boto3_conn(
        module,
        conn_type='client',
        resource='ec2',
        region=region,
        endpoint=ec2_url,
        **aws_connect_params
    )

    list_ec2_volumes(connection, module, region)


if __name__ == '__main__':
    main()
