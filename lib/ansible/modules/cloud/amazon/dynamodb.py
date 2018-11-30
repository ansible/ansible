#!/usr/bin/python
# Copyright: (c) 2018, David C Martin @blastikman
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: dynamodb
short_description: Reads, creates, updates or deletes single items in AWS Dynamo DB tables.
description:
    - Reads, creates, updates or deletes single items in AWS Dynamo DB tables.
    - More infomation can be found here U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#client).
version_added: "2.8"
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
            - Action to perform with the DyamoDB item.
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
            - One or more values that can be substituted in an expressionself.
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
    description: Item when you peform a 'get' action.
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
last_evaluated_key:
    description: Last evaluated key when you peform a 'get' action (scans a table)
    returned: success
    type: dict
    sample:
        {
            "bank": {
                "s": "hsbc"
            },
            "quantity": {
                "n": "1000"
            }
        }
response_metadata:
  description: response metadata about the snapshot
  returned: always
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

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict


try:
    import botocore
except ImportError:
    pass    # Handled by AnsibleAWSModule


def get(connection, table, filter_expression, expression_attribute_names,
        expression_attribute_values):

    if expression_attribute_names:
        response = connection.scan(
            TableName=table,
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names
        )
    else:
        response = connection.scan(
            TableName=table,
            ExpressionAttributeValues=expression_attribute_values,
            FilterExpression=filter_expression
        )

    changed = False

    response['returned_items'] = response.pop('Items')

    return response, changed


def put(connection, table, item):

    response = connection.put_item(
        TableName=table,
        Item=item,
    )

    changed = True
    return response, changed


def update(connection, table, primary_key, update_expression,
           condition_expression, expression_attribute_names,
           expression_attribute_values):

    if condition_expression:
        response = connection.update_item(TableName=table, Key=primary_key, UpdateExpression=update_expression,
                                          ConditionExpression=condition_expression, ExpressionAttributeValues=expression_attribute_values)
    elif expression_attribute_names:
        response = connection.update_item(TableName=table, Key=primary_key, UpdateExpression=update_expression,
                                          ExpressionAttributeValues=expression_attribute_values, ExpressionAttributeNames=expression_attribute_names)
    elif update_expression and expression_attribute_values:
        response = connection.update_item(TableName=table, Key=primary_key, UpdateExpression=update_expression,
                                          ExpressionAttributeValues=expression_attribute_values)
    else:
        response = connection.update_item(
            TableName=table, Key=primary_key, UpdateExpression=update_expression)

    changed = True
    return response, changed


def delete(connection, table, primary_key, condition_expression,
           expression_attribute_values):

    response = connection.delete_item(TableName=table, Key=primary_key, ConditionExpression=condition_expression,
                                      ExpressionAttributeValues=expression_attribute_values)

    changed = True
    return response, changed


def main():
    argument_spec = dict(
        table=dict(required=True),
        action=dict(required=True, choices=["get", "put", "update", "delete"]),
        primary_key=dict(required=False, type='dict'),
        filter_expression=dict(required=False, type='str'),
        item=dict(required=False, type='dict'),
        condition_expression=dict(required=False, type='str'),
        expression_attribute_names=dict(required=False, type='dict'),
        expression_attribute_values=dict(required=False, type='dict'),
        update_expression=dict(required=False, type='str')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=False)

    connection = module.client('dynamodb')

    try:
        table = module.params.get('table')
        action = module.params.get('action')
        primary_key = module.params.get('primary_key')
        filter_expression = module.params.get('filter_expression')
        condition_expression = module.params.get('condition_expression')
        item = module.params.get('item')
        update_expression = module.params.get('update_expression')
        expression_attribute_names = module.params.get(
            'expression_attribute_names')
        expression_attribute_values = module.params.get(
            'expression_attribute_values')

        changed = False
        response = {}

        if action == 'get':
            response, changed = get(
                connection, table, filter_expression,
                expression_attribute_names, expression_attribute_values)

        elif action == 'put':
            response, changed = put(connection, table, item)

        elif action == 'update':
            response, changed = update(connection, table, primary_key, update_expression,
                                       condition_expression, expression_attribute_names,
                                       expression_attribute_values)

        elif action == 'delete':
            response, changed = delete(connection, table, primary_key,
                                       condition_expression, expression_attribute_values)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            module.fail_json_aws(e, msg="Table {0} doesnt exist".format(table))
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            module.fail_json_aws(
                e, msg="No item matching your conditional expression")
        if e.response['Error']['Message'] == 'The provided key element does not match the schema':
            module.fail_json_aws(
                e, msg="Check the primary key, it doesnt match your table config")
        else:
            raise
    except botocore.exceptions.BotoCoreError as e:
        raise

    result = dict(changed=changed, **camel_dict_to_snake_dict(response))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
