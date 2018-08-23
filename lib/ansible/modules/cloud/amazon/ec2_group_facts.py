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
module: ec2_group_facts
short_description: Gather facts about ec2 security groups in AWS.
description:
    - Gather facts about ec2 security groups in AWS.
version_added: "2.3"
requirements: [ boto3 ]
author:
- Henrique Rodrigues (@Sodki)
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See \
      U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSecurityGroups.html) for \
      possible filters. Filter names and values are case sensitive. You can also use underscores (_) \
      instead of dashes (-) in the filter keys, which will take precedence in case of conflict.
    required: false
    default: {}
notes:
  - By default, the module will return all security groups. To limit results use the appropriate filters.

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all security groups
- ec2_group_facts:

# Gather facts about all security groups in a specific VPC
- ec2_group_facts:
    filters:
      vpc-id: vpc-12345678

# Gather facts about all security groups in a specific VPC
- ec2_group_facts:
    filters:
      vpc-id: vpc-12345678

# Gather facts about a security group
- ec2_group_facts:
    filters:
      group-name: example-1

# Gather facts about a security group by id
- ec2_group_facts:
    filters:
      group-id: sg-12345678

# Gather facts about a security group with multiple filters, also mixing the use of underscores as filter keys
- ec2_group_facts:
    filters:
      group_id: sg-12345678
      vpc-id: vpc-12345678

# Gather facts about various security groups
- ec2_group_facts:
    filters:
      group-name:
        - example-1
        - example-2
        - example-3

# Gather facts about any security group with a tag key Name and value Example. The quotes around 'tag:name' are important because of the colon in the value
- ec2_group_facts:
    filters:
      "tag:Name": Example
'''

RETURN = '''
security_groups:
    description: Security groups that match the provided filters. Each element consists of a dict with all the information related to that security group.
    type: list
    returned: always
    sample:
'''

import traceback

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass  # caught by imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (ec2_argument_spec, boto3_conn, HAS_BOTO3, get_aws_connection_info,
                                      boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_filter_list,
                                      camel_dict_to_snake_dict)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters=dict(default={}, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(
            module,
            conn_type='client',
            resource='ec2',
            region=region,
            endpoint=ec2_url,
            **aws_connect_params
        )
    else:
        module.fail_json(msg="region must be specified")

    # Replace filter key underscores with dashes, for compatibility, except if we're dealing with tags
    sanitized_filters = module.params.get("filters")
    for key in sanitized_filters:
        if not key.startswith("tag:"):
            sanitized_filters[key.replace("_", "-")] = sanitized_filters.pop(key)

    try:
        security_groups = connection.describe_security_groups(
            Filters=ansible_dict_to_boto3_filter_list(sanitized_filters)
        )
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc())

    snaked_security_groups = []
    for security_group in security_groups['SecurityGroups']:
        # Modify boto3 tags list to be ansible friendly dict
        # but don't camel case tags
        security_group = camel_dict_to_snake_dict(security_group)
        security_group['tags'] = boto3_tag_list_to_ansible_dict(security_group.get('tags', {}), tag_name_key_name='key', tag_value_key_name='value')
        snaked_security_groups.append(security_group)

    module.exit_json(security_groups=snaked_security_groups)


if __name__ == '__main__':
    main()
