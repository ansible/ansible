#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Nate Fleming <nate.fleming@moserit.com>
# Sponsored by Moser Consulting Inc http://www.moserit.com
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
module: snowflake_schema
short_description: Add or remove Snowflake schemas
description:
  - Add or remove Snowflake schemas
options:
  name:
    description:
      - name of the schema to add or remove
    required: true
    aliases: ["schema", "schemas", "names"]
    type: str
  database:
    description:
      - name of the database in which the schema resides
    required: false
    aliases: ["db"]
    type: str
  connection:
    description:
      - Provide parameters to the snowflake connection
    required: false
    type: dict
  comment:
    description:
      - A comment to include on the database
    required: false
    type: str
  clone:
    description:
      - The schema to clone
    required: false
    type: str
  preposition:
    description:
      - Used when cloning a schema at a certain time/offset or statement
    choices: ["at", "before"]
    required: false
    type: str
  timestamp:
    description:
      - Clone a schema at a specific timestamp
    required: false
    type: str
  offset:
    description:
      - Clone a schema at a specific offset
    required: false
    type: str
  statement:
    description:
      - Clone a schema at a specific statement
    required: false
    type: str
  retention_time_in_days:
    description:
      - The time retain this schema
    required: false
    type: int
  collation:
    description:
      - The collation to use on this schema
    required: false
    type: str
  managed_access:
    description:
      - Configure managed access for this schema
    required: false
    type: bool
  state:
    description:
      - The database state
    default: present
    choices: ["present", "absent"]
    type: str
notes:
   - Requires the snowflake Python package on the host. For Ubuntu, this
     is as easy as pip install snowflake-connector-python (See M(pip).)
requirements:
   - python >= 2.7
   - snowflake
   - snowflake-connector-python
seealso:
    - name: Snowflake Connection Parameters
      description: Comprehensive list of available Snowflake connection parameters
      link: https://docs.snowflake.com/en/user-guide/python-connector-api.html
author: Nate Fleming (@natefleming)
version_added: '1.0'
'''


EXAMPLES = r'''
- name: Create a schema (FOO) in the datbase (BAR) using the SYSADMIN role
  snowflake_schema:
    connection:
      role: SYSADMIN
    database: BAR
    schema: FOO
    state: present

- name: Delete a schema (FOO) in the datbase (BAR) using the SYSADMIN role
  snowflake_schema:
    connection:
      role: SYSADMIN
    database: BAR
    schema: FOO
    state: absent
'''

import os
import pipes
import subprocess
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.snowflake import snowflake_connect
from ansible.module_utils.snowflake import snowflake_found
from ansible.module_utils.snowflake import snowflake_missing_lib_exception
from ansible.module_utils.snowflake import snowflake_missing_lib_msg
from ansible.module_utils.snowflake import quoted_identifier
from ansible.module_utils.snowflake import fully_qualify


def schema_exists(cursor, database, schema):
    query = "SHOW SCHEMAS LIKE '{0}' IN DATABASE {1}".format(schema, database) if database else "SHOW SCHEMAS LIKE {0}".format(schema)
    cursor.execute(query)
    exists = cursor.rowcount > 0
    return exists


def schema_delete(cursor, database, schema):
    changed = False
    sfqid = None
    query = None
    if schema_exists(cursor, database, schema):
        schema = fully_qualify(database, schema)
        query = 'DROP SCHEMA {0}'.format(schema)
        cursor.execute(query)
        sfqid = cursor.sfqid
        changed = True
    return {'sql': query, 'schema': schema, 'changed': changed, 'sfqid': sfqid}


def schema_create(cursor, database, schema, clone, preposition, timestamp, offset, statement, retention_type_in_days, collation, managed_access, comment):
    changed = False
    sfqid = None
    query = None
    if not schema_exists(cursor, database, schema):
        schema = fully_qualify(database, schema)
        query = ['CREATE SCHEMA {0}'.format(schema)]
        query = query + ['CLONE {0}'.format(clone)] if clone else query
        query = query + [preposition.upper()] if preposition else query
        query = query + ["(STATEMENT => '{0}')".format(statement)] if statement else query
        query = query + ['(TIMESTAMP => {0})'.format(timestamp)] if timestamp else query
        query = query + ["(OFFSET => {0})".format(offset)] if offset else query
        query = query + ['DATA_RETENTION_TIME_IN_DAYS={0}'.format(retention_type_in_days)] if retention_type_in_days else query
        query = query + ["DEFAULT_DDL_COLLATION='{0}'".format(collation)] if collation else query
        query = query + ["WITH MANAGED ACCESS"] if managed_access else query
        query = query + ["COMMENT='{0}'".format(comment)] if comment else query
        query = ' '.join(query)
        cursor.execute(query)
        sfqid = cursor.sfqid
        changed = True

    return {'sql': query, 'schema': schema, 'changed': changed, 'sfqid': sfqid}


def create_connection(params):

    DEFAULT_CONNECTION = {
        "account": DEFAULT_ACCOUNT,
        "user": DEFAULT_USER,
        "password": DEFAULT_PWD,
        "role": DEFAULT_ROLE,
        "warehouse": DEFAULT_WAREHOUSE,
        "schema": DEFAULT_SCHEMA
    }

    options = DEFAULT_CONNECTION
    options.update(params)
    options = {key: value for (key, value) in options.items() if value}

    connection = snowflake.connector.connect(**options)

    return connection


def create_cursor(connection):

    cursor = connection.cursor()
    return cursor


def main():

    module = AnsibleModule(
        argument_spec=dict(
            connection=dict(default={}, type=dict),
            database=dict(default=None, aliases=['db']),
            name=dict(required=True, aliases=['schema', 'names', 'schemas']),
            state=dict(default="present", choices=["absent", "present"]),
            comment=dict(default=None),
            clone=dict(default=None),
            preposition=dict(default=None, choices=['at', 'before']),
            timestamp=dict(default=None),
            offset=dict(default=None),
            statement=dict(default=None),
            retention_time_in_days=dict(default=None, type=int),
            collation=dict(default=None),
            managed_access=dict(default=None, type=bool)
        ),
        supports_check_mode=True
    )

    if not snowflake_found:
        module.fail_json(msg=snowflake_missing_lib_msg, exception=snowflake_missing_lib_exception)

    database = module.params['database']
    name = [n.strip() for n in module.params['name'].split(',')]
    state = module.params['state']
    comment = module.params['comment']
    clone = module.params['clone']
    preposition = module.params['preposition']
    offset = module.params['offset']
    statement = module.params['statement']
    timestamp = module.params['timestamp']
    retention_type_in_days = module.params['retention_time_in_days']
    collation = module.params['collation']
    managed_access = module.params['managed_access']
    sfqid = None

    if preposition and not clone:
        module.fail_json(msg='Option clone is required with option preposition')

    if not preposition and (timestamp or offset or statement):
        module.fail_json(msg='Options preposition is required with offset, timestamp and statement')

    if sum(1 if x else 0 for x in [timestamp, offset, statement]) > 1:
        module.fail_json(msg='Options timestamp, offset and statement are mutually exclusive')

    try:
        connection = snowflake_connect(module.params['connection'])
        cursor = create_cursor(connection)
    except Exception as e:
        module.fail_json(msg="Unable to connect to database, check user and password are correct or has the credentials. Exception message: %s" % (e))

    changed = False
    results = []
    if state == "present":
        if module.check_mode:
            changed = any([not schema_exists(cursor, database, n) for n in name])
        else:
            try:
                results = [schema_create(
                    cursor,
                    database,
                    n,
                    clone,
                    preposition,
                    timestamp,
                    offset,
                    statement,
                    retention_type_in_days,
                    collation,
                    managed_access,
                    comment
                ) for n in name]
            except Exception as e:
                module.fail_json(msg="Error creating schema: %s" % to_native(e), exception=traceback.format_exc())
    elif state == "absent":
        if module.check_mode:
            changed = any([schema_exists(cursor, database, n) for n in name])
        else:
            try:
                results = [schema_delete(cursor, database, n) for n in name]
            except Exception as e:
                module.fail_json(msg="Error deleting schema: %s" % to_native(e), exception=traceback.format_exc())

    changed = any([result['changed'] for result in results]) if results else changed
    module.exit_json(changed=changed, state=state, results=results)


if __name__ == '__main__':
    main()
