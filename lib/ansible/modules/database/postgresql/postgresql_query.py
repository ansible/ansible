#!/usr/bin/python
# Copyright (c) 2017 Felix Archambault
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = '''
---
module: postgresql_query
short_description: Run arbitrary PostgreSQL queries.
description:
   - Run arbitrary PostgreSQL queries.
   - Can read queries from a .sql script files.
   - SQL scripts may be templated with ansible variables at execution time.
   - >
    Query results may be assigned to a variable for later reuse during ansible
    runtime.
version_added: "2.4"
options:
    db:
        description:
            - name of the database to run queries against.
        required: false
        default: None
    query:
        description:
            - SQL query to run. Variables can be escaped with psycopg2 syntax.
            - See U(http://initd.org/psycopg/docs/usage.html) and examples below.
            - This argument can also be a path to a SQL script file.
        required: true
    positional_args:
        description:
            - List of values to be passed as positional arguments to the query.
            - Cannot be used with I(named_args).
        required: false
        default: null
    named_args:
        description:
            - Dictionary of key-value arguments to pass to the query.
            - Cannot be used with I(positional_args).
        required: false
        default: null
    name:
        description:
            - The name of a variable into which assign the query_results.
            - Will make this new variable available as a fact to subsequent tasks.
        required: false
        default: null
    autocommit:
        description:
            - Enable transaction autocommit.
        required: false
        default: false
        type: bool

extends_documentation_fragment:
- postgres

requirements: [psycopg2]
author:
    - "Felix Archambault (@archf)"
    - "Will Rouesnel (@wrouesnel)"
'''

EXAMPLES = '''
# Simple select query.
- postgresql_query:
    db: acme
    login_user: django
    login_password: ceec4eif7ya
    query: SELECT * FROM my_table
    positional_args:
      - "first positional arg value"
      - "second positional arg value"

# Select query using named args.
- postgresql_query:
    db: acme
    login_user: django
    login_password: ceec4eif7ya
    query: SELECT * FROM some_table WHERE a_column=%(a_value)s AND b_column=%(b_value)s
    named_args:
      a_value: "named_arg value"
      b_value: "named_arg value"

# Run queries from a '.sql' script file. This file's script may contain
# 'named_args' or 'positional_args' placeholders.
- postgresql_query:
    db: acme
    login_user: django
    login_password: ceec4eif7ya
    query: "{{playbook_dir}}/scripts/my_sql_query_file.sql"
    named_args:
      a_value: "named arg value"
      b_value: "named arg value"

# Run query and assign result in a fact named 'my_key' that will be available
# for the rest of the ansible runtime.
- postgresql_query:
    db: acme
    login_user: django
    login_password: ceec4eif7ya
    name: my_key
    query: SELECT * FROM some_table WHERE a_column=%(a_value)s AND b_column=%(b_value)s
    named_args:
      a_value: "named arg value"
      b_value: "named arg value"
'''

RETURN = '''
query_results:
    description: List of dictionaries in column:value form representing returned rows.
    returned: changed
    type: list
    sample: [{"Column": "Value1"},{"Column": "Value2"}]
rowcount:
    description: Number of affected rows by query, if applicable.
    returned: changed
    type: int
    sample: 5
'''

import os
import traceback
from ansible.module_utils.six import iteritems
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.postgres as pgutils


def main():
    argument_spec = pgutils.postgres_common_argument_spec()

    argument_spec.update(dict(
        db=dict(default=None),
        query=dict(required=True, default=None),
        autocommit=dict(type="bool", default=False),
        positional_args=dict(type="list"),
        named_args=dict(type="dict"),
        name=dict(default=None),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ["positional_args", "named_args"],
            ["login_host", "login_unix_socket"]
        ],
        supports_check_mode=False,
    )

    changed = False
    psycopg2 = pgutils.psycopg2
    ansible_facts = {}
    query_results = []
    rowcount = 0

    # To use defaults values, keyword arguments must be absent, so
    # check which values are empty and don't include in the **kw
    # dictionary
    params_map = {
        "login_host": "host",
        "login_user": "user",
        "login_password": "password",
        "port": "port",
        "db": "database",
        "ssl_mode": "sslmode",
        "ssl_rootcert": "sslrootcert"
    }

    kw = dict((params_map[k], v) for (k, v) in iteritems(module.params)
              if k in params_map and v != '' and v is not None)

    try:
        pgutils.ensure_libs(sslrootcert=module.params.get('ssl_rootcert'))
        db_connection = psycopg2.connect(**kw)

        # Enable autocommit on demand only so we can create databases
        if module.params['autocommit']:
            if psycopg2.__version__ >= '2.4.2':
                db_connection.autocommit = True
            else:
                db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        # Using RealDictCursor allows access to row results by real column name
        cursor = db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    except Exception as e:
        db_connection.close()
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    # if query is a file, try read it
    query = module.params["query"]
    if query.endswith('.sql'):
        query = os.path.expanduser(query)
        try:
            query = open(query, 'r').read().strip('\n')
        except Exception as e:
            db_connection.close()
            module.fail_json(msg="Unable to find '%s' in given path." % query)

    # prepare args
    if module.params["positional_args"] is not None:
        arguments = module.params["positional_args"]
    elif module.params["named_args"] is not None:
        arguments = module.params["named_args"]
    else:
        arguments = None

    # execute query
    try:
        cursor.execute(query, arguments)
    except Exception as e:
        db_connection.close()
        module.fail_json(msg="Unable to execute query: %s" % e,
                         query_arguments=arguments)

    # retreive results
    if cursor.rowcount > 0:
        # There's no good way to return results arbitrarily without inspecting
        # the SQL, so we act consistent and return the empty set when there's
        # nothing to return.
        try:
            query_results = [dict(row) for row in cursor.fetchall()]
        except psycopg2.ProgrammingError:
            pass

        rowcount = len(query_results)
        fact = module.params["name"]
        if fact is not None:
            ansible_facts = {fact: query_results}

    statusmessage = cursor.statusmessage
    changed = False

    # set changed flag only on non read-only command
    if ("UPDATE" in statusmessage or "INSERT" in statusmessage or
            "UPSERT" in statusmessage or "DELETE" in statusmessage or
            "CREATE DATABASE" in statusmessage or
            "CREATE TABLE" in statusmessage or
            "DROP DATABASE" in statusmessage or
            "DROP TABLE" in statusmessage):
        changed = True
        db_connection.commit()

    db_connection.close()

    module.exit_json(changed=changed, stdout_lines=statusmessage,
                     query_results=query_results,
                     ansible_facts=ansible_facts,
                     rowcount=rowcount)

if __name__ == '__main__':
    main()
