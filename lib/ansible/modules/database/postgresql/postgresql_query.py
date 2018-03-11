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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: postgresql_query
short_description: Run arbitrary queries on a postgresql database.
description:
   - Run arbitrary queries on postgresql instances from the current host.
   - The function of this module is primarily to allow running queries which
     would benefit from bound parameters for SQL escaping.
   - Query results are returned as "query_result" as a list of dictionaries.
     Number of rows affected are returned as "row_count".
version_added: "2.4"
options:
  db:
    description:
      - name of database where permissions will be granted
    required: false
    default: null
  port:
    description:
      - Database port to connect to.
    required: false
    default: 5432
  login_user:
    description:
      - User (role) used to authenticate with PostgreSQL
    required: false
    default: postgres
  login_password:
    description:
      - Password used to authenticate with PostgreSQL
    required: false
    default: null
  login_host:
    description:
      - Host running PostgreSQL.
    required: false
    default: localhost
  unix_socket:
    description:
      - Path to a Unix domain socket for local connections
    required: false
    default: null
  ssl_mode:
    description:
      - SSL settings for the database connection.
      - allowed values are "disable","allow","prefer","require",
        "verify-ca","verify-full"
      - See http://www.postgresql.org/docs/current/static/libpq-connect.html#LIBPQ-CONNSTRING
    required: false
    default: prefer
  query:
    description:
      - SQL query to run. Variables can be escaped with psycopg2 syntax.
  positional_arguments:
    description:
      - A list of values to be passed as positional arguments to the query.
      - Cannot be used with named_arguments
  named_arguments:
    description:
      - A dictionary of key-value arguments to pass to the query.
      - Cannot be used with positional_argumetns
notes:
   - The default authentication assumes that you are either logging in as or
     sudo'ing to the postgres account on the host.
   - This module uses psycopg2, a Python PostgreSQL database adapter. You must
     ensure that psycopg2 is installed on the host before using this module. If
     the remote host is the PostgreSQL server (which is the default case), then
     PostgreSQL must also be installed on the remote host. For Ubuntu-based
     systems, install the postgresql, libpq-dev, and python-psycopg2 packages
     on the remote host before using this module.
requirements: [ psycopg2 ]
author: "Will Rouesnel (@wrouesnel)"
'''

EXAMPLES = '''
# Insert or update a record in a table with positional arguments
- postgresql_query:
    db: acme
    user: django
    password: ceec4eif7ya
    query: SELECT * FROM a_table WHERE a_column=%s AND b_column=%s
    positional_arguments:
    - "positional string value 1"
    - "positional string value 2"

# Insert or update a record in a table with named arguments
- postgresql_query:
    db: acme
    user: django
    password: ceec4eif7ya
    query: SELECT * FROM some_table WHERE a_column=%(a_value)s AND b_column=%(b_value)s
    named_arguments:
      a_value: "positional string value 1"
      b_value: "positional string value 2"
'''

RETURN = '''
query_result:
    description: list of dictionaries in column:value form
    returned: changed
    type: list
    sample: [{"Column": "Value1"},{"Column": "Value2"}]
row_count:
    description: number of affected rows by query, if applicable
    returned: changed
    type: int
    sample: 5
'''

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    postgresqldb_found = False
else:
    postgresqldb_found = True
from ansible.module_utils.six import iteritems

import re
import traceback

import ansible.module_utils.postgres as pgutils

from ansible.module_utils.database import SQLParseError, pg_quote_identifier
from ansible.module_utils.basic import get_exception, AnsibleModule

# ===========================================
# PostgreSQL module specific support methods.
#
# ===========================================
# Module execution.
#


def main():
    argument_spec = pgutils.postgres_common_argument_spec()
    argument_spec.update(dict(
        db=dict(default=''),
        query=dict(type="str"),
        positional_arguments=dict(type="list"),
        named_arguments=dict(type="dict")
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ["positional_arguments", "named_arguments"]
        ],
        supports_check_mode=False
    )

    db = module.params["db"]
    if db == '':
        module.fail_json(msg="a database must be specified")
    port = module.params["port"]

    if not postgresqldb_found:
        module.fail_json(msg="the python psycopg2 module is required")

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
              if k in params_map and v != "")

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    if psycopg2.__version__ < '2.4.3' and sslrootcert is not None:
        module.fail_json(msg='psycopg2 must be at least 2.4.3 in order to user the ssl_rootcert parameter')

    try:
        pgutils.ensure_libs(sslrootcert=module.params.get('ssl_rootcert'))
        db_connection = psycopg2.connect(**kw)
        cursor = db_connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)

    except pgutils.LibraryError:
        e = get_exception()
        module.fail_json(msg="unable to connect to database: {0}".format(
            str(e)), exception=traceback.format_exc())

    except TypeError:
        e = get_exception()
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least version 8.4 to support sslrootcert. Exception: {0}'.format(
                e), exception=traceback.format_exc())
        module.fail_json(msg="unable to connect to database: %s" %
                         e, exception=traceback.format_exc())

    except Exception:
        e = get_exception()
        module.fail_json(msg="unable to connect to database: %s" %
                         e, exception=traceback.format_exc())

    # Setup a datetime to string case
    def cast_timestamp(value, cur):
        if value is None:
            return None
        return str(value)

    cursor.execute("SELECT NULL::timestamp")
    oid = cursor.description[0][1]
    sqltype = psycopg2.extensions.new_type((oid,), "timestamp", cast_timestamp)
    psycopg2.extensions.register_type(sqltype)

    arguments = None
    if module.params["positional_arguments"] is not None:
        arguments = module.params["positional_arguments"]
    elif module.params["named_arguments"] is not None:
        arguments = module.params["named_arguments"]

    try:
        cursor.execute(module.params["query"], arguments)
    except NotSupportedError:
        e = get_exception()
        module.fail_json(msg=str(e))
    except SystemExit:
        # Avoid catching this on Python 2.4
        raise
    except Exception:
        e = get_exception()
        module.fail_json(msg="unable to execute query: %s" %
                         e, query_arguments=arguments)

    query_result = []
    if cursor.rowcount > 0:
        # There's no good way to return results arbitrarily without inspecting
        # the SQL, so we act consistent and return the empty set when there's
        # nothing to return.
        try:
            query_result = [dict(row) for row in cursor.fetchall()]
        except psycopg2.ProgrammingError:
            pass

    db_connection.commit()
    db_connection.close()

    module.exit_json(changed=True, query_result=query_result,
                     rowcount=len(query_result))

if __name__ == '__main__':
    main()
