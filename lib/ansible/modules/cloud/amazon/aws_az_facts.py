#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = '''
module: aws_az_facts
short_description: Gather facts about availability zones in AWS.
description:
    - Gather facts about availability zones in AWS.
version_added: '2.5'
author: 'Henrique Rodrigues (@Sodki)'
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See
        U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeAvailabilityZones.html) for
        possible filters. Filter names and values are case sensitive. You can also use underscores
        instead of dashes (-) in the filter keys, which will take precedence in case of conflict.
    required: false
    default: {}
extends_documentation_fragment:
    - aws
    - ec2
requirements: [botocore, boto3]
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all availability zones
- aws_az_facts:

# Gather facts about a single availability zone
- aws_az_facts:
    filters:
      zone-name: eu-west-1a
'''

RETURN = '''
availability_zones:
    returned: on success
    description: >
        Availability zones that match the provided filters. Each element consists of a dict with all the information
        related to that available zone.
    type: list
    sample: "[
        {
            'messages': [],
            'region_name': 'us-west-1',
            'state': 'available',
            'zone_name': 'us-west-1b'
        },
        {
            'messages': [],
            'region_name': 'us-west-1',
            'state': 'available',
            'zone_name': 'us-west-1c'
        }
    ]"
'''


import traceback
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import get_aws_connection_info, ec2_argument_spec, boto3_conn
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, camel_dict_to_snake_dict, HAS_BOTO3

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # will be detected by imported HAS_BOTO3


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters=dict(default={}, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

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

    # Replace filter key underscores with dashes, for compatibility
    sanitized_filters = dict((k.replace('_', '-'), v) for k, v in module.params.get('filters').items())

    try:
        availability_zones = connection.describe_availability_zones(
            Filters=ansible_dict_to_boto3_filter_list(sanitized_filters)
        )
    except ClientError as e:
        module.fail_json(msg="Unable to describe availability zones: {0}".format(to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except BotoCoreError as e:
        module.fail_json(msg="Unable to describe availability zones: {0}".format(to_native(e)),
                         exception=traceback.format_exc())

    # Turn the boto3 result into ansible_friendly_snaked_names
    snaked_availability_zones = [camel_dict_to_snake_dict(az) for az in availability_zones['AvailabilityZones']]

    module.exit_json(availability_zones=snaked_availability_zones)


if __name__ == '__main__':
    main()
