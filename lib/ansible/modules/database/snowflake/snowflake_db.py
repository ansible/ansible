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
---
module: snowflake_db
short_description: Add or remove Snowflake databases
description:
   - Add or remove Snowflake databases
options:
  name:
    description:
      - The name of the database to add or remove
    required: true
    aliases: ["db", "database"]
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
      - The database to clone
    required: false
    type: str
  preposition:
    description:
      - Used when cloning a database at a certain time/offset or statement
    choices: ["at", "before"]
    required: false
    type: str
  timestamp:
    description:
      - Clone a database at a specific timestamp
    required: false
    type: str
  offset:
    description:
      - Clone a database at a specific offset
    required: false
    type: str
  statement:
    description:
      - Clone a database at a specific statement
    required: false
    type: str
  retention_time_in_days:
    description:
      - The time retain this database
    required: false
    type: Int
  collation:
    description:
      - The collation to use on this database
    required: false
    type: str
  share:
    description:
      - Configure the share for this database
    required: false
    type: str
  state:
    description:
      - The database state
    default: present
    choices: ["present", "absent"]
    type: str
notes:
   - Requires the snowflake Python package on the host. For Ubuntu, this
     is as easy as pip install snowflake-connector-python (See M(pip).)
   - check_mode is supported
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
- name: Create a database (FOO) with a retention time and a comment using the ACCOUNTADMIN role
  snowflake_db:
    connection:
        role: ACCOUNTADMIN
    name: FOO
    state: present
    retention_time_in_days: 9
    comment: My FOO Database

- name: Clone a database (BAR) from database (FOO) at a previous time
  snowflake_db:
    connection:
        role: MYROLE
    database: BAR
    clone: FOO
    state: present
    preposition: at
    timestamp: to_timestamp_tz('04/05/2013 01:02:03', 'mm/dd/yyyy hh24:mi:ss')
    retention_time_in_days: 9
    comment: My FOO database

- name: Delete FOO Database
  snowflake_db:
    connection:
        role: ACCOUNTADMIN
    name: FOO
    state: absent

- name: Delete BAR Database
  snowflake_db:
    connection:
        role: ACCOUNTADMIN
    database: BAR
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


def db_exists(cursor, db):
    query = 'SHOW DATABASES LIKE {0}'.format(quoted_identifier(db))
    cursor.execute(query)
    exists = cursor.rowcount > 0
    return exists


def db_delete(cursor, db):
    changed = False
    sfqid = None
    query = None
    if db_exists(cursor, db):
        query = 'DROP DATABASE {0}'.format(db)
        cursor.execute(query)
        sfqid = cursor.sfqid
        changed = True
    return {'sql': query, 'database': db, 'changed': changed, 'sfqid': sfqid}


def db_create(cursor, db, clone, preposition, timestamp, offset, statement, retention_type_in_days, collation, share, comment):
    changed = False
    sfqid = None
    query = None
    if not db_exists(cursor, db):
        query = ['CREATE DATABASE {0}'.format(db)]
        query = query + ['CLONE {0}'.format(clone)] if clone else query
        query = query + [preposition.upper()] if preposition else query
        query = query + ["(STATEMENT => '{0}')".format(statement)] if statement else query
        query = query + ['(TIMESTAMP => {0})'.format(timestamp)] if timestamp else query
        query = query + ["(OFFSET => {0})".format(offset)] if offset else query
        query = query + ['DATA_RETENTION_TIME_IN_DAYS={0}'.format(retention_type_in_days)] if retention_type_in_days else query
        query = query + ["DEFAULT_DDL_COLLATION='{0}'".format(collation)] if collation else query
        query = query + ["FROM SHARE {0}".format(share)] if share else query
        query = query + ["COMMENT='{0}'".format(comment)] if comment else query
        query = ' '.join(query)
        cursor.execute(query)
        sfqid = cursor.sfqid
        changed = True
    return {'sql': query, 'database': db, 'changed': changed, 'sfqid': sfqid}


def main():

    module = AnsibleModule(
        argument_spec=dict(
            connection=dict(default={}, type=dict),
            name=dict(required=True, aliases=['db', 'database']),
            state=dict(default="present", choices=["absent", "present"]),
            comment=dict(default=''),
            clone=dict(default=None),
            preposition=dict(default=None, choices=['at', 'before']),
            timestamp=dict(default=None),
            offset=dict(default=None),
            statement=dict(default=None),
            retention_time_in_days=dict(default=None, type=int),
            collation=dict(default=None),
            share=dict(default=None),
        ),
        supports_check_mode=True
    )

    if not snowflake_found:
        module.fail_json(msg=snowflake_missing_lib_msg, exception=snowflake_missing_lib_exception)

    names = [n.strip() for n in module.params['name'].split(',')]
    state = module.params['state']
    comment = module.params['comment']
    clone = module.params['clone']
    preposition = module.params['preposition']
    offset = module.params['offset']
    statement = module.params['statement']
    timestamp = module.params['timestamp']
    retention_type_in_days = module.params['retention_time_in_days']
    collation = module.params['collation']
    share = module.params['share']

    if preposition and not clone:
        module.fail_json(msg='Option clone is required with option preposition')

    if not preposition and (timestamp or offset or statement):
        module.fail_json(msg='Options preposition is required with offset, timestamp and statement')

    if sum(1 if x else 0 for x in [timestamp, offset, statement]) > 1:
        module.fail_json(msg='Options timestamp, offset and statement are mutually exclusive')

    if share and (clone or retention_type_in_days or collation or preposition or timestamp or offset or statement):
        module.fail_json(msg='Option share must be provided alone')

    try:
        connection = snowflake_connect(module.params['connection'])
        cursor = connection.cursor()
    except Exception as e:
        module.fail_json(msg="Unable to connect to database, check user and password are correct or has the credentials. Exception message: %s" % (e))

    changed = False
    if state == "present":
        if module.check_mode:
            changed = any([not db_exists(cursor, n) for n in names])
        else:
            try:
                results = [db_create(
                    cursor,
                    n,
                    clone,
                    preposition,
                    timestamp,
                    offset,
                    statement,
                    retention_type_in_days,
                    collation,
                    share,
                    comment
                ) for n in names]
            except Exception as e:
                module.fail_json(msg="Error creating database: %s" % to_native(e), exception=traceback.format_exc())

    elif state == "absent":
        if module.check_mode:
            changed = any([db_exists(cursor, n) for n in names])
        else:
            try:
                results = [db_delete(cursor, n) for n in names]
            except Exception as e:
                module.fail_json(msg="Error deleting database: %s" % to_native(e), exception=traceback.format_exc())

    changed = any([r['changed'] for r in results]) if results else changed
    module.exit_json(changed=changed, results=results, state=state)


if __name__ == '__main__':
    main()
