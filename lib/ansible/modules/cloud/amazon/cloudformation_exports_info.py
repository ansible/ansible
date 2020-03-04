#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: cloudformation_exports_info
short_description: Read a value from CloudFormation Exports
description:
  - Module retrieves a value from CloudFormation Exports
requirements: ['boto3 >= 1.11.15']
version_added: "2.10"
author:
  - "Michael Moyle (@mmoyle)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
- name: Get Exports
  cloudformation_exports_info:
    profile: 'my_aws_profile'
    region: 'my_region'
  register: cf_exports
- debug:
    msg: "{{ cf_exports }}"
'''

RETURN = '''
export_items:
    description: A dictionary of Exports items names and values.
    returned: Always
    type: dict
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry

try:
    from botocore.exceptions import ClientError
    from botocore.exceptions import BotoCoreError
except ImportError:
    pass  # handled by AnsibleAWSModule


@AWSRetry.exponential_backoff()
def list_exports(cloudformation_client):
    '''Get Exports Names and Values and return in dictionary '''
    list_exports_paginator = cloudformation_client.get_paginator('list_exports')
    exports = list_exports_paginator.paginate().build_full_result()['Exports']
    export_items = dict()

    for item in exports:
        export_items[item['Name']] = item['Value']

    return export_items


def main():
    argument_spec = dict()
    result = dict(
        changed=False,
        original_message=''
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=False)
    cloudformation_client = module.client('cloudformation')

    try:
        result['export_items'] = list_exports(cloudformation_client)

    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e)

    result.update()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
