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
module: aws_dynamodb_item
short_description: Creates, updates or deletes single items in AWS Dynamo DB tables.
description:
    - Creates, updates or deletes single items in AWS DynamoDB tables.
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
    state:
        description:
          - If present, adds a new item or edits an existing item's attributes
            if it already exist. You can also perform a
            conditional update on an existing item (insert a new attribute
            name-value pair if it doesn't exist, or replace an existing
            name-value pair if it has certain expected attribute values).
          - If absent, deletes a single item in a table by primary key.
            You can perform a conditional delete operation that deletes the item
            if it exists, or if it has an expected attribute value.
        required: true
        choices: ["present", "absent"]
    primary_key:
        description:
            - The primary key of the DynamoDB table. Each element consists of
              an attribute name and a value for that attribute. For a composite
              primary key, you must provide values for both the partition key
              and the sort key.
        required: true
        default: null
        type: dict
    update_expression:
        description:
            - An expression that defines one or more attributes to be updated,
              the action to be performed on them, and new value(s) for them.
        required: false
        default: null
        type: str
    condition_expression:
        description:
            - A condition that must be satisfied in order for a conditional
              update to succeed.
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
    expression_attribute_values:
        description:
            - One or more values that can be substituted in an expression self.
              Use the ':' (colon) character in an expression to dereference
              an attribute value.
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
# Creates a single item in 'narcos' DynamoDB table where column 'bank' equals 'hsbc' string,
# column 'quantity' equals '1000' numeric and column 'person' equals 'ochoa' string
- name: Creates a new record
  aws_dynamodb_item:
    table: narcos
    state: present
    primary_key: {"bank": {"S": "hsbc"}}
    update_expression: 'SET quantity =:number, person=:person'
    expression_attribute_values: {":number": {"N": "1000"}, ":person": {"S": "ochoa"}}

# Updates the 'quantity' attibute value from a single item.
- name: Updates arribute 'number'
  aws_dynamodb_item:
    table: narcos
    state: present
    primary_key: {"bank": {"S": "hsbc"}}
    update_expression: 'SET quantity =:number'
    expression_attribute_values: {":number": {"N": "2000"}}

# Updates the 'status' (dynamodb protected keyword) attibute value from a single item.
- name: Updates arribute 'status'
  aws_dynamodb_item:
    table: narcos
    state: present
    primary_key: {"bank": {"S": "hsbc"}}
    update_expression: 'SET #s = :number'
    expression_attribute_values: {":number": {"N": "2000"}}
    expression_attribute_names: {"#s" : "status"}

# Deletes the 'person' attibute value from a single item. The table has a composite
# primary key. 'bank' is the primary key and 'quantity' is the sort key.
- name: Deletes arribute 'person'
  aws_dynamodb_item:
    table: narcos
    state: present
    primary_key: {"bank": {"S": "hsbc"}, "quantity": {"N": "1000"}}
    update_expression: 'REMOVE person'

# Connects with awscli profile 'development' and
# deletes a single item from 'releases' DynamoDB table
# where the column 'project' equals string 'potatoes' (also primary key)
# and column 'version' equals numeric '123456'
- name: Delete a single item
  aws_dynamodb_item:
    profile: development
    table: releases
    state: absent
    primary_key: {"project": {"S": "potatoes"}}
    condition_expression: version = :number
    expression_attribute_values: {":number": {"N": "123456"}}
'''

RETURN = '''
returned_items:
    description: item when you peform a 'get' action
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
    description: the number of total items evaluated when you peform a 'get' action
    returned: success
    type: int
    sample: 9589
consumed_capacity:
    description: the capacity units when you peform a 'get' action
    returned: success
    type: dict
count:
    description: the number of items in the response when you perform a 'get' action
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

from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    import botocore
except ImportError:
    pass    # Handled by AnsibleAWSModule


def update(connection, module, response, **params):

    try:
        if not module.check_mode:
            response = connection.update_item(**params)
        changed = True
        return response, changed
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
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


def delete(connection, module, response, **params):

    try:
        if not module.check_mode:
            response = connection.delete_item(**params)
        changed = True
        return response, changed
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            module.fail_json_aws(e, msg="Table {0} doesnt exist".format(
                module.params.get('table')))
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            module.fail_json_aws(
                e, msg="No item matching your conditional expression")
        if e.response['Error']['Message'] == 'The provided key element does not match the schema':
            module.fail_json_aws(
                e, msg="Check the primary key, it doesnt match your table config")
        else:
            module.fail_json_aws(e, msg="Error")


def main():
    argument_spec = dict(
        table=dict(required=True),
        state=dict(required=True, choices=['present', 'absent']),
        primary_key=dict(required=True, type='dict'),
        condition_expression=dict(type='str'),
        expression_attribute_names=dict(type='dict'),
        expression_attribute_values=dict(type='dict'),
        update_expression=dict(type='str')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    connection = module.client('dynamodb')
    state = module.params.get('state')

    params = {}

    params['TableName'] = module.params.get('table')
    params['Key'] = module.params.get('primary_key')

    if module.params.get('condition_expression') is not None:
        params['ConditionExpression'] = module.params.get('condition_expression')
    if module.params.get('update_expression') is not None:
        params['UpdateExpression'] = module.params.get('update_expression')
    if module.params.get('expression_attribute_names') is not None:
        params['ExpressionAttributeNames'] = module.params.get('expression_attribute_names')
    if module.params.get('expression_attribute_values') is not None:
        params['ExpressionAttributeValues'] = module.params.get('expression_attribute_values')

    changed = False
    response = {}

    if state == 'present':
        response, changed = update(connection, module, response, **params)

    elif state == 'absent':
        response, changed = delete(connection, module, response, **params)

    result = dict(changed=changed, **camel_dict_to_snake_dict(response))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
