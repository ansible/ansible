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
module: snowflake_query
short_description: Add or remove Snowflake schemas
description:
   - Add or remove Snowflake schemas
options:
  schema:
    description:
      - A comma separated list of schemas to add or remove
    type: str
  database:
    description:
      - name of the database in which the schema resides
    aliases: ["db"]
    type: str
  connection:
    description:
      - Provide parameters to the snowflake connection
    required: false
    type: dict
  query:
    description:
      - The query to run
    required: true
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
author: "Nate Fleming (@natefleming)"
version_added: "1.0"
'''

EXAMPLES = r'''
- name: Run a select query using a specific role and warehouse.
  snowflake_query:
    connection:
      role: SYSADMIN
      warehouse: LOAD_WH
    database: DELETEME
    schema: PUBLIC
    query: SELECT * FROM FOO
- name: Run an insert query using the configured database
  snowflake_query:
    connection:
      role: SYSADMIN
      warehouse: LOAD_WH
    database: DELETEME
    query: INSERT INTO FOO(name, id) VALUES (1,1), (2,1)
- name: Insert datrra using the fully qualified name
  snowflake_query:
    connection:
      role: SYSADMIN
      warehouse: LOAD_WH
    query: INSERT INTO DELETEME.PUBLIC.FOO(name, id) VALUES (1,1), (2,1)
- name: Run a update query
  snowflake_query:
    connection:
      role: SYSADMIN
      database: DELETEME
      schema: PUBLIC
      warehouse: LOAD_WH
    query: UPDATE FOO SET id = id + 1
- name: Run a delete query
  snowflake_query:
    connection:
      role: SYSADMIN
      database: DELETEME
      schema: PUBLIC
      warehouse: LOAD_WH
    query: DELETE FROM FOO WHERE id > 2
'''

import os
import pipes
import stat
import subprocess
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.snowflake import snowflake_connect
from ansible.module_utils.snowflake import snowflake_found
from ansible.module_utils.snowflake import snowflake_missing_lib_exception
from ansible.module_utils.snowflake import snowflake_missing_lib_msg
from ansible.module_utils.snowflake import quoted_identifier


def query_insert(cursor, query):
    cursor.execute(query)
    sfqid = cursor.sfqid
    row = cursor.fetchone()
    rows_inserted = row[0]
    return rows_inserted, sfqid


def query_delete(cursor, query):
    cursor.execute(query)
    sfqid = cursor.sfqid
    row = cursor.fetchone()
    rows_deleted = row[0]
    return rows_deleted, sfqid


def query_update(cursor, query):
    cursor.execute(query)
    sfqid = cursor.sfqid
    row = cursor.fetchone()
    rows_updated = row[0]
    return rows_updated, sfqid


def query_select(cursor, query):
    cursor.execute(query)
    sfqid = cursor.sfqid
    num_fields = len(cursor.description)
    field_names = [i[0] for i in cursor.description]
    columns = cursor.description
    result_set = [{columns[index][0]:column for index, column in enumerate(value)} for value in cursor.fetchall()]
    return result_set, cursor.rowcount, field_names, sfqid


def create_cursor(connection, database, schema):

    cursor = connection.cursor()

    if database:
        cursor.execute('USE DATABASE %s' % database)

    if schema:
        cursor.execute('USE SCHEMA %s' % schema)

    return cursor


def main():

    module = AnsibleModule(
        argument_spec=dict(
            connection=dict(default={}, type=dict),
            database=dict(default=None, aliases=['db']),
            schema=dict(default=None),
            query=dict(required=True)
        ),
        supports_check_mode=False
    )

    if not snowflake_found:
        module.fail_json(msg=snowflake_missing_lib_msg, exception=snowflake_missing_lib_exception)

    changed = False

    database = module.params['database']
    schema = module.params['schema']
    query = module.params['query'].strip()

    try:
        connection = snowflake_connect(module.params['connection'])
        cursor = create_cursor(connection, database, schema)
    except Exception as e:
        module.fail_json(msg='unable to connect to database, check user and password are correct or has the credentials. Exception message: %s' % (e))

    try:
        if query.upper().startswith('SELECT'):
            result_set, row_count, field_names, sfqid = query_select(cursor, query)
            connection.commit()
            changed = True
            module.exit_json(changed=changed, result_set=result_set, row_count=row_count, field_names=field_names, sfqid=sfqid)
        elif query.upper().startswith('INSERT'):
            rows_inserted, sfqid = query_insert(cursor, query)
            connection.commit()
            changed = True
            module.exit_json(changed=changed, rows_inserted=rows_inserted, sfqid=sfqid)
        elif query.upper().startswith('UPDATE'):
            rows_updated, sfqid = query_update(cursor, query)
            connection.commit()
            changed = True
            module.exit_json(changed=changed, rows_updated=rows_updated, sfqid=sfqid)
        elif query.upper().startswith('DELETE'):
            rows_deleted, sfqid = query_delete(cursor, query)
            connection.commit()
            changed = True
            module.exit_json(changed=changed, rows_deleted=rows_deleted, sfqid=sfqid)
        else:
            module.fail_json(msg='Query type unsupported')

    except Exception as e:
        module.fail_json(msg='Unable to run query against database. Exception message is %s' % (e))


if __name__ == '__main__':
    main()
