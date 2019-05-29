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
short_description: Reads, creates, updates or deletes single items in AWS Dynamo DB tables.
description:
    - Reads, creates, updates or deletes single items in AWS Dynamo DB tables.
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
    action:
        description:
            - Action to perform with the DynamoDB item.
            - If get, returns a set of attributes for the item with the given
              filter expression. If the total number of scanned items exceeds
              the maximum data set size limit of 1 MB, the scan stops and
              results are returned to the user as a LastEvaluatedKey value to
              continue the scan in a subsequent operation. The results also
              include the number of items exceeding the limit.
              A scan can result in no table data meeting the filter criteria.
            - If put, creates a new item, or replaces an old item with a new item.
              If an item that has the same primary key as the new item
              already exists in the specified table, the new item completely
              replaces the existing item.
            - If update, edits an existing item's attributes, or adds a new item to the
              table if it does not already exist. You can also perform a
              conditional update on an existing item (insert a new attribute
              name-value pair if it doesn't exist, or replace an existing
              name-value pair if it has certain expected attribute values).
            - If delete, deletes a single item in a table by primary key. You can
              perform a conditional delete operation that deletes the item
              if it exists, or if it has an expected attribute value.
        required: true
        default: null
        type: str
        choices: [get, put, update, delete]
    filter_expression:
        description:
            - A string that contains conditions.
              Required when I(action=get)
        required: false
        default: null
        type: str
    primary_key:
        description:
            - The primary key of the DynamoDB table. Each element consists of
              an attribute name and a value for that attribute. For a composite
              primary key, you must provide values for both the partition key
              and the sort key.
              Required when I(action=update) I(action=delete)
        required: false
        default: null
        type: dict
    item:
        description:
            - A map of attribute name/value pairs, one for each attribute.
              Only the primary key attributes are required; you can optionally
              provide other attribute name-value pairs for the item.
              Required when I(action=put).
        required: false
        default: null
        type: dict
    update_expression:
        description:
            - An expression that defines one or more attributes to be updated,
              the action to be performed on them, and new value(s) for them.
            - C(update_expression) and C(condition_expression) are required together.
        required: false
        default: null
        type: str
    condition_expression:
        description:
            - A condition that must be satisfied in order for a conditional
              update to succeed.
            - C(update_expression) and C(condition_expression) are required together.
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
# Returns a set of attributes for the item with the given primary key.
- name: Gets a single item
  dynamodb:
    profile: pre
    table: narcos
    action: get
    filter_expression: 'bank = :bank_name AND quantity = :number'
    expression_attribute_values: {":bank_name": {"S": "hsbc"}, ":number": {"N": "2000"}}

- name: Gets a single item (where 'project' is a dynamodb protected keyword)
  dynamodb:
    profile: pre
    table: narcos
    action: get
    filter_expression: '#p = :project'
    expression_attribute_values: {":project": {"S": "narcos"}}
    expression_attribute_names: {"#p" : "project"}

# Creates a single item in 'narcos' DynamoDB table where column 'bank' equals 'hsbc' string,
# column 'quantity' equals '1000' numeric and column 'person' equals 'ochoa' string
- name: Creates a new record
  dynamodb:
    table: narcos
    action: put
    item: {"bank": {"S": "hsbc"},"quantity": {"N": "1000"},"person": {"S": "ochoa"}}

# Updates the 'quantity' attibute value from a single item.
- name: Updates arribute 'number'
  dynamodb:
    table: narcos
    action: update
    primary_key: {"bank": {"S": "hsbc"}}
    update_expression: 'SET quantity = :number'
    expression_attribute_values: {":number": {"N": "2000"}}

# Updates the 'status' (dynamodb protected keyword) attibute value from a single item.
- name: Updates arribute 'status'
  dynamodb:
    table: narcos
    action: update
    primary_key: {"bank": {"S": "hsbc"}}
    update_expression: 'SET #s = :number'
    expression_attribute_values: {":number": {"N": "2000"}}
    expression_attribute_names: {"#s" : "status"}

# Deletes the 'person' attibute value from a single item. The table has a composite
# primary key. 'bank' is the primary key and 'quantity' is the sort key.
- name: Deletes arribute 'person'
  dynamodb:
    table: narcos
    action: update
    primary_key: {"bank": {"S": "hsbc"}, "quantity": {"N": "1000"}}
    update_expression: 'REMOVE person'

# Connects with awscli profile 'development' and
# deletes a single item from 'releases' DynamoDB table
# where the column 'project' equals string 'potatoes' (also primary key)
# and column 'version' equals numeric '123456'
- name: Delete a single item
  dynamodb:
    profile: development
    table: releases
    action: delete
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

    changed = False

    response['returned_items'] = response.pop('Items')

    return response, changed


def put(connection, module, response, **params):
    if not module.check_mode:
        response = connection.put_item(**params)

    changed = True
    return response, changed


def update(connection, module, response, **params):

    if not module.check_mode:
        response = connection.update_item(**params)

    changed = True
    return response, changed


def delete(connection, module, response, **params):

    if not module.check_mode:
        response = connection.delete_item(**params)

    changed = True
    return response, changed


def main():
    argument_spec = dict(
        table=dict(required=True),
        action=dict(required=True, choices=["get", "put", "update", "delete"]),
        primary_key=dict(type='dict'),
        filter_expression=dict(type='str'),
        item=dict(type='dict'),
        condition_expression=dict(type='str'),
        expression_attribute_names=dict(type='dict'),
        expression_attribute_values=dict(type='dict'),
        update_expression=dict(type='str')
    )

    required_if = [
        ["action", "get", ['filter_expression', 'expression_attribute_values']],
        ["action", "put", ['item']],
        ["action", "update", ['primary_key', 'update_expression']],
        ["action", "delete", ['condition_expression', 'expression_attribute_values']]
    ]

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True,
                              required_if=required_if)

    connection = module.client('dynamodb')

    params = {}

    action = module.params.get('action')

    if module.params.get('table') is not None:
        params['TableName'] = module.params.get('table')
    if module.params.get('primary_key') is not None:
        params['Key'] = module.params.get('primary_key')
    if module.params.get('filter_expression') is not None:
        params['FilterExpression'] = module.params.get('filter_expression')
    if module.params.get('condition_expression') is not None:
        params['ConditionExpression'] = module.params.get('condition_expression')
    if module.params.get('item') is not None:
        params['Item'] = module.params.get('item')
    if module.params.get('update_expression') is not None:
        params['UpdateExpression'] = module.params.get('update_expression')
    if module.params.get('expression_attribute_names') is not None:
        params['ExpressionAttributeNames'] = module.params.get('expression_attribute_names')
    if module.params.get('expression_attribute_values') is not None:
        params['ExpressionAttributeValues'] = module.params.get('expression_attribute_values')

    changed = False
    response = {}

    try:
        if action == 'get':
            response, changed = get(connection, module, response, **params)

        elif action == 'put':
            response, changed = put(connection, module, response, **params)

        elif action == 'update':
            response, changed = update(connection, module, response, **params)

        elif action == 'delete':
            response, changed = delete(connection, module, response, **params)

    except botocore.exceptions.ClientError as e:
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

    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Error")

    result = dict(changed=changed, **camel_dict_to_snake_dict(response))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
