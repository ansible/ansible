#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Felix Archambault
# Copyright: (c) 2019, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = r'''
---
module: postgresql_query
short_description: Run PostgreSQL queries
description:
- Runs arbitrary PostgreSQL queries.
- Can run queries from SQL script files.
- Does not run against backup files. Use M(postgresql_db) with I(state=restore)
  to run queries on files made by pg_dump/pg_dumpall utilities.
version_added: '2.8'
options:
  query:
    description:
    - SQL query to run. Variables can be escaped with psycopg2 syntax U(http://initd.org/psycopg/docs/usage.html).
    type: str
  positional_args:
    description:
    - List of values to be passed as positional arguments to the query.
      When the value is a list, it will be converted to PostgreSQL array.
    - Mutually exclusive with I(named_args).
    type: list
  named_args:
    description:
    - Dictionary of key-value arguments to pass to the query.
      When the value is a list, it will be converted to PostgreSQL array.
    - Mutually exclusive with I(positional_args).
    type: dict
  path_to_script:
    description:
    - Path to SQL script on the remote host.
    - Returns result of the last query in the script.
    - Mutually exclusive with I(query).
    type: path
  session_role:
    description:
    - Switch to session_role after connecting. The specified session_role must
      be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though
      the session_role were the one that had logged in originally.
    type: str
  db:
    description:
    - Name of database to connect to and run queries against.
    type: str
    aliases:
    - login_db
  autocommit:
    description:
    - Execute in autocommit mode when the query can't be run inside a transaction block
      (e.g., VACUUM).
    - Mutually exclusive with I(check_mode).
    type: bool
    default: no
    version_added: '2.9'
seealso:
- module: postgresql_db
author:
- Felix Archambault (@archf)
- Andrew Klychkov (@Andersson007)
- Will Rouesnel (@wrouesnel)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Simple select query to acme db
  postgresql_query:
    db: acme
    query: SELECT version()

- name: Select query to db acme with positional arguments and non-default credentials
  postgresql_query:
    db: acme
    login_user: django
    login_password: mysecretpass
    query: SELECT * FROM acme WHERE id = %s AND story = %s
    positional_args:
    - 1
    - test

- name: Select query to test_db with named_args
  postgresql_query:
    db: test_db
    query: SELECT * FROM test WHERE id = %(id_val)s AND story = %(story_val)s
    named_args:
      id_val: 1
      story_val: test

- name: Insert query to test_table in db test_db
  postgresql_query:
    db: test_db
    query: INSERT INTO test_table (id, story) VALUES (2, 'my_long_story')

- name: Run queries from SQL script
  postgresql_query:
    db: test_db
    path_to_script: /var/lib/pgsql/test.sql
    positional_args:
    - 1

- name: Example of using autocommit parameter
  postgresql_query:
    db: test_db
    query: VACUUM
    autocommit: yes

- name: >
    Insert data to the column of array type using positional_args.
    Note that we use quotes here, the same as for passing JSON, etc.
  postgresql_query:
    query: INSERT INTO test_table (array_column) VALUES (%s)
    positional_args:
    - '{1,2,3}'

# Pass list and string vars as positional_args
- name: Set vars
  set_fact:
    my_list:
    - 1
    - 2
    - 3
    my_arr: '{1, 2, 3}'

- name: Select from test table by passing positional_args as arrays
  postgresql_query:
    query: SELECT * FROM test_array_table WHERE arr_col1 = %s AND arr_col2 = %s
    positional_args:
    - '{{ my_list }}'
    - '{{ my_arr|string }}'
'''

RETURN = r'''
query:
    description: Query that was tried to be executed.
    returned: always
    type: str
    sample: 'SELECT * FROM bar'
statusmessage:
    description: Attribute containing the message returned by the command.
    returned: always
    type: str
    sample: 'INSERT 0 1'
query_result:
    description:
    - List of dictionaries in column:value form representing returned rows.
    returned: changed
    type: list
    sample: [{"Column": "Value1"},{"Column": "Value2"}]
rowcount:
    description: Number of affected rows.
    returned: changed
    type: int
    sample: 5
'''

import datetime
import decimal

try:
    from psycopg2 import ProgrammingError as Psycopg2ProgrammingError
    from psycopg2.extras import DictCursor
except ImportError:
    # it is needed for checking 'no result to fetch' in main(),
    # psycopg2 availability will be checked by connect_to_db() into
    # ansible.module_utils.postgres
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.postgres import (
    connect_to_db,
    get_conn_params,
    postgres_common_argument_spec,
)
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems


# ===========================================
# Module execution.
#

def list_to_pg_array(elem):
    """Convert the passed list to PostgreSQL array
    represented as a string.

    Args:
        elem (list): List that needs to be converted.

    Returns:
        elem (str): String representation of PostgreSQL array.
    """
    elem = str(elem).strip('[]')
    elem = '{' + elem + '}'
    return elem


def convert_elements_to_pg_arrays(obj):
    """Convert list elements of the passed object
    to PostgreSQL arrays represented as strings.

    Args:
        obj (dict or list): Object whose elements need to be converted.

    Returns:
        obj (dict or list): Object with converted elements.
    """
    if isinstance(obj, dict):
        for (key, elem) in iteritems(obj):
            if isinstance(elem, list):
                obj[key] = list_to_pg_array(elem)

    elif isinstance(obj, list):
        for i, elem in enumerate(obj):
            if isinstance(elem, list):
                obj[i] = list_to_pg_array(elem)

    return obj


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        query=dict(type='str'),
        db=dict(type='str', aliases=['login_db']),
        positional_args=dict(type='list'),
        named_args=dict(type='dict'),
        session_role=dict(type='str'),
        path_to_script=dict(type='path'),
        autocommit=dict(type='bool', default=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=(('positional_args', 'named_args'),),
        supports_check_mode=True,
    )

    query = module.params["query"]
    positional_args = module.params["positional_args"]
    named_args = module.params["named_args"]
    path_to_script = module.params["path_to_script"]
    autocommit = module.params["autocommit"]

    if autocommit and module.check_mode:
        module.fail_json(msg="Using autocommit is mutually exclusive with check_mode")

    if positional_args and named_args:
        module.fail_json(msg="positional_args and named_args params are mutually exclusive")

    if path_to_script and query:
        module.fail_json(msg="path_to_script is mutually exclusive with query")

    if positional_args:
        positional_args = convert_elements_to_pg_arrays(positional_args)

    elif named_args:
        named_args = convert_elements_to_pg_arrays(named_args)

    if path_to_script:
        try:
            query = open(path_to_script, 'r').read()
        except Exception as e:
            module.fail_json(msg="Cannot read file '%s' : %s" % (path_to_script, to_native(e)))

    conn_params = get_conn_params(module, module.params)
    db_connection = connect_to_db(module, conn_params, autocommit=autocommit)
    cursor = db_connection.cursor(cursor_factory=DictCursor)

    # Prepare args:
    if module.params.get("positional_args"):
        arguments = module.params["positional_args"]
    elif module.params.get("named_args"):
        arguments = module.params["named_args"]
    else:
        arguments = None

    # Set defaults:
    changed = False

    # Execute query:
    try:
        cursor.execute(query, arguments)
    except Exception as e:
        cursor.close()
        db_connection.close()
        module.fail_json(msg="Cannot execute SQL '%s' %s: %s" % (query, arguments, to_native(e)))

    statusmessage = cursor.statusmessage
    rowcount = cursor.rowcount

    query_result = []
    try:
        for row in cursor.fetchall():
            # Ansible engine does not support decimals.
            # An explicit conversion is required on the module's side
            row = dict(row)
            for (key, val) in iteritems(row):
                if isinstance(val, decimal.Decimal):
                    row[key] = float(val)

                elif isinstance(val, datetime.timedelta):
                    row[key] = str(val)

            query_result.append(row)
    except Psycopg2ProgrammingError as e:
        if to_native(e) == 'no results to fetch':
            query_result = {}

    except Exception as e:
        module.fail_json(msg="Cannot fetch rows from cursor: %s" % to_native(e))

    if 'SELECT' not in statusmessage:
        if 'UPDATE' in statusmessage or 'INSERT' in statusmessage or 'DELETE' in statusmessage:
            s = statusmessage.split()
            if len(s) == 3:
                if statusmessage.split()[2] != '0':
                    changed = True

            elif len(s) == 2:
                if statusmessage.split()[1] != '0':
                    changed = True

            else:
                changed = True

        else:
            changed = True

    if module.check_mode:
        db_connection.rollback()
    else:
        if not autocommit:
            db_connection.commit()

    kw = dict(
        changed=changed,
        query=cursor.query,
        statusmessage=statusmessage,
        query_result=query_result,
        rowcount=rowcount if rowcount >= 0 else 0,
    )

    cursor.close()
    db_connection.close()

    module.exit_json(**kw)


if __name__ == '__main__':
    main()
