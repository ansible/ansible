#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: dynamodb_table
short_description: Create, update or delete AWS Dynamo DB tables
version_added: "2.0"
description:
  - Create or delete AWS Dynamo DB tables.
  - Can update the provisioned throughput on existing tables.
  - Returns the status of the specified table.
author: Alan Loi (@loia)
requirements:
  - "boto >= 2.37.0"
  - "boto3 >= 1.4.4 (for tagging)"
options:
  state:
    description:
      - Create or delete the table.
    choices: ['present', 'absent']
    default: 'present'
    type: str
  name:
    description:
      - Name of the table.
    required: true
    type: str
  hash_key_name:
    description:
      - Name of the hash key.
      - Required when C(state=present).
    type: str
  hash_key_type:
    description:
      - Type of the hash key.
    choices: ['STRING', 'NUMBER', 'BINARY']
    default: 'STRING'
    type: str
  range_key_name:
    description:
      - Name of the range key.
    type: str
  range_key_type:
    description:
      - Type of the range key.
    choices: ['STRING', 'NUMBER', 'BINARY']
    default: 'STRING'
    type: str
  read_capacity:
    description:
      - Read throughput capacity (units) to provision.
    default: 1
    type: int
  write_capacity:
    description:
      - Write throughput capacity (units) to provision.
    default: 1
    type: int
  indexes:
    description:
      - list of dictionaries describing indexes to add to the table. global indexes can be updated. local indexes don't support updates or have throughput.
      - "required options: ['name', 'type', 'hash_key_name']"
      - "other options: ['hash_key_type', 'range_key_name', 'range_key_type', 'includes', 'read_capacity', 'write_capacity']"
    suboptions:
      name:
        description: The name of the index.
        type: str
        required: true
      type:
        description:
          - The type of index.
          - "Valid types: C(all), C(global_all), C(global_include), C(global_keys_only), C(include), C(keys_only)"
        type: str
        required: true
      hash_key_name:
        description: The name of the hash-based key.
        required: true
        type: str
      hash_key_type:
        description: The type of the hash-based key.
        type: str
      range_key_name:
        description: The name of the range-based key.
        type: str
      range_key_type:
        type: str
        description: The type of the range-based key.
      includes:
        type: list
        description: A list of fields to include when using C(global_include) or C(include) indexes.
      read_capacity:
        description:
          - Read throughput capacity (units) to provision for the index.
        type: int
      write_capacity:
        description:
          - Write throughput capacity (units) to provision for the index.
        type: int
    default: []
    version_added: "2.1"
    type: list
    elements: dict
  tags:
    version_added: "2.4"
    description:
      - A hash/dictionary of tags to add to the new instance or for starting/stopping instance by tag.
      - 'For example: C({"key":"value"}) and C({"key":"value","key2":"value2"})'
    type: dict
  wait_for_active_timeout:
    version_added: "2.4"
    description:
      - how long before wait gives up, in seconds. only used when tags is set
    default: 60
    type: int
extends_documentation_fragment:
    - aws
    - ec2
"""

EXAMPLES = '''
# Create dynamo table with hash and range primary key
- dynamodb_table:
    name: my-table
    region: us-east-1
    hash_key_name: id
    hash_key_type: STRING
    range_key_name: create_time
    range_key_type: NUMBER
    read_capacity: 2
    write_capacity: 2
    tags:
      tag_name: tag_value

# Update capacity on existing dynamo table
- dynamodb_table:
    name: my-table
    region: us-east-1
    read_capacity: 10
    write_capacity: 10

# set index on existing dynamo table
- dynamodb_table:
    name: my-table
    region: us-east-1
    indexes:
      - name: NamedIndex
        type: global_include
        hash_key_name: id
        range_key_name: create_time
        includes:
          - other_field
          - other_field2
        read_capacity: 10
        write_capacity: 10

# Delete dynamo table
- dynamodb_table:
    name: my-table
    region: us-east-1
    state: absent
'''

RETURN = '''
table_status:
    description: The current status of the table.
    returned: success
    type: str
    sample: ACTIVE
'''

import time
import json
import traceback
import itertools

try:

    from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
    import boto3.dynamodb
    from boto3.dynamodb.table import Table
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import botocore
    from ansible.module_utils.ec2 import ansible_dict_to_boto3_tag_list, boto3_conn
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import AnsibleAWSError, connect_to_aws, ec2_argument_spec, get_aws_connection_info

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by AnsibleAWSModule

DYNAMO_TYPE_DEFAULT = 'STRING'
INDEX_REQUIRED_OPTIONS = ['name', 'type', 'hash_key_name']
INDEX_OPTIONS = INDEX_REQUIRED_OPTIONS + ['hash_key_type', 'range_key_name', 'range_key_type', 'includes', 'read_capacity', 'write_capacity']
INDEX_TYPE_OPTIONS = ['all', 'global_all', 'global_include', 'global_keys_only', 'include', 'keys_only']


def create_or_update_dynamo_table(resource, module):
    table_name = module.params.get('name')
    hash_key_name = module.params.get('hash_key_name')
    hash_key_type = module.params.get('hash_key_type')
    range_key_name = module.params.get('range_key_name')
    range_key_type = module.params.get('range_key_type')
    read_capacity = module.params.get('read_capacity')
    write_capacity = module.params.get('write_capacity')
    all_indexes = module.params.get('indexes')
    tags = module.params.get('tags')
    wait_for_active_timeout = module.params.get('wait_for_active_timeout')
    key_type_mapping = {'STRING': 'S', 'BOOLEAN': 'B', 'NUMBER': 'B'}

    for index in all_indexes:
        validate_index(index, module)

    throughput = {
        'read': read_capacity,
        'write': write_capacity
    }

    indexes, global_indexes, attr_definitions = get_indexes(all_indexes)
    result = dict(
        table_name=table_name,
        hash_key_name=hash_key_name,
        hash_key_type=hash_key_type,
        range_key_name=range_key_name,
        range_key_type=range_key_type,
        read_capacity=read_capacity,
        write_capacity=write_capacity,
        indexes=all_indexes,
    )

    try:
        client = module.client('dynamodb')
        table = resource.Table(table_name)
        try:
            table_status = table.table_status
        except is_boto3_error_code('ResourceNotFoundException'):
            # table doesn't exist
            table_status = 'TABLE_NOT_FOUND'
        if table_status in ['ACTIVE', 'CREATING', 'UPDATING']:
            table.wait_until_exists()
            if table_status == 'CREATING':
                table.wait_until_exists()
            result['changed'], result['global_index_updates'] = update_dynamo_table(module,
                                                                                    client,
                                                                                    table,
                                                                                    throughput=throughput,
                                                                                    check_mode=module.check_mode,
                                                                                    global_indexes=global_indexes,
                                                                                    global_attr_definitions=attr_definitions)
            # result['changed'] = 'update the table'
        else:
            if not module.check_mode:
                kwargs = {}
                key_schema = []
                prov_throughput = {
                    'ReadCapacityUnits': read_capacity,
                    'WriteCapacityUnits': write_capacity
                }

                if range_key_name:
                    key_schema.append({'AttributeName': hash_key_name, 'KeyType': "HASH"}, {'AttributeName': range_key_name, 'KeyType': "RANGE"})
                    attr_definitions.append({'AttributeName': hash_key_name, 'AttributeType': key_type_mapping[hash_key_type.upper()]}, {
                                            'AttributeName': range_key_name, 'AttributeType': key_type_mapping[range_key_type.upper()]})
                else:
                    key_schema.append({'AttributeName': hash_key_name, 'KeyType': "HASH"})
                    attr_definitions.append({'AttributeName': hash_key_name, 'AttributeType': key_type_mapping[hash_key_type.upper()]})

                kwargs.update({"AttributeDefinitions": remove_duplicates(attr_definitions), "TableName": table_name,
                               "KeySchema": key_schema, "ProvisionedThroughput": prov_throughput})
                if indexes:
                    kwargs.update({"LocalSecondaryIndexes": indexes})
                if global_indexes:
                    kwargs.update({"GlobalSecondaryIndexes": global_indexes})
                resource.create_table(**kwargs)
            result['changed'] = True

        if not module.check_mode:
            result['table_status'] = table.table_status
            result['global_secondary_indexes'] = table.global_secondary_indexes
            result['local_secondary_indexes'] = table.local_secondary_indexes

        if tags:
            # only tables which are active can be tagged
            if table.table_status != 'ACTIVE':
                try:
                    table.wait_until_exists()
                except Exception as e:
                    module.fail_json(msg="timed out waiting for table to exist")
                client.tag_resource(
                    ResourceArn=table.table_arn,
                    Tags=ansible_dict_to_boto3_tag_list(tags))
                result['tags'] = tags

    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json_aws(e, 'Unable to locate credential' + traceback.format_exc())
    except ClientError as e:
        module.fail_json_aws(e, 'Failed to create/update dynamo table due to error: ' + traceback.format_exc())
    except Exception as exc:
        module.fail_json_aws(exc, 'Ansible dynamodb operation failed: ' + traceback.format_exc())
    else:
        module.exit_json(**result)


def delete_dynamo_table(resource, module):
    table_name = module.params.get('name')

    result = dict(
        table_name=table_name,
    )

    try:
        table = resource.Table(table_name)
        table.wait_until_exists()
        try:
            table_status = table.table_status
        except is_boto3_error_code('ResourceNotFoundException'):
            # table doesn't exist
            table_status = 'TABLE_NOT_FOUND'

        if table_status == 'ACTIVE':
            if not module.check_mode:
                table.delete()
            result['changed'] = True

        else:
            result['changed'] = False

    except ClientError as e:
        module.fail_json_aws(e, 'Failed to delete dynamo table due to error: ' + traceback.format_exc())
    else:
        module.exit_json(**result)


def update_dynamodb_table_args(table_name, prov_throughput=None, throughput_updates=None, global_indexes_updates=None, global_attr_definitions=None):
    kwargs = {}
    if throughput_updates:
        kwargs.update({"TableName": table_name, "ProvisionedThroughput": prov_throughput})
    if global_indexes_updates:
        kwargs.update({"TableName": table_name, "AttributeDefinitions": global_attr_definitions, "GlobalSecondaryIndexUpdates": global_indexes_updates})
    return kwargs


def update_dynamo_table(module, client, table, throughput=None, check_mode=False, global_indexes=None, global_attr_definitions=None):
    table_updated = False
    table_name = table.table_name
    kwargs = {}
    prov_throughput = {
        'ReadCapacityUnits': throughput['read'],
        'WriteCapacityUnits': throughput['write']
    }
    throughput_updates = has_throughput_changed(table, throughput)
    global_indexes_updates = get_changed_global_indexes(table, global_indexes)
    kwargs = update_dynamodb_table_args(table_name, prov_throughput, throughput_updates, global_indexes_updates, global_attr_definitions)
    if not check_mode and (global_indexes_updates or throughput_updates):
        client.update_table(**kwargs)
        table_updated = True

    return table_updated, global_indexes_updates


def has_throughput_changed(table, new_throughput):
    if not new_throughput:
        return False

    return new_throughput['read'] != table.provisioned_throughput['ReadCapacityUnits'] or \
        new_throughput['write'] != table.provisioned_throughput['WriteCapacityUnits']


def remove_duplicates(attr_definitions):
    seen = set()
    new_l = []
    for d in attr_definitions:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            new_l.append(d)
    return new_l


def get_schema_param(hash_key_name, hash_key_type, range_key_name, range_key_type):
    if range_key_name:
        schema = [
            {'AttributeName': hash_key_name, 'KeyType': 'HASH'}, {'AttributeName': range_key_name, 'KeyType': 'RANGE'}
        ]
    else:
        schema = [
            {'AttributeName': hash_key_name, 'KeyType': 'HASH'}
        ]
    return schema


def get_changed_global_indexes(table, global_indexes):
    global_indexes_updates = []
    table_gsi_indexes = table.global_secondary_indexes
    if global_indexes:
        param_global_indexes = map(lambda index: index['IndexName'], global_indexes)
        param_global_indexes_prov_throughput = map(lambda index: (index['IndexName'], index['ProvisionedThroughput']), global_indexes)
        set_table_indexes = []
        set_table_indexes_prov_throughput = []

        if table_gsi_indexes:
            set_table_indexes = map(lambda index: index['IndexName'], table_gsi_indexes)
            set_table_indexes_prov_throughput = map(lambda index: (index['IndexName'], index['ProvisionedThroughput']), table_gsi_indexes)

        for index in set_table_indexes:
            if index not in param_global_indexes:
                global_indexes_updates.append({'Delete': {'IndexName': index}})

        for index in global_indexes:
            if index['IndexName'] not in set_table_indexes or not set_table_indexes:
                global_indexes_updates.append({'Create': index})

        for set_index in set_table_indexes_prov_throughput:
            for param_index in param_global_indexes_prov_throughput:
                if (set_index[0] == param_index[0] and
                   (set_index[1]['ReadCapacityUnits'] != param_index[1]['ReadCapacityUnits'] or
                   set_index[1]['WriteCapacityUnits'] != param_index[1]['WriteCapacityUnits'])):
                    global_indexes_updates.append({'Update': {'IndexName': set_index[0], 'ProvisionedThroughput': param_index[1]}})

    return global_indexes_updates


def validate_index(index, module):
    for key, val in index.items():
        if key not in INDEX_OPTIONS:
            module.fail_json(msg='%s is not a valid option for an index' % key)
    for required_option in INDEX_REQUIRED_OPTIONS:
        if required_option not in index:
            module.fail_json(msg='%s is a required option for an index' % required_option)
    if index['type'] not in INDEX_TYPE_OPTIONS:
        module.fail_json(msg='%s is not a valid index type, must be one of %s' % (index['type'], INDEX_TYPE_OPTIONS))


def get_indexes(all_indexes):
    indexes = []
    global_indexes = []
    global_indexes_attr_definitions = []
    global_indexes_attr_definition = {}
    for index in all_indexes:
        name = index['name']
        index_type = index.get('type')
        hash_key_name = index.get('hash_key_name')
        hash_key_type = 'S'
        if 'hash_key_type' in index:
            hash_key_type = index.get('hash_key_type')
        range_key_name = None
        range_key_type = None
        if 'range_key_name' in index:
            range_key_name = index.get('range_key_name')
            range_key_type = 'S'
            if 'range_key_type' in index:
                range_key_type = index.get('range_key_type')

        schema = get_schema_param(hash_key_name, hash_key_type, range_key_name, range_key_type)
        projection_type = index_type.replace('global_', '')
        projection = {'ProjectionType': projection_type.upper()}
        index_throughput = {'ReadCapacityUnits': index.get('read_capacity', 1), 'WriteCapacityUnits': index.get('write_capacity', 1)}
        if projection_type == 'include':

            projection.update({'NonKeyAttributes': index['includes']})

        if index_type in ['all', 'include', 'keys_only']:
            # local secondary all_indexes
            indexes.append({'IndexName': name, 'KeySchema': schema, 'Projection': projection})
        elif index_type in ['global_all', 'global_include', 'global_keys_only']:
            # global secondary indexes
            global_indexes.append({'IndexName': name, 'KeySchema': schema, 'Projection': projection, 'ProvisionedThroughput': index_throughput})
            global_indexes_attr_definitions.append({'AttributeName': hash_key_name, 'AttributeType': hash_key_type})

            if range_key_name:
                global_indexes_attr_definitions.append({'AttributeName': range_key_name, 'AttributeType': range_key_type})

    return indexes, global_indexes, remove_duplicates(global_indexes_attr_definitions)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(required=True, type='str'),
        hash_key_name=dict(type='str'),
        hash_key_type=dict(default='STRING', type='str', choices=['STRING', 'NUMBER', 'BINARY']),
        range_key_name=dict(type='str'),
        range_key_type=dict(default='STRING', type='str', choices=['STRING', 'NUMBER', 'BINARY']),
        read_capacity=dict(default=1, type='int'),
        write_capacity=dict(default=1, type='int'),
        indexes=dict(default=[], type='list'),
        tags=dict(type='dict'),
        wait_for_active_timeout=dict(default=60, type='int'),
    ))

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['state', 'present', ['name', 'hash_key_name']]],
    )
    resource = module.resource('dynamodb')
    state = module.params.get('state')
    if state == 'present':
        create_or_update_dynamo_table(resource, module)
    elif state == 'absent':
        delete_dynamo_table(resource, module)


if __name__ == '__main__':
    main()
