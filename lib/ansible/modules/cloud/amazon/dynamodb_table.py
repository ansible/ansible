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
  sse_enabled:
    version_added: "2.8"
    type: bool
    description:
    - boolean for setting server-side encryption
  stream_enabled:
    version_added: "2.8"
    type: bool
    description:
    - Indicates whether DynamoDB Streams is enabled (true) or disabled (false) on the table
  stream_view_type:
    version_added: "2.8"
    choices: ['KEYS_ONLY', 'NEW_IMAGE', 'OLD_IMAGE', 'NEW_AND_OLD_IMAGES']
    description:
    - when an item in the table is modified, stream_view_type determines what information is written to the stream for this table.
    - "valid types: : ['KEYS_ONLY', 'NEW_IMAGE', 'OLD_IMAGE', 'NEW_AND_OLD_IMAGES']"
  sse_type:
    version_added: "2.8"
    choices: ['AES256', 'KMS']
    description:
    - server-side encryption type
  sse_kms_master_key_id:
    version_added: "2.8"
    description:
    - The KMS Master Key (CMK) which should be used for the KMS encryption.
    - To specify a CMK, use its key ID, Amazon Resource Name (ARN), alias name, or alias ARN.
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
    # stream specification
    stream_enabled = module.params.get('stream_enabled')
    stream_view_type = module.params.get('stream_view_type')

    # sse specification
    sse_enabled = module.params.get('sse_enabled')
    sse_type = module.params.get('sse_type')
    sse_kms_master_key_id = module.params.get('sse_kms_master_key_id')

    key_type_mapping = {'STRING': 'S', 'BOOLEAN': 'B', 'NUMBER': 'B'}

    for index in all_indexes:
        validate_index(index, module)

    throughput = {
        'read': read_capacity,
        'write': write_capacity
    }
    stream_specification = None
    sse_specification = None
    if stream_enabled:
        stream_specification = {
            'StreamEnabled': stream_enabled,
            'StreamViewType': stream_view_type
        }
    if sse_enabled:
        sse_specification = {
            'Enabled': sse_enabled,
            'SSEType': sse_type
        }
        if sse_kms_master_key_id and sse_kms_master_key_id != "":
            sse_specification.update({'KMSMasterKeyId': sse_kms_master_key_id})

    local_secondary_indexes, global_secondary_indexes, attribute_definitions = serialize_indexes(all_indexes)

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
                                                                                    stream_spec=stream_specification,
                                                                                    sse_spec=sse_specification,
                                                                                    check_mode=module.check_mode,
                                                                                    global_indexes=global_secondary_indexes,
                                                                                    global_attr_definitions=attribute_definitions)
        else:
            if not module.check_mode:
                kwargs = {}
                key_schema = []
                prov_throughput = {
                    'ReadCapacityUnits': read_capacity,
                    'WriteCapacityUnits': write_capacity
                }

                if range_key_name:
                    key_schema.append({'AttributeName': hash_key_name, 'KeyType': "HASH"})
                    key_schema.append({'AttributeName': range_key_name, 'KeyType': "RANGE"})
                    attribute_definitions.append({'AttributeName': hash_key_name, 'AttributeType': key_type_mapping[hash_key_type.upper()]})
                    attribute_definitions.append({'AttributeName': range_key_name, 'AttributeType': key_type_mapping[range_key_type.upper()]})
                else:
                    key_schema.append({'AttributeName': hash_key_name, 'KeyType': "HASH"})
                    attribute_definitions.append({'AttributeName': hash_key_name, 'AttributeType': key_type_mapping[hash_key_type.upper()]})

                kwargs.update({"AttributeDefinitions": remove_duplicates(attribute_definitions), "TableName": table_name,
                               "KeySchema": key_schema, "ProvisionedThroughput": prov_throughput})
                if local_secondary_indexes:
                    kwargs.update({"LocalSecondaryIndexes": local_secondary_indexes})
                if global_secondary_indexes:
                    kwargs.update({"GlobalSecondaryIndexes": global_secondary_indexes})
                if stream_specification:
                    kwargs.update({'StreamSpecification': stream_specification})
                if sse_specification:
                    kwargs.update({'SSESpecification': sse_specification})
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
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e, 'Client Error: ' + traceback.format_exc())
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


def update_dynamodb_table_args(table_name, prov_throughput=None, throughput_updates=None, stream_spec_updates=None, stream_spec=None,
                               sse_spec_updates=None, sse_spec=None, global_indexes_updates=None, global_attr_definitions=None):
    kwargs = {}
    if throughput_updates:
        kwargs.update({"TableName": table_name, "ProvisionedThroughput": prov_throughput})
    if global_indexes_updates:
        kwargs.update({"TableName": table_name, "AttributeDefinitions": global_attr_definitions, "GlobalSecondaryIndexUpdates": global_indexes_updates})
    if stream_spec_updates:
        kwargs.update({"TableName": table_name, "StreamSpecification": stream_spec})
    if sse_spec_updates:
        # if kmsmaster key id is empty pop it off.
        if sse_spec['KMSMasterKeyId'] == "":
            sse_spec.pop('KMSMasterKeyId', None)
        kwargs.update({"TableName": table_name, "SSESpecification": sse_spec})
    return kwargs


def update_dynamo_table(module, client, table, throughput=None, stream_spec=None, sse_spec=None,
                        check_mode=False, global_indexes=None, global_attr_definitions=None):
    table_updated = False
    table_name = table.table_name
    kwargs = {}
    prov_throughput = {
        'ReadCapacityUnits': throughput['read'],
        'WriteCapacityUnits': throughput['write']
    }
    throughput_updates = has_throughput_changed(table, throughput)
    global_indexes_updates = get_changed_global_indexes(table.global_secondary_indexes, global_indexes)
    stream_spec_updates = None
    sse_spec_updates = None
    if stream_spec:
        stream_spec_updates = has_stream_spec_changed(table, stream_spec)
    if sse_spec:
        sse_spec_updates = has_sse_spec_changed(table, sse_spec)
    kwargs = update_dynamodb_table_args(table_name, prov_throughput, throughput_updates, stream_spec_updates,
                                        stream_spec,
                                        sse_spec_updates,
                                        sse_spec, global_indexes_updates, global_attr_definitions)
    if not check_mode and (global_indexes_updates or throughput_updates):
        client.update_table(**kwargs)
        table_updated = True

    return table_updated, global_indexes_updates


def has_sse_spec_changed(table, new_sse_spec):
    if not new_sse_spec:
        return False
    return table.sse_description is None or new_sse_spec['Enabled'] != table.sse_description['Enabled'] or \
        new_sse_spec['SSEType'] != table.sse_description['SSEType'] or \
        (new_sse_spec['KMSMasterKeyId'] != '' and new_sse_spec['KMSMasterKeyId'] != table.sse_description['KMSMasterKeyId'])


def has_stream_spec_changed(table, new_stream_spec):
    if not new_stream_spec:
        return False
    return table.stream_specification is None or new_stream_spec['StreamEnabled'] != table.stream_specification['StreamEnabled'] or \
        new_stream_spec['StreamViewType'] != table.stream_specification['StreamViewType']


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


def deserialize_index_names(indexes):
    index_names = []
    key = 'IndexName'
    for index in indexes:
        if key in index.keys():
            index_names.append(index[key])
    return set(index_names)


def filter_index_by_name(key, indexes):
    for index in indexes:
        if index['IndexName'] == key:
            return index
    return None


def get_changed_global_indexes(table_gsi_indexes, global_indexes):
    # check if this is a new index to be created
    global_indexes_updates = []

    input_gsi_index_names_set = deserialize_index_names(global_indexes)
    from_aws_gsi_index_names_set = deserialize_index_names(table_gsi_indexes)

    #
    # Find indexes to be deleted and created
    # An index is deleted when index name exists in the from_aws_gsi_index_names_set and not in the input_gsi_index_names_set
    # An index is created when index name exists in input_gsi_index_names_set but not in from_aws_gsi_index_names_set
    #
    indexes_to_be_deleted = from_aws_gsi_index_names_set - input_gsi_index_names_set

    for index_name in indexes_to_be_deleted:
        global_indexes_updates.append({'Delete': {'IndexName': index_name}})

    indexes_to_be_created = input_gsi_index_names_set - from_aws_gsi_index_names_set
    for index_name in indexes_to_be_created:
        index = filter_index_by_name(index_name, global_indexes)
        global_indexes_updates.append({'Create': index})
    #
    # Find indexes that needs to be updated
    # only provisioned throughput can be updated on an existing gsi index
    #
    indexes_to_be_updated = input_gsi_index_names_set & from_aws_gsi_index_names_set

    input_gsi_indexes_to_be_updated = [index for index in global_indexes if index['IndexName'] in indexes_to_be_updated]
    from_aws_gsi_indexes_to_be_updated = [index for index in table_gsi_indexes if index['IndexName'] in indexes_to_be_updated]

    for index_name in indexes_to_be_updated:
        input_gsi_index = filter_index_by_name(index_name, global_indexes)
        from_aws_gsi_index = filter_index_by_name(index_name, table_gsi_indexes)
        if input_gsi_index and 'ProvisionedThroughput' in input_gsi_index:
            input_gsi_index_prov_throughput = input_gsi_index.get('ProvisionedThroughput')
            from_aws_gsi_index_prov_throughput = from_aws_gsi_index.get('ProvisionedThroughput')
            if (input_gsi_index_prov_throughput.get('ReadCapacityUnits') != from_aws_gsi_index_prov_throughput.get('ReadCapacityUnits')) or (
                    input_gsi_index_prov_throughput.get('WriteCapacityUnits') != from_aws_gsi_index_prov_throughput.get('WriteCapacityUnits')):
                global_indexes_updates.append({'Update': {'IndexName': index_name, 'ProvisionedThroughput': input_gsi_index_prov_throughput}})

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


def serialize_index_to_json(index):
    serialized_index = dict()
    serialized_index_attribute_definitions = dict()
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
    serialized_index.update({'IndexName': name, 'KeySchema': schema, 'Projection': projection})

    if index_type in ['global_all', 'global_include', 'global_keys_only']:
        serialized_index.update({'ProvisionedThroughput': index_throughput})
    serialized_index_attribute_definitions.update({'AttributeName': hash_key_name, 'AttributeType': hash_key_type})
    if range_key_name:
        serialized_index_attribute_definitions.update({'AttributeName': range_key_name, 'AttributeType': range_key_type})
    return index_type, serialized_index, serialized_index_attribute_definitions


def serialize_indexes(all_indexes):
    local_secondary_indexes = []
    global_secondary_indexes = []
    indexes_attr_definitions = []
    for index in all_indexes:
        index_type, serialized_index_to_json, serialized_index_attribute_definitions = serialize_index_to_json(index)
        indexes_attr_definitions.append(serialized_index_attribute_definitions)
        if index_type in ['all', 'include', 'keys_only']:
            # local secondary all_indexes
            local_secondary_indexes.append(serialized_index_to_json)
        elif index_type in ['global_all', 'global_include', 'global_keys_only']:
            # global secondary indexes
            global_secondary_indexes.append(serialized_index_to_json)

    return local_secondary_indexes, global_secondary_indexes, remove_duplicates(indexes_attr_definitions)


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
        stream_enabled=dict(type='bool'),
        stream_view_type=dict(type='str', choices=['NEW_IMAGE', 'OLD_IMAGE', 'NEW_AND_OLD_IMAGES', 'KEYS_ONLY']),
        sse_enabled=dict(type='bool'),
        sse_type=dict(type='str', choices=['AES256', 'KMS']),
        sse_kms_master_key_id=dict(type='str')
    ))

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['state', 'present', ['name', 'hash_key_name']], ['sse_type', 'KMS', ['sse_type']],
                     ['sse_enabled', 'True', ['sse_type']], ['stream_enabled', 'True', ['stream_view_type']]],
    )
    resource = module.resource('dynamodb')
    state = module.params.get('state')
    if state == 'present':
        create_or_update_dynamo_table(resource, module)
    elif state == 'absent':
        delete_dynamo_table(resource, module)


if __name__ == '__main__':
    main()
