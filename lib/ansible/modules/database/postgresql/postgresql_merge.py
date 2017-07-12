#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ted Trask <ttrask01@yahoo.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: postgresql_merge
short_description: Merge database entries into a Postgresql database table.
description:
  - Merge database entries into a Postgresql database table.
version_added: "2.5"
author: Ted Trask (@tdtrask) <ttrask01@yahoo.com>
options:
  database:
    description:
      - Name of database to connect to.
      - 'Alias: I(db)'
    required: true
  table:
    description:
      - Name of table where entries will be merged
    required: true
  entries:
    description:
      - List of database entries in Values expression format. See https://www.postgresql.org/docs/current/static/queries-values.html
        for examples. The first entry must contain the column names. The second entry may contain type casts if necessary.
    required: true
  fields:
    description:
      - List of fields to match on. If not specified, postgresql_merge will attempt to use the primary key or unique constraint.
  delete:
    description:
      - Delete non-matching rows.
    default: False
  port:
    description:
      - Database port to connect to.
    default: 5432
  user:
    description:
      - User (role) used to authenticate with PostgreSQL.
      - 'Alias: I(login_user), I(login)'
    default: postgres
  password:
    description:
      - Password used to authenticate with PostgreSQL.
      - 'Alias: I(login_password))'
    default: null
  host:
    description:
      - Host running PostgreSQL.
      - 'Alias: I(login_host)'
    default: localhost
  unix_socket:
    description:
      - Path to a Unix domain socket for local connections.
      - 'Alias: I(login_unix_socket)'
    default: null
  ssl_mode:
    description:
      - Determines whether or with what priority a secure SSL TCP/IP connection will be negotiated with the server.
      - See https://www.postgresql.org/docs/current/static/libpq-ssl.html for more information on the modes.
      - Default of C(prefer) matches libpq default.
    default: prefer
    choices: [disable, allow, prefer, require, verify-ca, verify-full]
  ssl_rootcert:
    description:
      - Specifies the name of a file containing SSL certificate authority (CA) certificate(s). If the file exists, the server's certificate will be
        verified to be signed by one of these authorities.
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
   - If you specify PUBLIC as the user, then the privilege changes will apply
     to all users. You may not specify password or role_attr_flags when the
     PUBLIC user is specified.
   - The ssl_rootcert parameter requires at least Postgres version 8.4 and I(psycopg2) version 2.4.3.
requirements: [ psycopg2 ]
'''

EXAMPLES = '''
# Merge database entry
- postgresql_merge:
    database: testdb
    table: films
    entries:
        - "code,title,did,date_prod,kind"
        - "'UA502','Bananas',105,'1971-07-13'::date,'Comedy'"
'''

RETURN = ''' # '''

import re
from ansible.module_utils.six import iteritems
from ansible.module_utils.basic import AnsibleModule

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    postgresqldb_found = False
else:
    postgresqldb_found = True

# ===========================================
# PostgreSQL module specific support methods.
#


def lock_table(cursor, table):
    query = 'LOCK TABLE %s IN ACCESS EXCLUSIVE MODE' % table
    cursor.execute(query)


def get_version(cursor):
    query = 'SHOW server_version_num'
    try:
        cursor.execute(query)
        return cursor.fetchone()[0]
    except Exception:
        return 0
    return 0


def get_primary_key(cursor, table):
    # Returns an array of column names making up the primary key (or Null)
    key = []
    query = ("SELECT pg_attribute.attname AS field FROM pg_index, pg_class, pg_attribute WHERE pg_class.oid = '%s'::regclass "
             "AND indrelid = pg_class.oid AND pg_attribute.attrelid = pg_class.oid AND pg_attribute.attnum = any(pg_index.indkey) AND indisprimary" % table)
    cursor.execute(query)
    for k in cursor:
        key.append(k[0])
    return key


def get_unique_constraint(cursor, table):
    # Returns an array of column names making up the single unique constraint (or Null)
    indexrelid = None
    constraint = []
    query = ("SELECT pg_attribute.attname AS field, indexrelid FROM pg_index, pg_class, pg_attribute WHERE pg_class.oid = '%s'::regclass "
             "AND indrelid = pg_class.oid AND pg_attribute.attrelid = pg_class.oid AND pg_attribute.attnum = any(pg_index.indkey) AND indisunique" % table)
    cursor.execute(query)
    for k in cursor:
        if indexrelid is None:
            indexrelid = k[1]
        elif indexrelid != k[1]:
            # Found second unique index
            constraint = []
            break
        constraint.append(k[0])
    return constraint


def determine_fields(cursor, table, fields):
    # First, determine what fields we compare on
    if not fields:
        # Check for primary key
        fields = get_primary_key(cursor, table)
    if not fields:
        # Check for single unique constraint
        fields = get_unique_constraint(cursor, table)
    if not fields:
        raise ValueError("Cannot determine merge fields, must be specified")
    return fields


def format_fields(fields):
    return ','.join(fields)


def format_entries(entries):
    rows = []
    for num, row in enumerate(entries, start=0):
        if num != 0 and row != "":
            rows.append('(%s)' % row)
    return ','.join(rows)


def format_diff(cursor):
    # Ansible cannot handle returns of random types, so convert each row to a string
    diff = []
    row = []
    for r in cursor:
        for e in r:
            row.append(cursor.mogrify("%s", (e,)))
        diff.append(','.join(row))
    return diff


def check_update(cursor, table, headers, entries, delete, fields):
    before = None
    after = None
    formatted_entries = format_entries(entries)
    formatted_fields = format_fields(fields)
    # Check for differences between the VALUES and actual table using SQL EXCEPT
    query = 'SELECT * FROM (VALUES %s) AS t(%s) EXCEPT SELECT * FROM %s' % (formatted_entries, headers, table)
    cursor.execute(query)
    if cursor.rowcount > 0:
        after = format_diff(cursor)

    if delete:
        query = 'SELECT * FROM %s EXCEPT SELECT * FROM (VALUES %s) AS t(%s)' % (table, formatted_entries, headers)
    else:
        query = ('WITH valuestable AS (SELECT * FROM (VALUES %s) AS t(%s)) SELECT * FROM %s WHERE (%s) IN (SELECT %s FROM valuestable) '
                 'AND (%s) NOT IN (SELECT * FROM valuestable)' % (formatted_entries, headers, table, formatted_fields, formatted_fields, headers))
    cursor.execute(query)
    if cursor.rowcount > 0:
        before = format_diff(cursor)
    if before or after:
        diff = {}
        diff['before'] = before
        diff['after'] = after
        return diff
    return None


def perform_update(cursor, table, headers, entries, delete, fields):
    formatted_entries = format_entries(entries)
    formatted_fields = format_fields(fields)
    # First, insert / update rows
    # Check server version, because ON CONFLICT supported on postgresql >= 9.5
    upsert_success = False
    version = get_version(cursor)

    # Try the ON CONFLICT method
    if int(version) >= 90500:
        try:
            query = ('INSERT INTO %s (%s) VALUES %s ON CONFLICT (%s) DO UPDATE SET (%s) = (excluded.%s)' %
                     (table, headers, formatted_entries, formatted_fields, headers, re.sub(r',', ",excluded.", re.sub(r'\s', '', headers))))
            cursor.execute(query)
            upsert_success = True
        except:
            upsert_success = False

    # Try the UPDATE / INSERT per row
    if upsert_success is False:
        indeces = None
        for row in entries:
            entry = re.split(''',(?=(?:[^']|'[^']*')*$)''', row)
            if indeces is None:
                # Parse the header row to determine column indeces
                indeces = []
                for i, field in enumerate(fields, start=0):
                    for j, e in enumerate(entry, start=0):
                        if field == e:
                            indeces.append(j)
                            break
                if len(fields) != len(indeces):
                    raise ValueError("Cannot find all fields in header row")
            else:
                values = []
                for i, field in enumerate(fields, start=0):
                    values.append(entry[indeces[i]])
                query = 'UPDATE %s SET (%s) = (%s) WHERE (%s) = (%s)' % (table, headers, row, formatted_fields, ','.join(values))
                cursor.execute(query)
                if cursor.rowcount == 0:
                    query = 'INSERT INTO %s (%s) VALUES (%s)' % (table, headers, row)
                    cursor.execute(query)

    # Next, delete rows
    if delete:
        # Check for differences between the VALUES and actual table using SQL EXCEPT
        query = ('DELETE FROM %s WHERE (%s) IN (SELECT %s FROM %s EXCEPT SELECT %s FROM (VALUES %s) AS t(%s))' %
                 (table, formatted_fields, formatted_fields, table, formatted_fields, formatted_entries, headers))
        cursor.execute(query)

# ===========================================
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            database=dict(required=True, aliases=['db']),
            table=dict(required=True),
            entries=dict(type='list', required=True),
            fields=dict(type='list'),
            delete=dict(type='bool', default='no'),
            port=dict(default='5432'),
            user=dict(default='postgres', aliases=['login_user', 'login']),
            password=dict(default='', aliases=['login_password'], no_log=True),
            host=dict(default='localhost', aliases=['login_host']),
            unix_socket=dict(default='', aliases=['login_unix_socket']),
            ssl_mode=dict(default='prefer', choices=['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']),
            ssl_rootcert=dict(default=None)
        ),
        supports_check_mode=True
    )

    p = module.params

    if not postgresqldb_found:
        module.fail_json(msg="the python psycopg2 module is required")

    # To use defaults values, keyword arguments must be absent, so
    # check which values are empty and don't include in the **kw
    # dictionary
    params_map = {
        "host": "host",
        "user": "user",
        "password": "password",
        "port": "port",
        "database": "database",
        "ssl_mode": "sslmode",
        "ssl_rootcert": "sslrootcert"
    }
    kw = dict((params_map[k], v) for (k, v) in iteritems(p)
              if k in params_map and v != "" and v is not None)

    # If a unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"
    if is_localhost and p["unix_socket"] != "":
        kw["host"] = p["unix_socket"]

    if psycopg2.__version__ < '2.4.3' and p["ssl_rootcert"] is not None:
        module.fail_json(msg='psycopg2 must be at least 2.4.3 in order to user the ssl_rootcert parameter')

    try:
        db_connection = psycopg2.connect(**kw)
        cursor = db_connection.cursor()
    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least version 8.4 to support sslrootcert')
        module.fail_json(msg="unable to connect to database: %s" % e)
    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % e)

    diff = None
    try:
        # Lock the table. This will kill performance but ensure correctness.
        # If this table is being updated often, it probably shouldn't be configured by Ansible anyway.
        if not module.check_mode:
            lock_table(cursor, p["table"])

        table = p["table"]
        headers = p["entries"][0]
        entries = p["entries"]
        delete = p["delete"]
        fields = determine_fields(cursor, table, p["fields"])

        # Check if will cause change. This is done as a separate step because INSERT .. ON CONFLICT does not report actual changes
        diff = check_update(cursor, table, headers, entries, delete, fields)

        if diff and not module.check_mode:
            perform_update(cursor, table, headers, entries, delete, fields)

        if diff and not module.check_mode:
            db_connection.commit()
        else:
            db_connection.rollback()
    except Exception as e:
        module.fail_json(msg=str(e))

    module.exit_json(changed=(diff is not None), diff=diff)

if __name__ == '__main__':
    main()
