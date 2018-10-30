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
            - Name of the DynamoDB table.
        required: true
        default: null
        type: str
        choices:
          - get : Returns a set of attributes for the item with the given primary key.
          - put : Creates a new item, or replaces an old item with a new item. If an item that has the same primary key as the new item already exists in the specified table, the new item completely replaces the existing item.
          - update : Edits an existing item's attributes, or adds a new item to the table if it does not already exist. You can also perform a conditional update on an existing item (insert a new attribute name-value pair if it doesn't exist, or replace an existing name-value pair if it has certain expected attribute values).
          - delete : Deletes a single item in a table by primary key. You can perform a conditional delete operation that deletes the item if it exists, or if it has an expected attribute value.
    primary_key:
        description:
            - The primary key of the DynamoDB table. Each element consists of an attribute name and a value for that attribute. For a composite primary key, you must provide values for both the partition key and the sort key. Required when I(action=get) I(action=update) I(action=delete)
        required: false
        default: null
        type: dict
    projection_expression:
        description:
            - A string that identifies one or more attributes (separated by commas) to retrieve from the table. Required when I(action=get).
        required: false
        default: null
        type: str
    item:
        description:
            - A map of attribute name/value pairs, one for each attribute. Only the primary key attributes are required; you can optionally provide other attribute name-value pairs for the item. Required when I(action=put).
        required: false
        default: null
        type: dict
    update_expression:
        description:
            - An expression that defines one or more attributes to be updated, the action to be performed on them, and new value(s) for them.
        required: false
        default: null
        type: str
    condition_expression:
        description:
            - A condition that must be satisfied in order for a conditional update to succeed.
        required: false
        default: null
        type: str
    expression_attribute_names:
        description:
            - One or more substitution tokens for attribute names in an expression to access an attribute whose name conflicts with a DynamoDB reserved word. Reserved keywords list U(https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ReservedWords.html)
        required: false
        default: null
        type: dict
    expression_attribute_values:
        description:
            - One or more values that can be substituted in an expressionself. Use the ':' (colon) character in an expression to dereference an attribute value.
        required: false
        default: null
        type: dict
requirements:
    - boto3
    - botocore
'''

EXAMPLES = '''
# Returns a set of attributes for the item with the given primary key.
- name: Gets a single item
  dynamodb:
    profile: pre
    table: narcos
    action: get
    primary_key: {"bank": {"S": "hsbc"}}

# Creates a single item in 'narcos' DynamoDB table where column 'bank' equals 'hsbc' string,
# column 'quantity' equals '1000' numeric and column 'person' equals 'ochoa' string
- name: Creates a new record
  dynamodb:
    table: narcos
    action: put
    item: {"bank": {"S": "hsbc"},"quantity": {"N": "1000"},"person": {"S": "ochoa"}}

# Updates the 'quantity' attibute value from a single item.
- name: Updates arribute 'person'
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
item:
    description: Item when you peform a 'get' action.
    returned: success
    type: dict
    sample:
        {
            "bank": {
                "S": "hsbc"
            },
            "quantity": {
                "N": "1000"
            },
            "person": {
                "S": "ochoa"
            }
        }
'''

import ansible.module_utils.ec2
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto_exception


try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get(connection, table, primary_key, projection_expression, result):

    if projection_expression:
        response = connection.get_item(
            TableName=table,
            Key=primary_key,
            ProjectionExpression=projection_expression
        )
    else:
        response = connection.get_item(
            TableName=table,
            Key=primary_key
        )

    if 'Item' in response:
        result['item'] = response['Item']
    else:
        result = dict(failed=True, message='No item found')

    return result


def put(connection, table, item, result):

    connection.put_item(
        TableName=table,
        Item=item,
    )

    result = dict(changed=True, message='Item added')

    return result


def update(connection, table, primary_key, update_expression,
           condition_expression, expression_attribute_names,
           expression_attribute_values, result):

    if condition_expression:
        connection.update_item(
            TableName=table,
            Key=primary_key,
            UpdateExpression=update_expression,
            ConditionExpression=condition_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
    elif expression_attribute_names:
        connection.update_item(
            TableName=table,
            Key=primary_key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names
        )
    elif update_expression and expression_attribute_values:
        connection.update_item(
                TableName=table,
                Key=primary_key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
    else:
        connection.update_item(
            TableName=table,
            Key=primary_key,
            UpdateExpression=update_expression
        )

    result = dict(changed=True, message='Item updated')
    return result


def delete(connection, table, primary_key, condition_expression,
           expression_attribute_values, result):

    connection.delete_item(
        TableName=table,
        Key=primary_key,
        ConditionExpression=condition_expression,
        ExpressionAttributeValues=expression_attribute_values
    )

    result = dict(changed=True, message='Item deleted')

    return result


def main():
    argument_spec = ansible.module_utils.ec2.ec2_argument_spec()
    argument_spec.update(dict(
        table=dict(required=True),
        action=dict(required=True, choices=["get", "put", "update", "delete"]),
        primary_key=dict(required=False, type='dict'),
        item=dict(required=False, type='dict'),
        condition_expression=dict(required=False, type='str'),
        expression_attribute_names=dict(required=False, type='dict'),
        expression_attribute_values=dict(required=False, type='dict'),
        update_expression=dict(required=False, type='str'),
        projection_expression=dict(required=False, type='str')
    )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
    )

    if not HAS_BOTO3:
        module.fail_json(msg='pip modules boto3 and botocore are required')

    try:
        region, ec2_url, aws_connect_kwargs = ansible.module_utils.ec2.get_aws_connection_info(
            module, boto3=True)
        connection = ansible.module_utils.ec2.boto3_conn(module, conn_type='client',
                                                         resource='dynamodb',
                                                         region=region, endpoint=ec2_url,
                                                         **aws_connect_kwargs)
    except (botocore.exceptions.NoRegionError,
            botocore.exceptions.ProfileNotFound,
            botocore.exceptions.NoCredentialsError) as error:

        error_msg = boto_exception(error)
        module.fail_json(msg=error_msg)

    try:
        table = module.params.get('table')
        action = module.params.get('action')
        primary_key = module.params.get('primary_key')
        condition_expression = module.params.get('condition_expression')
        item = module.params.get('item')
        update_expression = module.params.get('update_expression')
        expression_attribute_names = module.params.get(
            'expression_attribute_names')
        expression_attribute_values = module.params.get(
            'expression_attribute_values')
        projection_expression = module.params.get('projection_expression')

        result = dict(
            changed=False,
            item=''
        )

        if action == 'get':
            result = get(connection, table, primary_key, projection_expression,
                         result)

        elif action == 'put':
            result = put(connection, table, item, result)

        elif action == 'update':
            result = update(connection, table, primary_key, update_expression,
                            condition_expression, expression_attribute_names,
                            expression_attribute_values, result)

        elif action == 'delete':
            result = delete(connection, table, primary_key,
                            condition_expression, expression_attribute_values,
                            result)

    except connection.exceptions.ResourceNotFoundException as error:
        error_msg = 'Table {0} not found'.format(table)
        module.fail_json(msg=error_msg)
    except connection.exceptions.ConditionalCheckFailedException as error:
        error_msg = 'No item matches the condition'
        module.fail_json(msg=error_msg)
    except Exception as error:
        error_msg = boto_exception(error)
        module.fail_json(msg=error_msg)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
