#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: s3_cors
short_description: Manage CORS for S3 buckets in AWS
description:
    - Manage CORS for S3 buckets in AWS
version_added: "2.4"
author: "Oyvind Saltvik (@fivethreeo)"
options:
  name:
    description:
      - Name of the s3 bucket
    required: true
    default: null
  rules:
    description:
      - Cors rules to put on the s3 bucket
    required: false
  state:
    description:
      - Create or remove cors on the s3 bucket
    required: false
    default: present
    choices: [ 'present', 'absent' ]
extends_documentation_fragment:
    - aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a simple cors for s3 bucket
- s3_cors:
  name: mys3bucket
  rules:
    - allowed_origins:
        - http://www.example.com/
      allowed_methods:
        - GET
        - POST
      allowed_headers:
        - Authorization
      expose_headers:
        - x-amz-server-side-encryption
        - x-amz-request-id
      max_age_seconds: 30000

# Remove cors for s3 bucket
- s3_cors:
  name: mys3bucket
  state: absent
'''

RETURN = '''
changed:
  description: check to see if a change was made to the rules
  returned: always
  type: boolean
  sample: true
name:
  description: name of bucket
  returned: always
  type: string
  sample: 'bucket-name'
rules:
  description: list of current rules
  returned: always
  type: list
  sample: [
     {
        "allowed_headers": [
          "Authorization"
        ],
        "allowed_methods": [
          "GET"
        ],
        "allowed_origins": [
          "*"
        ],
        "max_age_seconds": 30000
      }
    ]
'''

import re

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info, snake_dict_to_camel_dict


def create_or_update_bucket_cors(connection, module):

    name = module.params.get("name")
    rules = module.params.get("rules", [])
    changed = False

    try:
        current_camel_rules = connection.get_bucket_cors(Bucket=name)['CORSRules']
    except ClientError as e:
        current_camel_rules = []

    new_camel_rules = snake_dict_to_camel_dict(rules)

    if not (len(new_camel_rules) == len(current_camel_rules)):
        changed = True

    if not changed:
        for rule_index, new_camel_rule in enumerate(new_camel_rules):
            if not changed:
                if not (new_camel_rule.keys() == current_camel_rules[rule_index].keys()):
                    changed = True
                    break
                for rule_key in new_camel_rule.keys():
                    if rule_key == 'MaxAgeSeconds':
                        if not (new_camel_rule[rule_key] == current_camel_rules[rule_index].get(rule_key, None)):
                            changed = True
                            break
                    else:
                        if not (set(new_camel_rule[rule_key]) == set(current_camel_rules[rule_index].get(rule_key, []))):
                            changed = True
                            break
            else:
                break

    if changed:
        try:
            cors = connection.put_bucket_cors(Bucket=name, CORSConfiguration={'CORSRules': new_camel_rules})
        except ClientError as e:
            module.fail_json(
              msg="Error putting bucket CORS", exception=traceback.format_exc(),
              **camel_dict_to_snake_dict(e.message))

    module.exit_json(changed=changed, name=name, rules=rules)


def destroy_bucket_cors(connection, module):

    name = module.params.get("name")
    changed = False

    try:
        cors = connection.delete_bucket_cors(Bucket=name)
        changed = True
    except ClientError as e:
        module.fail_json(
          msg="Error deleting bucket CORS", exception=traceback.format_exc(),
          **camel_dict_to_snake_dict(e.message))

    module.exit_json(changed=changed)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            rules=dict(type='list'),
            state=dict(type='str', choices=['present', 'absent'])
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    check_mode = module.check_mode
    try:
        region, ec2_url, aws_connect_kwargs = (
            get_aws_connection_info(module, boto3=True)
        )
        client = (
            boto3_conn(
                module, conn_type='client', resource='s3',
                region=region, endpoint=ec2_url, **aws_connect_kwargs
            )
        )
    except ClientError as e:
        module.fail_json(
          msg="Boto3 Client Error", exception=traceback.format_exc(),
          **camel_dict_to_snake_dict(e.message))

    state = module.params.get("state")

    if state == 'present':
        create_or_update_bucket_cors(client, module)
    elif state == 'absent':
        destroy_bucket_cors(client, module)

if __name__ == '__main__':
    main()
