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
description:
  - Create or delete AWS Dynamo DB tables.
  - Can update the provisioned throughput on existing tables.
  - Returns the status of the specified table.
version_added: "2.0"
author: Alan Loi (@loia)
version_added: "2.0"
requirements:
  - "boto >= 2.13.2"
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
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    aliases: ['aws_region', 'ec2_region']

extends_documentation_fragment: aws
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

try:
    import boto
    import boto.dynamodb2
    from boto.dynamodb2.table import Table
    from boto.dynamodb2.fields import HashKey, RangeKey
    from boto.dynamodb2.types import STRING, NUMBER, BINARY
    from boto.exception import BotoServerError, NoAuthHandlerFound, JSONResponseError
    HAS_BOTO = True

except ImportError:
    HAS_BOTO = False


DYNAMO_TYPE_MAP = {
    'STRING': STRING,
    'NUMBER': NUMBER,
    'BINARY': BINARY
}


def create_or_update_dynamo_table(connection, module):
    table_name = module.params.get('name')
    hash_key_name = module.params.get('hash_key_name')
    hash_key_type = module.params.get('hash_key_type')
    range_key_name = module.params.get('range_key_name')
    range_key_type = module.params.get('range_key_type')
    read_capacity = module.params.get('read_capacity')
    write_capacity = module.params.get('write_capacity')

    if range_key_name:
        schema = [
            HashKey(hash_key_name, DYNAMO_TYPE_MAP.get(hash_key_type)),
            RangeKey(range_key_name, DYNAMO_TYPE_MAP.get(range_key_type))
        ]
    else:
        schema = [
            HashKey(hash_key_name, DYNAMO_TYPE_MAP.get(hash_key_type))
        ]
    throughput = {
        'read': read_capacity,
        'write': write_capacity
    }

    result = dict(
        region=module.params.get('region'),
        table_name=table_name,
        hash_key_name=hash_key_name,
        hash_key_type=hash_key_type,
        range_key_name=range_key_name,
        range_key_type=range_key_type,
        read_capacity=read_capacity,
        write_capacity=write_capacity,
    )

    try:
        table = Table(table_name, connection=connection)

        if dynamo_table_exists(table):
            result['changed'] = update_dynamo_table(table, throughput=throughput, check_mode=module.check_mode)
        else:
            if not module.check_mode:
                Table.create(table_name, connection=connection, schema=schema, throughput=throughput)
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

    except JSONResponseError, e:
        if e.message and e.message.startswith('Requested resource not found'):
            return False
        else:
            raise e


def update_dynamo_table(table, throughput=None, check_mode=False):
    table.describe()  # populate table details

    if has_throughput_changed(table, throughput):
        if not check_mode:
            return table.update(throughput=throughput)
        else:
            return True

    return False


def has_throughput_changed(table, new_throughput):
    if not new_throughput:
        return False

    return new_throughput['read'] != table.throughput['read'] or \
           new_throughput['write'] != table.throughput['write']


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

    except (NoAuthHandlerFound, StandardError), e:
        module.fail_json(msg=str(e))

    state = module.params.get('state')
    if state == 'present':
        create_or_update_dynamo_table(connection, module)
    elif state == 'absent':
        delete_dynamo_table(connection, module)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
