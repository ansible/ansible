#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = """
---
module: dynamodb_table
short_description: Create, update or delete AWS Dynamo DB tables.
version_added: "2.0"
description:
  - Create or delete AWS Dynamo DB tables.
  - Can update the provisioned throughput on existing tables.
  - Returns the status of the specified table.
author: Alan Loi (@loia)
requirements:
  - "boto >= 2.37.0"
options:
  state:
    description:
      - Create or delete the table
    required: false
    choices: ['present', 'absent']
    default: 'present'
  name:
    description:
      - Name of the table.
    required: true
  hash_key_name:
    description:
      - Name of the hash key.
      - Required when C(state=present).
    required: false
    default: null
  hash_key_type:
    description:
      - Type of the hash key.
    required: false
    choices: ['STRING', 'NUMBER', 'BINARY']
    default: 'STRING'
  range_key_name:
    description:
      - Name of the range key.
    required: false
    default: null
  range_key_type:
    description:
      - Type of the range key.
    required: false
    choices: ['STRING', 'NUMBER', 'BINARY']
    default: 'STRING'
  read_capacity:
    description:
      - Read throughput capacity (units) to provision.
    required: false
    default: 1
  write_capacity:
    description:
      - Write throughput capacity (units) to provision.
    required: false
    default: 1
  indexes:
    description:
      - list of dictionaries describing indexes to add to the table. global indexes can be updated. local indexes don't support updates or have throughput.
      - "required options: ['name', 'type', 'hash_key_name']"
      - "valid types: ['all', 'global_all', 'global_include', 'global_keys_only', 'include', 'keys_only']"
      - "other options: ['hash_key_type', 'range_key_name', 'range_key_type', 'includes', 'read_capacity', 'write_capacity']"
    required: false
    default: []
    version_added: "2.1"
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
    type: string
    sample: ACTIVE
'''

import traceback

try:
    import boto
    import boto.dynamodb2
    from boto.dynamodb2.table import Table
    from boto.dynamodb2.fields import HashKey, RangeKey, AllIndex, GlobalAllIndex, GlobalIncludeIndex, GlobalKeysOnlyIndex, IncludeIndex, KeysOnlyIndex
    from boto.dynamodb2.types import STRING, NUMBER, BINARY
    from boto.exception import BotoServerError, NoAuthHandlerFound, JSONResponseError
    from boto.dynamodb2.exceptions import ValidationException
    HAS_BOTO = True

    DYNAMO_TYPE_MAP = {
        'STRING': STRING,
        'NUMBER': NUMBER,
        'BINARY': BINARY
    }

except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import AnsibleAWSError, connect_to_aws, ec2_argument_spec, get_aws_connection_info


DYNAMO_TYPE_DEFAULT = 'STRING'
INDEX_REQUIRED_OPTIONS = ['name', 'type', 'hash_key_name']
INDEX_OPTIONS = INDEX_REQUIRED_OPTIONS + ['hash_key_type', 'range_key_name', 'range_key_type', 'includes', 'read_capacity', 'write_capacity']
INDEX_TYPE_OPTIONS = ['all', 'global_all', 'global_include', 'global_keys_only', 'include', 'keys_only']


def create_or_update_dynamo_table(connection, module):
    table_name = module.params.get('name')
    hash_key_name = module.params.get('hash_key_name')
    hash_key_type = module.params.get('hash_key_type')
    range_key_name = module.params.get('range_key_name')
    range_key_type = module.params.get('range_key_type')
    read_capacity = module.params.get('read_capacity')
    write_capacity = module.params.get('write_capacity')
    all_indexes = module.params.get('indexes')

    for index in all_indexes:
        validate_index(index, module)

    schema = get_schema_param(hash_key_name, hash_key_type, range_key_name, range_key_type)

    throughput = {
        'read': read_capacity,
        'write': write_capacity
    }

    indexes, global_indexes = get_indexes(all_indexes)

    result = dict(
        region=module.params.get('region'),
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
        table = Table(table_name, connection=connection)


        if dynamo_table_exists(table):
            result['changed'] = update_dynamo_table(table, throughput=throughput, check_mode=module.check_mode, global_indexes=global_indexes)
        else:
            if not module.check_mode:
                Table.create(table_name, connection=connection, schema=schema, throughput=throughput, indexes=indexes, global_indexes=global_indexes)
            result['changed'] = True

        if not module.check_mode:
            result['table_status'] = table.describe()['Table']['TableStatus']

    except BotoServerError:
        result['msg'] = 'Failed to create/update dynamo table due to error: ' + traceback.format_exc()
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def delete_dynamo_table(connection, module):
    table_name = module.params.get('name')

    result = dict(
        region=module.params.get('region'),
        table_name=table_name,
    )

    try:
        table = Table(table_name, connection=connection)

        if dynamo_table_exists(table):
            if not module.check_mode:
                table.delete()
            result['changed'] = True

        else:
            result['changed'] = False

    except BotoServerError:
        result['msg'] = 'Failed to delete dynamo table due to error: ' + traceback.format_exc()
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def dynamo_table_exists(table):
    try:
        table.describe()
        return True

    except JSONResponseError as e:
        if e.message and e.message.startswith('Requested resource not found'):
            return False
        else:
            raise e


def update_dynamo_table(table, throughput=None, check_mode=False, global_indexes=None):
    table.describe()  # populate table details
    throughput_changed = False
    global_indexes_changed = False
    if has_throughput_changed(table, throughput):
        if not check_mode:
            throughput_changed = table.update(throughput=throughput)
        else:
            throughput_changed = True

    removed_indexes, added_indexes, index_throughput_changes = get_changed_global_indexes(table, global_indexes)
    if removed_indexes:
        if not check_mode:
            for name, index in removed_indexes.iteritems():
                global_indexes_changed = table.delete_global_secondary_index(name) or global_indexes_changed
        else:
            global_indexes_changed = True

    if added_indexes:
        if not check_mode:
            for name, index in added_indexes.iteritems():
                global_indexes_changed = table.create_global_secondary_index(global_index=index) or global_indexes_changed
        else:
            global_indexes_changed = True

    if index_throughput_changes:
        if not check_mode:
            # todo: remove try once boto has https://github.com/boto/boto/pull/3447 fixed
            try:
                global_indexes_changed = table.update_global_secondary_index(global_indexes=index_throughput_changes) or global_indexes_changed
            except ValidationException:
                pass
        else:
            global_indexes_changed = True

    return throughput_changed or global_indexes_changed


def has_throughput_changed(table, new_throughput):
    if not new_throughput:
        return False

    return new_throughput['read'] != table.throughput['read'] or \
           new_throughput['write'] != table.throughput['write']


def get_schema_param(hash_key_name, hash_key_type, range_key_name, range_key_type):
    if range_key_name:
        schema = [
            HashKey(hash_key_name, DYNAMO_TYPE_MAP.get(hash_key_type, DYNAMO_TYPE_MAP[DYNAMO_TYPE_DEFAULT])),
            RangeKey(range_key_name, DYNAMO_TYPE_MAP.get(range_key_type, DYNAMO_TYPE_MAP[DYNAMO_TYPE_DEFAULT]))
        ]
    else:
        schema = [
            HashKey(hash_key_name, DYNAMO_TYPE_MAP.get(hash_key_type, DYNAMO_TYPE_MAP[DYNAMO_TYPE_DEFAULT]))
        ]
    return schema


def get_changed_global_indexes(table, global_indexes):
    table.describe()

    table_index_info = dict((index.name, index.schema()) for index in table.global_indexes)
    table_index_objects = dict((index.name, index) for index in table.global_indexes)
    set_index_info = dict((index.name, index.schema()) for index in global_indexes)
    set_index_objects = dict((index.name, index) for index in global_indexes)

    removed_indexes = dict((name, index) for name, index in table_index_info.iteritems() if name not in set_index_info)
    added_indexes = dict((name, set_index_objects[name]) for name, index in set_index_info.iteritems() if name not in table_index_info)
    # todo: uncomment once boto has https://github.com/boto/boto/pull/3447 fixed
    # index_throughput_changes = dict((name, index.throughput) for name, index in set_index_objects.iteritems() if name not in added_indexes and (index.throughput['read'] != str(table_index_objects[name].throughput['read']) or index.throughput['write'] != str(table_index_objects[name].throughput['write'])))
    # todo: remove once boto has https://github.com/boto/boto/pull/3447 fixed
    index_throughput_changes = dict((name, index.throughput) for name, index in set_index_objects.iteritems() if name not in added_indexes)

    return removed_indexes, added_indexes, index_throughput_changes


def validate_index(index, module):
    for key, val in index.iteritems():
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
    for index in all_indexes:
        name = index['name']
        schema = get_schema_param(index.get('hash_key_name'), index.get('hash_key_type'), index.get('range_key_name'), index.get('range_key_type'))
        throughput = {
            'read': index.get('read_capacity', 1),
            'write': index.get('write_capacity', 1)
        }

        if index['type'] == 'all':
            indexes.append(AllIndex(name, parts=schema))

        elif index['type'] == 'global_all':
            global_indexes.append(GlobalAllIndex(name, parts=schema, throughput=throughput))

        elif index['type'] == 'global_include':
            global_indexes.append(GlobalIncludeIndex(name, parts=schema, throughput=throughput, includes=index['includes']))

        elif index['type'] == 'global_keys_only':
            global_indexes.append(GlobalKeysOnlyIndex(name, parts=schema, throughput=throughput))

        elif index['type'] == 'include':
            indexes.append(IncludeIndex(name, parts=schema, includes=index['includes']))

        elif index['type'] == 'keys_only':
            indexes.append(KeysOnlyIndex(name, parts=schema))

    return indexes, global_indexes



def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(required=True, type='str'),
        hash_key_name=dict(required=True, type='str'),
        hash_key_type=dict(default='STRING', type='str', choices=['STRING', 'NUMBER', 'BINARY']),
        range_key_name=dict(type='str'),
        range_key_type=dict(default='STRING', type='str', choices=['STRING', 'NUMBER', 'BINARY']),
        read_capacity=dict(default=1, type='int'),
        write_capacity=dict(default=1, type='int'),
        indexes=dict(default=[], type='list'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg='region must be specified')

    try:
        connection = connect_to_aws(boto.dynamodb2, region, **aws_connect_params)
    except (NoAuthHandlerFound, AnsibleAWSError) as e:
        module.fail_json(msg=str(e))

    state = module.params.get('state')
    if state == 'present':
        create_or_update_dynamo_table(connection, module)
    elif state == 'absent':
        delete_dynamo_table(connection, module)


if __name__ == '__main__':
    main()
