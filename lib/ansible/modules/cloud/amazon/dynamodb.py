from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: dynamodb
<<<<<<< HEAD
short_description: Reads, creates, updates or deletes single items in AWS Dynamo DB tables.
version_added: "2.8"
description:
  - Reads, creates, updates or deletes single items in AWS Dynamo DB tables.
  More infomation can be found here:
  https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#client
=======
short_description: Reads, creates, updates or deletes items in AWS Dynamo DB tables.
version_added: "2.7"
>>>>>>> Merge branch 'dynamodb' into add_dynamodb
author:
  - David C. Martin @blastikman
requirements:
  - boto3
options:
  table:
<<<<<<< HEAD
    type: string
    required: true
    description:
      - Name of the DynamoDB table
  action:
    type: string
    required: true
=======
    description:
      - Name of the DynamoDB table
  action:
>>>>>>> Merge branch 'dynamodb' into add_dynamodb
    description:
      - "get": Returns a set of attributes for the item with
      the given primary key.
      - "put": Creates a new item, or replaces an old item with a new item.
      If an item that has the same primary key as the new item already exists
      in the specified table, the new item completely replaces the existing item.
<<<<<<< HEAD
      - "update": Edits an existing item's attributes, or adds a new item to the
      table if it does not already exist. You can also perform a conditional update on an
      existing item (insert a new attribute name-value pair if it doesn't exist,
      or replace an existing name-value pair if it has certain expected attribute values).
      - "delete": Deletes a single item in a table by primary key. You can
      perform a conditional delete operation that deletes the item if it exists,
      or if it has an expected attribute value.
    choices: [ 'get', 'put', 'update', 'delete' ]
  primary_key:
    type: dict
    description:
      - The primary key of the DynamoDB table. Each element consists of an
      attribute name and a value for that attribute. For a composite primary key,
      you must provide values for both the partition key and the sort key.
  projection_expression:
    type: string
    description:
      - A string that identifies one or more attributes (separated by commas)
      to retrieve from the table. Only to be used with action -get-.
  item:
    type: dict
    description:
      - A map of attribute name/value pairs, one for each attribute. Only the
      primary key attributes are required; you can optionally provide other
      attribute name-value pairs for the item. Only to be used with action -put-.
  update_expression:
    type: string
    description:
      - An expression that defines one or more attributes to be updated,
      the action to be performed on them, and new value(s) for them.
  condition_expression:
    type: string
    description:
      - A condition that must be satisfied in order for a conditional update to succeed.
  expression_attribute_values:
    type: dict
    description:
      - One or more values that can be substituted in an expressionself.
      Use the : (colon) character in an expression to dereference an attribute value.
"""

EXAMPLES = '''
# Returns a set of attributes for the item with the given primary key.
- name: Gets a single item
  dynamodb:
    profile: pre
    table: narcos
    action: get
    primary_key: {"bank": {"S": "hsbc"}}

=======
      - "delete": Deletes a single item in a table by primary key. You can
      perform a conditional delete operation that deletes the item if it exists,
       or if it has an expected attribute value.
  primary_key:
    description:
      -
  item:
    description:
      -
  update_expression:
    description:
      -
  update_expression:
    description:
      -
  update_expression:
    description:
      -
  update_expression:
    description:
      -
  update_expression:
    description:
      -
  update_expression:
    description:
      -


"""

EXAMPLES = '''
>>>>>>> Merge branch 'dynamodb' into add_dynamodb
# Creates a single item in 'narcos' DynamoDB table where column 'bank' equals 'hsbc' string,
# column 'quantity' equals '1000' numeric and column 'person' equals 'ochoa' string
- name: Creates a new record
  dynamodb:
    table: narcos
    action: put
    item: {"bank": {"S": "hsbc"},"quantity": {"N": "1000"},"person": {"S": "ochoa"}}

<<<<<<< HEAD
# Updates the 'quantity' attibute value from a single item.
- name: Updates arribute 'person'
  dynamodb:
    table: narcos
    action: update
    primary_key: {"bank": {"S": "hsbc"}}
    update_expression: 'SET quantity=:number'
    expression_attribute_values = {":number": {"N": "2000"}}

# Deletes the 'person' attibute value from a single item. The table has a composite
# primary key. 'bank' is the primary key and 'quantity' is the sort key.
- name: Deletes arribute 'person'
  dynamodb:
    table: narcos
    action: update
    primary_key: {"bank": {"S": "hsbc"}, "quantity": {"N": "1000"}}
    update_expression: 'REMOVE person'

=======
>>>>>>> Merge branch 'dynamodb' into add_dynamodb
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

<<<<<<< HEAD
RETURN = '''
---
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

=======
>>>>>>> Merge branch 'dynamodb' into add_dynamodb
import boto3

import ansible.module_utils.ec2
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto_exception


try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
def get(connection, table, primary_key):

    response = connection.get_item(
        TableName=table,
        Key=primary_key,
        # ProjectionExpression=projection_expression
    )

    result = dict(changed=False, message=response)
>>>>>>> refactor main() to call small functions

    return result


<<<<<<< HEAD
def put(connection, table, item, result):

    connection.put_item(
=======
def put(connection, table, item):

    result = connection.put_item(
>>>>>>> refactor main() to call small functions
        TableName=table,
        Item=item,
    )

    result = dict(changed=True, message='Item added')

    return result


<<<<<<< HEAD
def update(connection, table, primary_key, update_expression, condition_expression, expression_attribute_values, result):

    if condition_expression and expression_attribute_values:
        connection.update_item(
            TableName=table,
            Key=primary_key,
            UpdateExpression=update_expression,
            ConditionExpression=condition_expression,
            ExpressionAttributeValues=expression_attribute_values
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


def delete(connection, table, primary_key, condition_expression, expression_attribute_values, result):

    connection.delete_item(
=======
def delete(connection, table, primary_key, condition_expression, expression_attribute_values):

    result = connection.delete_item(
>>>>>>> refactor main() to call small functions
        TableName=table,
        Key=primary_key,
        ConditionExpression=condition_expression,
        ExpressionAttributeValues=expression_attribute_values
    )

    result = dict(changed=True, message='Item deleted')

    return result


<<<<<<< HEAD
=======
>>>>>>> Merge branch 'dynamodb' into add_dynamodb
=======
>>>>>>> refactor main() to call small functions
=======
>>>>>>> Merge branch 'dynamodb' into add_dynamodb
def main():
    argument_spec = ansible.module_utils.ec2.ec2_argument_spec()
    argument_spec.update(dict(
        table=dict(required=True),
        action=dict(required=True, choices=["get", "put", "update", "delete"]),
        primary_key=dict(required=False, type='dict'),
        item=dict(required=False, type='dict'),
        condition_expression=dict(required=False, type='str'),
        expression_attribute_values=dict(required=False, type='dict'),
<<<<<<< HEAD
        update_expression=dict(required=False, type='str'),
        projection_expression=dict(required=False, type='str')
        )
=======
        # projection_expression=dict(required=True)
        # primary_key_type=dict(required=True),
        # update_expression=dict(default='present', type='str', choices=[
        #     "SET", "REMOVE", "ADD", "DELETE"]),
        # expression_attribute_names=dict(required=False),
    )
>>>>>>> Merge branch 'dynamodb' into add_dynamodb
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
<<<<<<< HEAD
        update_expression = module.params.get('update_expression')
        expression_attribute_values = module.params.get(
            'expression_attribute_values')
        projection_expression = module.params.get('projection_expression')

        result = dict(
            changed=False,
            item=''
        )

        if action == 'get':
            result = get(connection, table, primary_key, projection_expression, result)

        elif action == 'put':
            result = put(connection, table, item, result)

        elif action == 'update':
            result = update(connection, table, primary_key, update_expression,
                            condition_expression, expression_attribute_values, result)

        elif action == 'delete':
            result = delete(connection, table, primary_key,
                            condition_expression, expression_attribute_values, result)
=======
        expression_attribute_values = module.params.get(
            'expression_attribute_values')
        # projection_expression = module.params.get('projection_expression')
        # update_expression = module.params.get('update_expression')
        # expression_attribute_names = module.params.get(
        #     'expression_attribute_names')


        if action == 'get':
            response = connection.get_item(
                TableName=table,
                Key=primary_key,
                # ProjectionExpression=projection_expression
            )

            return response

        elif action == 'put':
            result = connection.put_item(
                TableName=table,
                Item=item,
            )

        elif action == 'update':
            result = connection.update_item(
                TableName=table,
                Key={primary_key_type: primary_key},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
            )

            return result

        elif action == 'delete':
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Merge branch 'dynamodb' into add_dynamodb
            result = connection.delete_item(
                TableName=table,
                Key=primary_key,
                ConditionExpression=condition_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_OLD'
            )

            return result
<<<<<<< HEAD
>>>>>>> Merge branch 'dynamodb' into add_dynamodb
=======
            delete(connection, table, primary_key,
                   condition_expression, expression_attribute_values)
>>>>>>> refactor main() to call small functions
=======
>>>>>>> Merge branch 'dynamodb' into add_dynamodb

    except connection.exceptions.ResourceNotFoundException as error:
        error_msg = 'Table {} not found'.format(table)
        module.fail_json(msg=error_msg)
    except connection.exceptions.ConditionalCheckFailedException as error:
        error_msg = 'No item matches the condition'
        module.fail_json(msg=error_msg)
    except Exception as error:
        error_msg = boto_exception(error)
        module.fail_json(msg=error_msg)

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
    result = dict(changed=False, message=response)

>>>>>>> Merge branch 'dynamodb' into add_dynamodb
=======
>>>>>>> refactor main() to call small functions
=======
    result = dict(changed=False, message=response)

>>>>>>> Merge branch 'dynamodb' into add_dynamodb
    module.exit_json(**result)


if __name__ == '__main__':
    main()
