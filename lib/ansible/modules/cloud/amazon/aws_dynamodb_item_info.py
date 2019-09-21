#!/usr/bin/python
# Copyright: (c) 2018, David C Martin @blastik
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_dynamodb_item_info
short_description: Reads items from AWS Dynamo DB tables.
description:
    - Reads items from AWS Dynamo DB tables.
    - More infomation can be found here U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#client).
version_added: "2.9"
author: "David C. Martin (@blastik)"
options:
    table:
        description:
            - Name of the DynamoDB table.
        required: true
        default: null
        type: str
    primary_key:
        description:
            - The primary key of the DynamoDB table. Each element consists of
              an attribute name and a value for that attribute. For a composite
              primary key, you must provide values for both the partition key
              and the sort key.
        required: true
        default: null
        type: dict
    consistent_read:
        description:
            - Determines the read consistency model.
              If set to true, then the operation uses strongly consistent
              reads; otherwise, the operation uses eventually consistent reads.
        required: false
        choices: ["True", "False"]
        default: null
        type: bool
    return_consumed_capacity:
        description:
            - Determines the level of detail about provisioned throughput
              consumption that is returned in the response.
        required: false
        choices: ["INDEXES", "TOTAL", "NONE"]
        default: null
        type: str
    projection_expression:
        description:
            - A string that identifies one or more attributes to retrieve from the table.
              More info U(https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.AccessingItemAttributes.html)
        required: false
        default: null
        type: str
    expression_attribute_names:
        description:
            - One or more substitution tokens for attribute names in an
              expression to access an attribute whose name conflicts with a
              DynamoDB reserved word.
              Reserved keywords list U(https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ReservedWords.html)
        required: false
        default: null
        type: dict
requirements:
    - boto3
    - botocore
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Returns a set of attributes for the item with the given primary key.
- name: Gets a single item
  aws_dynamodb_item_info:
    table: narcos
    primary_key: {"bank": {"S": "hsbc"}}

- name: Gets a single item returning the value for project field (where 'project' is a dynamodb protected keyword)
  aws_dynamodb_item_info:
    table: narcos
    primary_key: {"bank": {"S": "hsbc"}}
    projection_expression: #p
    expression_attribute_names: {"#p" : "project"}
'''

RETURN = '''
returned_items:
    description: item returned
    returned: success
    type: list
    sample:
        [
            {
                "bank": {
                    "s": "hsbc"
                },
                "quantity": {
                    "n": "1000"
                },
                "person": {
                    "s": "ochoa"
                }
            }
        ]
scanned_count:
    description: the number of total items evaluated
    returned: success
    type: int
    sample: 9589
consumed_capacity:
    description: the capacity units when you set 'return_consumed_capacity' to a value
    returned: success
    type: dict
count:
    description: the number of items in the response
    returned: success
    type: int
    sample: 13
response_metadata:
  description: aws response metadata
  returned: success
  type: dict
  sample:
    http_headers:
      content-length: 1490
      content-type: text/xml
      date: Tue, 07 Feb 2017 16:43:04 GMT
      x-amz-crc32: 2745614147
      x-amzn-requestid: 7f436dea-ed54-11e6-a04c-ab2372a1f14d
    http_status_code: 200
    request_id: 7f436dea-ed54-11e6-a04c-ab2372a1f14d
    retry_attempts: 0
'''

from ansible.module_utils.ec2 import camel_dict_to_snake_dict, AWSRetry
from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    import botocore
except ImportError:
    pass    # Handled by AnsibleAWSModule


@AWSRetry.exponential_backoff(retries=3, delay=2)
def get_with_backoff(connection, **kwargs):
    paginator = connection.get_paginator('scan')
    return paginator.paginate(**kwargs).build_full_result()


def get(connection, module, response, **params):
    response = get_with_backoff(connection, **params)
    response['returned_items'] = response.pop('Items')
    return response, changed


def main():
    argument_spec = dict(
        table=dict(required=True),
        primary_key=dict(required=True, type='dict'),
        consistent_read=dict(type='bool'),
        return_consumed_capacity=dict(type='str', choices=['INDEXES', 'TOTAL', 'NONE']),
        projection_expression=dict(type='str'),
        expression_attribute_names=dict(type='dict')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('dynamodb')

    params = {}

    params['TableName'] = module.params.get('table')
    params['Key'] = module.params.get('primary_key')

    if module.params.get('consistent_read') is not None:
        params['ConsistentRead'] = module.params.get('consistent_read')
    if module.params.get('return_consumed_capacity') is not None:
        params['ReturnConsumedCapacity'] = module.params.get('return_consumed_capacity').upper()
    if module.params.get('projection_expression') is not None:
        params['ProjectionExpression'] = module.params.get('projection_expression')
    if module.params.get('expression_attribute_names') is not None:
        params['ExpressionAttributeNames'] = module.params.get('expression_attribute_names')

    changed = False
    response = {}

    try:
        if not module.check_mode:
            response, changed = get(connection, module, response, **params)
        return response, changed

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            module.fail_json_aws(e, msg="Table {0} doesnt exist".format(
                module.params.get('table')))
        if e.response['Error']['Message'] == 'The provided key element does not match the schema':
            module.fail_json_aws(
                e, msg="Check the primary key, it doesnt match your table config")
        if 'Attribute name is a reserved keyword' in e.response['Error']['Message']:
            module.fail_json_aws(
                e, msg='''You are trying to use a DynamoDB reserved word,
                see https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ReservedWords.html
                Use expression_attribute_names to deal with this case.''')
        if 'contains invalid key' in e.response['Error']['Message']:
            module.fail_json_aws(
                e, msg='''You are trying to use a DynamoDB reserved word,
                see https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ReservedWords.html
                Use expression_attribute_names to deal with this case.''')
        else:
            module.fail_json_aws(e, msg="Error")

    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Error")

    result = dict(changed=changed, **camel_dict_to_snake_dict(response))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
