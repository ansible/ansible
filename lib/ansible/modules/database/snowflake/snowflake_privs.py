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
module: snowflake_privs
short_description: Grant or Revoke privileges from snowflake objects
description:
   -  Grant or Revoke privileges from snowflake objects
options:
  warehouse:
    description:
      - Provide the warehouse name when granting/revoking to/from warehouse
    aliases: ["wh"]
    type: str
  database:
    description:
      - Provide the database name when granting/revoking to/from databases
    aliases: ["db"]
    type: str
  schema:
    description:
      - Provide the schema name when granting/revoking to/from schema
    default: PUBLIC
    type: str
  objs:
    description:
      - The comma separated list of names of objects which to execute grants/revokes
    aliases: ["obj", "object", "objects"]
    type: str
  privileges:
    description:
      - The comma separated list of privileges
    aliases: ["priv", "privs", "privilege"]
    type: str
  roles:
    description:
      - The roles which to grant/revoke to or from
    aliases: ["role"]
    type: str
  users:
    description:
      - The user which to grant/revoke to or from
    aliases: ["user"]
    type: str
  type:
    description:
      - The types of objects to grant/revoke privileges to/from
    aliases: ["types", "obj_type", "obj_types"]
    default: table
    type: str
  future_option:
    description:
      - Include future grants/revokes
    type: str
    choices: ["yes", "no"]
  grant_option:
    description:
      - "Include 'WITH GRANT OPTION'"
    type: str
    choices: ["yes", "no"]
  connection:
    description:
      - Provide parameters to the snowflake connection
    required: false
    type: dict
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
author: "Nate Fleming (@natefleming)"
version_added: "1.0"
'''

EXAMPLES = r'''
- name: Grant SELECT,INSERT,UPDATE (with grants) on tables books and author to roles librarian, research
  snowflake_privs:
    database: BAR
    schema: FOO
    privs: SELECT,INSERT,UPDATE
    type: table
    objs: books,author
    roles: librarian, research
    grant_option: yes
    state: present

- name: Revoke Grants on SELECT,INSERT,UPDATE (with grants) on tables books and author to roles librarian, research
  snowflake_privs:
    database: BAR
    schema: FOO
    privs: SELECT,INSERT,UPDATE
    type: table
    objs: books,author
    roles: librarian, research
    grant_option: no
    state: present

- name: Revoke INSERT on the books table from the librarian role
  snowflake_privs:
    db: BAR
    schema: FOO
    priv: INSERT
    obj: books
    role: librarian
    state: absent

- name: Grant ALL privileges on the PUBLIC and BAZ schemas to the librarian role
  snowflake_privs:
    db: FOO
    privs: ALL
    type: schema
    objs: PUBLIC, BAZ
    role: librarian

- name: Grant ALL privileges on the function FOO.BAR.baz(int, int) to roles librarian and author
  snowflake_privs:
    db: FOO
    schema: BAR
    privs: ALL
    type: function
    obj: baz(int,int)
    roles: librarian, author

- name: Grant ALL privileges on database FOO to librarian
  snowflake_privs:
    db: FOO
    privs: ALL
    type: database
    role: librarian

- name: Grant ALL privileges on database FOO to librarian
  snowflake_privs:
    objs: FOO
    privs: ALL
    type: database
    role: librarian

- name: Grant USAGE on all functions in schema FOO.BAR to role authors
  snowflake_privs:
    db: FOO
    schema: BAR
    type: function
    state: present
    privs: USAGE
    roles: authors
    objs: ALL_IN_SCHEMA

- name: Grant USAGE on all functions in database FOO to role authors
  snowflake_privs:
    db: FOO
    type: function
    state: present
    privs: USAGE
    roles: authors
    objs: ALL_IN_DATABASE

- name: Grant role author to both librarian and user JOHN_SMITH
  snowflake_privs:
    db: DELETEME
    type: role
    state: present
    roles: librarian
    user: JOHN_SMITH
    objs: author

- name: Revoke role author from both librarian and user JOHN_SMITH
  snowflake_privs:
    db: DELETEME
    type: role
    state: absent
    roles: librarian
    user: JOHN_SMITH
    objs: author
'''


import os
import pipes
import subprocess
import traceback
import re
from distutils.util import strtobool

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.snowflake import snowflake_connect
from ansible.module_utils.snowflake import snowflake_found
from ansible.module_utils.snowflake import snowflake_missing_lib_exception
from ansible.module_utils.snowflake import snowflake_missing_lib_msg
from ansible.module_utils.snowflake import fully_qualify


def execute(cursor, queries):
    changed = []
    results = []

    for q in queries:
        cursor.execute(q)
        result = True
        results += [{
            'changed': result,
            'sfqid': cursor.sfqid,
            'sql': q
        }]
        changed += [result]

    return any(c for c in changed), results


def create_cursor(connection):

    cursor = connection.cursor()
    return cursor


def split(value, delimiter=','):
    if not value:
        return []
    pattern = r'{0}(?![^()]*\))'.format(delimiter)
    return [x.upper().strip() for x in re.split(pattern, value) if x.strip()]


def main():

    module = AnsibleModule(
        argument_spec=dict(
            connection=dict(default={}, type=dict),
            warehouse=dict(default=None, aliases=['wh']),
            database=dict(default=None, aliases=['db']),
            schema=dict(default='PUBLIC'),
            grant_option=dict(default=None, choices=['yes', 'no']),
            future_option=dict(default=None, choices=['yes', 'no']),
            objs=dict(default=None, aliases=['obj', 'object', 'objects']),
            privileges=dict(default=None, aliases=['priv', 'privs', 'privilege']),
            roles=dict(default=None, aliases=['role']),
            users=dict(default=None, aliases=['user']),
            type=dict(default='table', aliases=['types', 'obj_type', 'obj_types']),
            state=dict(default="present", choices=["absent", "present"])
        ),
        supports_check_mode=False
    )

    if not snowflake_found:
        module.fail_json(msg=snowflake_missing_lib_msg, exception=snowflake_missing_lib_exception)

    try:
        connection = snowflake_connect(module.params['connection'])
        cursor = create_cursor(connection)
    except Exception as e:
        module.fail_json(msg="Unable to connect to database, check user and password are correct or has the credentials. Exception message: %s" % (e))

    builder, state = create_privileges(module, module.params)
    try:
        changed, results = execute(cursor, builder())
    except Exception as e:
        module.fail_json(msg="Error granting privilege: %s" % to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=changed, results=results, state=state)


def create_privileges(module, params):

    warehouse = params['warehouse']
    database = params['database']
    schema = split(params['schema'])
    privileges = split(params['privileges'])
    objs = split(params['objs'])
    roles = split(params['roles'])
    users = split(params['users'])
    obj_types = split(params['type'])
    grant_option = strtobool(params['grant_option']) if params['grant_option'] else None
    future_option = strtobool(params['future_option']) if params['future_option'] else None
    state = params['state']

    def null_factory():
        return []
    factory = null_factory

    if 'OWNERSHIP' in privileges:
        factory = ownership_privileges(module, warehouse, database, schema, obj_types, objs, privileges, roles, grant_option, state)
    elif 'ACCOUNT' in obj_types:
        factory = global_privileges(module, obj_types, privileges, roles, grant_option, state)
    elif 'SCHEMA' in obj_types:
        factory = schema_privileges(module, database, schema, obj_types, objs, privileges, roles, grant_option, future_option, state)
    elif 'ROLE' in obj_types:
        factory = role_privileges(module, obj_types, objs, roles, users, state)
    elif len(set(obj_types).intersection(['RESOURCE MONITOR', 'WAREHOUSE', 'DATABASE', 'INTEGRATION'])):
        factory = account_object_privileges(module, warehouse, database, obj_types, objs, privileges, roles, grant_option, state)
    else:
        factory = schema_object_privileges(module, database, schema, obj_types, objs, privileges, roles, grant_option, future_option, state)

    return factory, state


def ownership_privileges(module, warehouse, database, schema, obj_types, objs, privileges, roles, grant_option, state):

    if len(privileges) > 1:
        module.fail_json(msg='privilege: OWNERSHIP is mutually exclusive')

    if not roles:
        module.fail_json(msg='missing required option: roles')

    obj_type = next(iter(obj_types or []), None)

    pattern = '^(ROLE|USER|WAREHOUSE|DATABASE|SCHEMA|TABLE|VIEW|STAGE|FILE\\s+FORMAT|STREAM|TASK|PIPE|INTEGRATION|FUNCTION|PROCEDURE|SEQUENCE)$'
    if 'ALL_IN_SCHEMA' in objs:
        pattern = '^(TABLE|VIEW|STAGE|FILE\\s+FORMAT|FUNCTION|PROCEDURE|SEQUENCE|STREAM|TASK)$'
    if not re.match(pattern, obj_type):
        module.fail_json(msg='object type: %s must match the pattern: %s' % (obj_type, pattern))

    objs = warehouse if not objs and obj_type == 'WAREHOUSE' else objs
    objs = schema if not objs and obj_type == 'SCHEMA' else objs
    objs = database if not objs and obj_type == 'DATABASE' else objs

    if not objs:
        module.fail_json(msg='missing required option: warehouse or database or schema or objs for type: %s' % obj_type)

    def grant():
        return create(True)

    def revoke():
        return []

    def create(present):
        with_grant_option = ''
        if grant_option is not None:
            with_grant_option = ' COPY CURRENT GRANTS' if grant_option else ' REVOKE CURRENT GRANTS'

        sql = []
        for obj in objs:
            sql_format = 'GRANT OWNERSHIP ON {obj_type} {obj} TO ROLE {role}{grant_option}'
            if obj == 'ALL_IN_SCHEMA':
                sql_format = 'GRANT OWNERSHIP ON ALL {obj_type}S IN SCHEMA {schema} TO ROLE {role}{grant_option}'
            sql += [sql_format.format(
                obj_type=obj_type,
                obj=(fully_qualify(database, schema, obj)),
                schema=(fully_qualify(database, s)),
                role=role,
                grant_option=with_grant_option
            ) for obj_type in obj_types for role in roles for s in schema]

        return sql

    return revoke if state == 'absent' else grant


def role_privileges(module, obj_types, objs, roles, users, state):

    if not objs:
        module.fail_json(msg='missing required option: objs')

    if not roles and not users:
        module.fail_json(msg='missing required option: roles or users')

    def grant():
        return create(True)

    def revoke():
        return create(False)

    def create(present):
        sql = []
        sql_format = '{action} ROLE {obj} {direction} {role} {to}'
        sql += [sql_format.format(
            action=('GRANT' if present else 'REVOKE'),
            obj=obj,
            direction=('TO' if present else 'FROM'),
            role='ROLE',
            to=role
        ) for obj in objs for role in roles]

        sql += [sql_format.format(
            action=('GRANT' if present else 'REVOKE'),
            obj=obj,
            direction=('TO' if present else 'FROM'),
            role='USER',
            to=user
        ) for obj in objs for user in users]

        return sql

    return revoke if state == 'absent' else grant


def schema_object_privileges(module, database, schema, obj_types, objs, privileges, roles, grant_option, future_option, state):

    if not future_option and not objs:
        module.fail_json(msg='missing required option: objs or future_option')

    if not future_option and not schema:
        module.fail_json(msg='missing required option: schema or future_option')

    if not roles:
        module.fail_json(msg='missing required option: roles')

    if not privileges:
        module.fail_json(msg='missing required option: privileges')

    obj_type = next(iter(obj_types or []), None)
    pattern = {
        'TABLE': '^(ALL|SELECT|INSERT|UPDATE|DELETE|TRUNCATE|REFERENCES)$',
        'VIEW': '^(ALL|SELECT)$',
        'MATERIALIZED VIEW': '^(ALL|SELECT)$',
        'STAGE': '^(ALL|USAGE|READ|WRITE)$',
        'FILE FORMAT': '^(ALL|USAGE)$',
        'FUNCTION': '^(ALL|USAGE)$',
        'SEQUENCE': '^(ALL|USAGE)$',
        'STREAM': '^(ALL|SELECT)$',
        'TASK': '^(ALL|MONITOR|OPERATE)$'
    }.get(obj_type)

    if not all(re.match(pattern, p) for p in privileges):
        module.fail_json(msg='privileges for object type: %s must match the pattern: %s' % (obj_type, pattern))

    privileges = ', '.join(privileges)

    def grant():
        return create(True)

    def revoke():
        return create(False)

    def create(present):
        with_grant_option = ' WITH GRANT OPTION' if grant_option and present else ''
        sql = []
        for obj in objs:
            sql_format = '{action} {privileges} ON {obj_type} {obj} {direction} ROLE {role}{grant_option}'
            if obj == 'ALL_IN_SCHEMA' or obj == 'ALL_IN_DATABASE':
                sql_format = '{action} {privileges} ON ALL {obj_type}S IN {target_type} {target_value} {direction} ROLE {role}{grant_option}'
            sql += [sql_format.format(
                action=('GRANT' if present else 'REVOKE'),
                privileges=privileges,
                obj_type=obj_type,
                obj=(fully_qualify(database, s, obj)),
                target_type=('DATABASE' if obj == 'ALL_IN_DATABASE' else 'SCHEMA'),
                target_value=(database if obj == 'ALL_IN_DATABASE' else fully_qualify(database, s)),
                direction=('TO' if present else 'FROM'),
                role=role,
                grant_option=with_grant_option
            ) for obj_type in obj_types for role in roles for s in schema]
            if future_option and obj in ['ALL_IN_SCHEMA', 'ALL_IN_DATABASE']:
                sql_format = '{action} {privileges} ON FUTURE {obj_type}S IN {target_type} {target_value} {direction} ROLE {role}{grant_option}'
                sql += [sql_format.format(
                    action=('GRANT' if present else 'REVOKE'),
                    privileges=privileges,
                    obj_type=obj_type,
                    target_type=('DATABASE' if obj == 'ALL_IN_DATABASE' else 'SCHEMA'),
                    target_value=(database if obj == 'ALL_IN_DATABASE' else fully_qualify(database, s)),
                    direction=('TO' if present else 'FROM'),
                    role=role,
                    grant_option=with_grant_option
                ) for obj_type in obj_types for role in roles for s in schema]

        return sql

    return revoke if state == 'absent' else grant


def schema_privileges(module, database, schema, obj_types, objs, privileges, roles, grant_option, future_option, state):
    if len(obj_types) > 1:
        module.fail_json(msg='object type: SCHEMA is mutually exclusive')

    objs = schema if not objs else objs

    if not objs:
        module.fail_json(msg='missing required option: objs or schema')

    if not roles:
        module.fail_json(msg='missing required option: roles')

    if not privileges:
        module.fail_json(msg='missing required option: privileges')

    obj_type = next(iter(obj_types or []), None)

    pattern = '^(ALL|MODIFY|MONITOR|USAGE|(CREATE\\s+(TABLE|VIEW|MATERIALIZED\\s+VIEW|FILE\\s+FORMAT|STAGE|PIPE|STREAM|TASK|SEQUENCE|FUNCTION|PROCEDURE)))$'
    if not all(re.match(pattern, p) for p in privileges):
        module.fail_json(msg='privileges for object type: %s must match the pattern: %s' % (obj_type, pattern))

    privileges = ', '.join(privileges)

    def grant():
        return create(True)

    def revoke():
        return create(False)

    def create(present):
        with_grant_option = ' WITH GRANT OPTION' if grant_option else ''
        sql = []
        for o in objs:
            if o == 'ALL_IN_DATABASE':
                when = ['ALL']
                when += ['FUTURE'] if future_option else []
                sql_format = '{action} {privileges} ON {when} SCHEMAS IN DATABASE {database} {direction} ROLE {role}{grant_option}'
                sql += [sql_format.format(
                    action=('GRANT' if present else 'REVOKE'),
                    privileges=privileges,
                    when=w,
                    database=database,
                    direction=('TO' if present else 'FROM'),
                    role=r,
                    grant_option=with_grant_option
                ) for r in roles for w in when]
            else:
                sql_format = '{action} {privileges} ON SCHEMA {obj} {direction} ROLE {role}{grant_option}'
                sql += [sql_format.format(
                    action=('GRANT' if present else 'REVOKE'),
                    privileges=privileges,
                    obj=fully_qualify(database, o),
                    direction=('TO' if present else 'FROM'),
                    role=r,
                    grant_option=with_grant_option
                ) for r in roles]

        return sql

    return revoke if state == 'absent' else grant


def account_object_privileges(module, warehouse, database, obj_types, objs, privileges, roles, grant_option, state):
    if len(obj_types) > 1:
        module.fail_json(msg='object types: RESOURCE MONITOR | WAREHOUSE | DATABASE | INTEGRATION are mutually exclusive')

    obj_type = next(iter(obj_types or []), None)
    pattern = {
        'RESOURCE MONITOR': '^(ALL|MODIFY|MONITOR)$',
        'WAREHOUSE': '^(ALL|MODIFY|MONITOR|USAGE|OPERATE)$',
        'DATABASE': '^(ALL|MODIFY|MONITOR|USAGE|CREATE\\s+SCHEMA|IMPORTED\\s+PRIVILEGES)$',
        'INTEGRATION': '^(ALL|USAGE)$'
    }.get(obj_type)

    if not all(re.match(pattern, p) for p in privileges):
        module.fail_json(msg='privileges for object type: %s must match the pattern: %s' % (obj_type, pattern))

    objs = [database] if not objs and obj_type == 'DATABASE' else objs
    objs = [warehouse] if not objs and obj_type == 'WAREHOUSE' else objs

    if not roles:
        module.fail_json(msg='missing required option: roles')

    if not privileges:
        module.fail_json(msg='missing required option: privileges')

    privileges = ', '.join(privileges)

    def grant():
        return create(True)

    def revoke():
        return create(False)

    def create(present):
        with_grant_option = ' WITH GRANT OPTION' if grant_option and present else ''
        sql_format = '{action} {privileges} ON {obj_type} {obj} {direction} ROLE {role}{grant_option}'
        sql = [sql_format.format(
            action=('GRANT' if present else 'REVOKE'),
            privileges=privileges,
            obj_type=obj_type,
            obj=o,
            direction=('TO' if present else 'FROM'),
            role=r,
            grant_option=with_grant_option
        ) for o in objs for r in roles]

        return sql

    return revoke if state == 'absent' else grant


def global_privileges(module, obj_types, privileges, roles, grant_option, state):
    if len(obj_types) > 1:
        module.fail_json(msg='object type: account is mutually exclusive')

    if not roles:
        module.fail_json(msg='missing required option: roles')

    if not privileges:
        module.fail_json(msg='missing required option: privileges')

    obj_type = next(iter(obj_types or []), None)
    pattern = '^(ALL|(CREATE\\s+(ROLE|USER|WAREHOUSE|DATABASE|INTEGRATION))|MANAGE\\s+GRANTS|MONITOR\\s+USAGE|EXECUTE\\s+TASK)$'
    if not all(re.match(pattern, p) for p in privileges):
        module.fail_json(msg='privileges must match the pattern: %s' % pattern)

    privileges = ', '.join(privileges)

    def grant():
        return create(True)

    def revoke():
        return create(False)

    def create(present):
        with_grant_option = ' WITH GRANT OPTION' if grant_option and present else ''
        sql_format = '{action} {privileges} ON {obj_type} {direction} ROLE {role}{grant_option}'
        sql = [sql_format.format(
            action=('GRANT' if present else 'REVOKE'),
            privileges=privileges,
            obj_type=obj_type,
            direction=('TO' if present else 'FROM'),
            role=r,
            grant_option=with_grant_option
        ) for r in roles]

        return sql

    return revoke if state == 'absent' else grant


if __name__ == '__main__':
    main()
