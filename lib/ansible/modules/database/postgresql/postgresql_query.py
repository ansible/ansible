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
    - Mutually exclusive with I(named_args).
    type: list
  named_args:
    description:
    - Dictionary of key-value arguments to pass to the query.
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
notes:
- The default authentication assumes that you are either logging in as or
  sudo'ing to the postgres account on the host.
- To avoid "Peer authentication failed for user postgres" error,
  use postgres user as a I(become_user).
- This module uses psycopg2, a Python PostgreSQL database adapter. You must
  ensure that psycopg2 is installed on the host before using this module. If
  the remote host is the PostgreSQL server (which is the default case), then
  PostgreSQL must also be installed on the remote host. For Ubuntu-based
  systems, install the postgresql, libpq-dev, and python-psycopg2 packages
  on the remote host before using this module.
requirements: [ psycopg2 ]
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

- name: Insert query to db test_db
  postgresql_query:
    db: test_db
    query: INSERT INTO test_db (id, story) VALUES (2, 'my_long_story')

- name: Run queries from SQL script
  postgresql_query:
    db: test_db
    path_to_script: /var/lib/pgsql/test.sql
    positional_args:
    - 1
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

try:
    from psycopg2 import ProgrammingError as Psycopg2ProgrammingError
    from psycopg2.extras import DictCursor
except ImportError:
    # it is needed for checking 'no result to fetch' in main(),
    # psycopg2 availability will be checked by connect_to_db() into
    # ansible.module_utils.postgres
    pass

import ansible.module_utils.postgres as pgutils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import SQLParseError
from ansible.module_utils.postgres import connect_to_db, get_conn_params, postgres_common_argument_spec
from ansible.module_utils._text import to_native


# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        query=dict(type='str'),
        db=dict(type='str', aliases=['login_db']),
        positional_args=dict(type='list'),
        named_args=dict(type='dict'),
        session_role=dict(type='str'),
        path_to_script=dict(type='path'),
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

    if positional_args and named_args:
        module.fail_json(msg="positional_args and named_args params are mutually exclusive")

    if path_to_script and query:
        module.fail_json(msg="path_to_script is mutually exclusive with query")

    if path_to_script:
        try:
            query = open(path_to_script, 'r').read()
        except Exception as e:
            module.fail_json(msg="Cannot read file '%s' : %s" % (path_to_script, to_native(e)))

    conn_params = get_conn_params(module, module.params)
    db_connection = connect_to_db(module, conn_params, autocommit=False)
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

    try:
        query_result = [dict(row) for row in cursor.fetchall()]
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
