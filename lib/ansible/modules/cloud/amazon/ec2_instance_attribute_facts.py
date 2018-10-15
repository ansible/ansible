#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright, (c) 2018, Ansible Project
# Copyright, (c) 2018, Moshe Immerman
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_instance_attribute_facts
short_description: Get EC2 instance attribute facts
description:
    -  Get EC2 instance attribute facts
version_added: 2.8
author:
    - Moshe Immerman <moshe.immerman@gmail.com>
requirements: [ "boto3", "botocore" ]
options:
   instance_id:
        description:
            - EC2 Instance Id.
        required: True
   region:
         description:
            - AWS Region of the instance.
         required: True
   attribute:
        description:
            - See U(https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instance-attribute.html)
        required: True
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = """
# Note: These examples do not set authentication details, see the AWS Guide for details.
- ec2_instance_attribute_facts:
    instance_id: "{{ec2_instance.id}}"
    region: "{{region}}"
    attribute: "user_data"
  register: user_data_fact
- debug: msg="{{user_data_fact.attributes.user_data.value}}"
"""

RETURN = """
attributes:
    description:
        - A dictionary of instance attribute values.
        - See U(https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instance-attribute.html)
    returned: always
    type: dict
"""

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.common.dict_transformations import (camel_dict_to_snake_dict, _snake_to_camel)

try:
    import botocore.exceptions
except ImportError:
    pass  # caught by AnsibleAWSModule


def get_instance_attribute(connection, module):
    try:
        instance_id = module.params.get("instance_id")
        attribute = _snake_to_camel(module.params.get('attribute'))
        response = connection.describe_instance_attribute(Attribute=attribute, InstanceId=instance_id)
        return camel_dict_to_snake_dict(response)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Couldn't get instance attributes")


def main():
    argument_spec = dict(
        instance_id=dict(required=True),
        attribute=dict(required=True)
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    response = get_instance_attribute(module.client('ec2'), module)
    module.exit_json(attributes=response)


if __name__ == '__main__':
    main()
