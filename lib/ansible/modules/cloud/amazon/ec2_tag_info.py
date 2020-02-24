#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_tag_info
short_description: list tags on ec2 resources
description:
    - Lists tags for any EC2 resource.
    - Resources are referenced by their resource id (e.g. an instance being i-XXXXXXX, a vpc being vpc-XXXXXX).
    - Resource tags can be managed using the M(ec2_tag) module.
version_added: "2.10"
requirements: [ "boto3", "botocore" ]
options:
  resource:
    description:
      - The EC2 resource id (for example i-XXXXXX or vpc-XXXXXX).
    required: true
    type: str

author:
  - Mark Chappell (@tremble)
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
- name: Retrieve all tags on an instance
  ec2_tag_info:
    region: eu-west-1
    resource: i-xxxxxxxxxxxxxxxxx
  register: instance_tags

- name: Retrieve all tags on a VPC
  ec2_tag_info:
    region: eu-west-1
    resource: vpc-xxxxxxxxxxxxxxxxx
  register: vpc_tags
'''

RETURN = '''
tags:
  description: A dict containing the tags on the resource
  returned: always
  type: dict
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict, AWSRetry

try:
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:
    pass    # Handled by AnsibleAWSModule


@AWSRetry.jittered_backoff()
def get_tags(ec2, module, resource):
    filters = [{'Name': 'resource-id', 'Values': [resource]}]
    return boto3_tag_list_to_ansible_dict(ec2.describe_tags(Filters=filters)['Tags'])


def main():
    argument_spec = dict(
        resource=dict(required=True),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    resource = module.params['resource']
    ec2 = module.client('ec2')

    try:
        current_tags = get_tags(ec2, module, resource)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to fetch tags for resource {0}'.format(resource))

    module.exit_json(changed=False, tags=current_tags)


if __name__ == '__main__':
    main()
