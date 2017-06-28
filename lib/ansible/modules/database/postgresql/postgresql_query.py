#!/usr/bin/python
# -*- coding: utf-8 -*-

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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: postgresql_query
short_description: Run arbitrary queries on a postgresql database.
description:
   - Run arbitrary SQL queries against a PostgreSQL instance from the current host.
   - Query results are returned as "query_results" as a list of dictionaries.
     Number of rows affected are returned as "row_count".
   - Can read queries from a .sql script files.
   - SQL scripts may be templated with ansible variables at execution time.
version_added: "2.4"
options:
  db:
    description:
      - name of the database to run queries against.
    required: false
    default: postgres
  port:
    description:
      - Database port to connect to.
    required: false
    default: 5432
  login_user:
    description:
      - User (role) used to authenticate with PostgreSQL.
    required: false
    default: postgres
  login_password:
    description:
      - Password used to authenticate with PostgreSQL.
    required: false
    default: null
  login_host:
    description:
      - Host running PostgreSQL.
    required: false
    default: localhost
  login_unix_socket:
    description:
      - Path to a Unix domain socket for local connections.
    required: false
    default: null
  query:
    description:
      - SQL query to run. Variables can be escaped with psycopg2 syntax.
      - Can be a sql scripts file.
    required: true
  positional_args:
    description:
      - A list of values to be passed as positional arguments to the query.
      - Cannot be used with named_args.
    required: false
    default: null
  autocommit:
      description:
        - Enable transaction autocommit.
        - If enabled, This WILL run the query in check_mode.
      required: false
      default: false
      type: bool
  named_args:
    description:
      - A dictionary of key-value arguments to pass to the query.
      - Cannot be used with positional_args.
    required: false
    default: null
  fact:
    description:
        - Assign the query_results to a key by the name of this arg.
        - Will make this new variable available as a fact to subsequent tasks.
    required: false
    default: null
  ssl_mode:
    description:
      - Determines whether or with what priority a secure SSL TCP/IP connection will be negotiated with the server.
      - See https://www.postgresql.org/docs/current/static/libpq-ssl.html for more information on the modes.
      - Default of C(prefer) matches libpq default.
    required: false
    default: prefer
    choices: [disable, allow, prefer, require, verify-ca, verify-full]
  ssl_rootcert:
    description:
      - Specifies the name of a file containing SSL certificate authority (CA) certificate(s).
      - If the file exists, the server's certificate will be verified to be signed by one of these authorities.
    required: false
    default: null
notes:
   - The default authentication assumes that you are either logging in as or
     sudo'ing to the postgres account on the host.
   - This module uses psycopg2, a Python PostgreSQL database adapter. You must
     ensure that psycopg2 is installed on the host before using this module. If
     the remote host is the PostgreSQL server (which is the default case), then
     PostgreSQL must also be installed on the remote host. For Ubuntu-based
     systems, install the postgresql, libpq-dev, and python-psycopg2 packages
     on the remote host before using this module.
   - If the passlib library is installed, then passwords that are encrypted
     in the DB but not encrypted when passed as arguments can be checked for
     changes. If the passlib library is not installed, unencrypted passwords
     stored in the DB encrypted will be assumed to have changed.
   - If you specify PUBLIC as the user, then the privilege changes will apply
     to all users. You may not specify password or role_attr_flags when the
     PUBLIC user is specified.
   - The ssl_rootcert parameter requires at least Postgres version 8.4 and I(psycopg2) version 2.4.3.
requirements: [ psycopg2 ]
author:
    - "Felix Archambault (@archf)"
    - "Will Rouesnel (@wrouesnel)"
'''

EXAMPLES = '''
# Insert or update a record in a table with positional arguments
- postgresql_query:
    db: acme
    login_user: django
    login_password: ceec4eif7ya
    query: SELECT * FROM a_table WHERE a_column=%s AND b_column=%s
    positional_args:
      - "positional string value 1"
      - "positional string value 2"

# Insert or update a record in a table with named arguments
- postgresql_query:
    db: acme
    login_user: django
    login_password: ceec4eif7ya
    query: SELECT * FROM some_table WHERE a_column=%(a_value)s AND b_column=%(b_value)s
    positional_args:
      a_value: "positional string value 1"
      b_value: "positional string value 2"


# Run queries from a '.sql' file
- postgresql_query:
    db: acme
    login_user: django
    login_password: ceec4eif7ya
    query: "{{playbook_dir}}/scripts/my_sql_query_file.sql"
    named_args:
      a_value: "positional string value 1"
      b_value: "positional string value 2"

# Run queries from a '.sql' file and assign result in a fact available for the
# rest of the ansible runtime. Query inside scripts may contain 'named_args'
# or 'positional_args'.
- postgresql_query:
    db: acme
    login_user: django
    login_password: ceec4eif7ya
    query: SELECT * FROM some_table WHERE a_column=%(a_value)s AND b_column=%(b_value)s
    query: /path/to/my/script.sql
    named_args:
      a_value: "positional string value 1"
      b_value: "positional string value 2"
    fact: my_key
'''

RETURN = '''
query_results:
    description: List of dictionaries in column:value form representing returned rows.
    returned: changed
    type: list
    sample: [{"Column": "Value1"},{"Column": "Value2"}]
row_count:
    description: number of affected rows by query, if applicable
    returned: changed
    type: int
    sample: 5
'''

HAS_PSYCOPG2 = False
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    pass
else:
    HAS_PSYCOPG2 = True

import traceback
from ansible.module_utils.six import iteritems
from ansible.module_utils.basic import AnsibleModule, get_exception, BOOLEANS
import ansible.module_utils.postgres as pgutils


def main():
    argument_spec = pgutils.postgres_common_argument_spec()

    argument_spec.update(dict(
        db=dict(default=None),
        query=dict(type="str"),
        autocommit=dict(type='bool', default=False, choices=BOOLEANS),
        positional_args=dict(type="list"),
        named_args=dict(type="dict"),
        fact=dict(default=None),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ["positional_args", "named_args"]
        ],
        supports_check_mode=True,
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg="the python psycopg2 module is required")

    changed = False

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

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"

    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

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

    except TypeError:
        e = get_exception()
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='''Postgresql server must be at least version
                             8.4 to support sslrootcert.
                             Exception: {0}'''.format(e), exception=traceback.format_exc())
        module.fail_json(msg="unable to connect to database: %s" % e, exception=traceback.format_exc())

    except Exception:
        e = get_exception()
        module.fail_json(msg="unable to connect to database: {0}".format(str(e)), exception=traceback.format_exc())

    # if query is a file, load the file and run it
    query = module.params["query"]
    if query.endswith('.sql'):
        try:
            query = open(query, 'r').read().strip('\n')
        except Exception:
            e = get_exception()
            module.fail_json(msg="Unable to find '%s' in given path." % query)

    arguments = None

    # prepare args
    if module.params["positional_args"] is not None:
        arguments = module.params["positional_args"]

    elif module.params["named_args"] is not None:
        arguments = module.params["named_args"]

    try:
        cursor.execute(query, arguments)
    except Exception:
        e = get_exception()
        module.fail_json(msg="Unable to execute query: %s" % e,
                         query_arguments=arguments)

    ansible_facts = {}
    query_results = []
    if cursor.rowcount > 0:
        # There's no good way to return results arbitrarily without inspecting
        # the SQL, so we act consistent and return the empty set when there's
        # nothing to return.
        try:
            query_results = cursor.fetchall()
        except psycopg2.ProgrammingError:
            pass

        rowcount = len(query_results)
        fact = module.params["fact"]
        if fact is not None:
            ansible_facts = {fact: query_results}
    else:
        rowcount = 0

    statusmessage = cursor.statusmessage

    changed = False

    # set changed flag only on non read-only command
    if ("UPDATE" in statusmessage or "INSERT" in statusmessage or
            "UPSERT" in statusmessage or "DELETE" in statusmessage):
        changed = True

    if changed:
        if module.check_mode:
            db_connection.rollback()
        else:
            db_connection.commit()

    db_connection.close()

    module.exit_json(changed=changed, stout_lines=statusmessage,
                     query_results=query_results,
                     ansible_facts=ansible_facts,
                     rowcount=rowcount)

if __name__ == '__main__':
    main()
