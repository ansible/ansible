from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: dynamodb
short_description: Reads, creates, updates or deletes items in AWS Dynamo DB tables.
version_added: "2.7"
author:
  - David C. Martin @blastikman
requirements:
  - boto3
options:
  table:
    description:
      - Name of the DynamoDB table
  action:
    description:
      - "get": Returns a set of attributes for the item with
      the given primary key.
      - "put": Creates a new item, or replaces an old item with a new item.
      If an item that has the same primary key as the new item already exists
      in the specified table, the new item completely replaces the existing item.
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


def get(connection, table, primary_key, result):

    response = connection.get_item(
        TableName=table,
        Key=primary_key,
        # ProjectionExpression=projection_expression
    )

    if 'Item' in response:
        result['item'] = response['Item']
    else:
        result = dict(failed=True, message='No item found')

    return result


def put(connection, table, item, result):

    response = connection.put_item(
        TableName=table,
        Item=item,
    )

    result = dict(changed=True, message='Item added')

    return result


def update(table, primary_key, ):

    response = connection.update_item(
        TableName=table,
        Key=primary_key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
    )

    return result


def delete(connection, table, primary_key, condition_expression, expression_attribute_values, result):

    response = connection.delete_item(
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
        expression_attribute_values=dict(required=False, type='dict'),
        # projection_expression=dict(required=True)
        # primary_key_type=dict(required=True),
        # update_expression=dict(default='present', type='str', choices=[
        #     "SET", "REMOVE", "ADD", "DELETE"]),
        # expression_attribute_names=dict(required=False),
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
        expression_attribute_values = module.params.get(
            'expression_attribute_values')
        # projection_expression = module.params.get('projection_expression')
        # update_expression = module.params.get('update_expression')
        # expression_attribute_names = module.params.get(
        #     'expression_attribute_names')

        result = dict(
            changed=False,
            item=''
        )

        if action == 'get':
            result = get(connection, table, primary_key, result)

        elif action == 'put':
            result = put(connection, table, item, result)

        elif action == 'update':
            result = update()

        elif action == 'delete':
            result = delete(connection, table, primary_key,
                   condition_expression, expression_attribute_values, result)

    except connection.exceptions.ResourceNotFoundException as error:
        error_msg = 'Table {} not found'.format(table)
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
