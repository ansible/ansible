#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_s3_cors
short_description: Manage CORS for S3 buckets in AWS
description:
    - Manage CORS for S3 buckets in AWS
version_added: "2.5"
author: "Oyvind Saltvik (@fivethreeo)"
options:
  name:
    description:
      - Name of the s3 bucket
    required: true
  rules:
    description:
      - Cors rules to put on the s3 bucket
  state:
    description:
      - Create or remove cors on the s3 bucket
    required: true
    choices: [ 'present', 'absent' ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a simple cors for s3 bucket
- aws_s3_cors:
    name: mys3bucket
    state: present
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
- aws_s3_cors:
    name: mys3bucket
    state: absent
'''

RETURN = '''
changed:
  description: check to see if a change was made to the rules
  returned: always
  type: bool
  sample: true
name:
  description: name of bucket
  returned: always
  type: str
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

try:
    from botocore.exceptions import ClientError, BotoCoreError
except Exception:
    # handled by HAS_BOTO3 check in main
    pass

import traceback

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (HAS_BOTO3, boto3_conn, ec2_argument_spec, get_aws_connection_info,
                                      camel_dict_to_snake_dict, snake_dict_to_camel_dict, compare_policies)


def create_or_update_bucket_cors(connection, module):

    name = module.params.get("name")
    rules = module.params.get("rules", [])
    changed = False

    try:
        current_camel_rules = connection.get_bucket_cors(Bucket=name)['CORSRules']
    except ClientError:
        current_camel_rules = []

    new_camel_rules = snake_dict_to_camel_dict(rules, capitalize_first=True)
    # compare_policies() takes two dicts and makes them hashable for comparison
    if compare_policies(new_camel_rules, current_camel_rules):
        changed = True

    if changed:
        try:
            cors = connection.put_bucket_cors(Bucket=name, CORSConfiguration={'CORSRules': new_camel_rules})
        except ClientError as e:
            module.fail_json(
                msg="Unable to update CORS for bucket {0}: {1}".format(name, to_native(e)),
                exception=traceback.format_exc(),
                **camel_dict_to_snake_dict(e.response)
            )
        except BotoCoreError as e:
            module.fail_json(
                msg=to_native(e),
                exception=traceback.format_exc()
            )

    module.exit_json(changed=changed, name=name, rules=rules)


def destroy_bucket_cors(connection, module):

    name = module.params.get("name")
    changed = False

    try:
        cors = connection.delete_bucket_cors(Bucket=name)
        changed = True
    except ClientError as e:
        module.fail_json(
            msg="Unable to delete CORS for bucket {0}: {1}".format(name, to_native(e)),
            exception=traceback.format_exc(),
            **camel_dict_to_snake_dict(e.response)
        )
    except BotoCoreError as e:
        module.fail_json(
            msg=to_native(e),
            exception=traceback.format_exc()
        )

    module.exit_json(changed=changed)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            rules=dict(type='list'),
            state=dict(type='str', choices=['present', 'absent'], required=True)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client = boto3_conn(module, conn_type='client', resource='s3',
                        region=region, endpoint=ec2_url, **aws_connect_kwargs)

    state = module.params.get("state")

    if state == 'present':
        create_or_update_bucket_cors(client, module)
    elif state == 'absent':
        destroy_bucket_cors(client, module)


if __name__ == '__main__':
    main()
