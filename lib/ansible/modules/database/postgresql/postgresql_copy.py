#!/usr/bin/python
# -*- coding: utf-8 -*-

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
module: postgresql_copy
short_description: Copy data between a file/program and a PostgreSQL table
description:
- Copy data between a file/program and a PostgreSQL table.
version_added: '2.9'

options:
  copy_to:
    description:
    - Copy the contents of a table to a file.
    - Can also copy the results of a SELECT query.
    - Mutually exclusive with I(copy_from) and I(dst).
    type: path
    aliases: [ to ]
  copy_from:
    description:
    - Copy data from a file to a table (appending the data to whatever is in the table already).
    - Mutually exclusive with I(copy_to) and I(src).
    type: path
    aliases: [ from ]
  src:
    description:
    - Copy data from I(copy_from) to I(src=tablename).
    - Used with I(copy_to) only.
    type: str
    aliases: [ source ]
  dst:
    description:
    - Copy data to I(dst=tablename) from I(copy_from=/path/to/data.file).
    - Used with I(copy_from) only.
    type: str
    aliases: [ destination ]
  columns:
    description:
    - List of column names for the src/dst table to COPY FROM/TO.
    type: list
    elements: str
    aliases: [ column ]
  program:
    description:
    - Mark I(src)/I(dst) as a program. Data will be copied to/from a program.
    - See block Examples and PROGRAM arg description U(https://www.postgresql.org/docs/current/sql-copy.html).
    type: bool
    default: no
  options:
    description:
    - Options of COPY command.
    - See the full list of available options U(https://www.postgresql.org/docs/current/sql-copy.html).
    type: dict
  db:
    description:
    - Name of database to connect to.
    type: str
    aliases: [ login_db ]
  session_role:
    description:
    - Switch to session_role after connecting.
      The specified session_role must be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though
      the session_role were the one that had logged in originally.
    type: str

notes:
- Supports PostgreSQL version 9.4+.
- COPY command is only allowed to database superusers.
- if I(check_mode=yes), we just check the src/dst table availability
  and return the COPY query that actually has not been executed.
- If i(check_mode=yes) and the source has been passed as SQL, the module
  will execute it and rolled the transaction back but pay attention
  it can affect database performance (e.g., if SQL collects a lot of data).

seealso:
- name: COPY command reference
  description: Complete reference of the COPY command documentation.
  link: https://www.postgresql.org/docs/current/sql-copy.html

author:
- Andrew Klychkov (@Andersson007)

extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Copy text TAB-separated data from file /tmp/data.txt to acme table
  postgresql_copy:
    copy_from: /tmp/data.txt
    dst: acme

- name: Copy CSV (comma-separated) data from file /tmp/data.csv to columns id, name of table acme
  postgresql_copy:
    copy_from: /tmp/data.csv
    dst: acme
    columns: id,name
    options:
      format: csv

- name: >
    Copy text vertical-bar-separated data from file /tmp/data.txt to bar table.
    The NULL values are specified as N
  postgresql_copy:
    copy_from: /tmp/data.csv
    dst: bar
    options:
      delimiter: '|'
      null: 'N'

- name: Copy data from acme table to file /tmp/data.txt in text format, TAB-separated
  postgresql_copy:
    src: acme
    copy_to: /tmp/data.txt

- name: Copy data from SELECT query to/tmp/data.csv in CSV format
  postgresql_copy:
    src: 'SELECT * FROM acme'
    copy_to: /tmp/data.csv
    options:
      format: csv

- name: Copy CSV data from my_table to gzip
  postgresql_copy:
    src: my_table
    copy_to: 'gzip > /tmp/data.csv.gz'
    program: yes
    options:
      format: csv

- name: >
    Copy data from columns id, name of table bar to /tmp/data.txt.
    Output format is text, vertical-bar-separated, NULL as N
  postgresql_copy:
    src: bar
    columns:
    - id
    - name
    copy_to: /tmp/data.csv
    options:
      delimiter: '|'
      null: 'N'
'''

RETURN = r'''
queries:
  description: List of executed queries.
  returned: always
  type: str
  sample: [ "COPY test_table FROM '/tmp/data_file.txt' (FORMAT csv, DELIMITER ',', NULL 'NULL')" ]
src:
  description: Data source.
  returned: always
  type: str
  sample: "mytable"
dst:
  description: Data destination.
  returned: always
  type: str
  sample: "/tmp/data.csv"
'''

try:
    from psycopg2.extras import DictCursor
except ImportError:
    # psycopg2 is checked by connect_to_db()
    # from ansible.module_utils.postgres
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import pg_quote_identifier
from ansible.module_utils.postgres import (
    connect_to_db,
    exec_sql,
    get_conn_params,
    postgres_common_argument_spec,
)
from ansible.module_utils.six import iteritems


class PgCopyData(object):

    """Implements behavior of COPY FROM, COPY TO PostgreSQL command.

    Arguments:
        module (AnsibleModule) -- object of AnsibleModule class
        cursor (cursor) -- cursor object of psycopg2 library

    Attributes:
        module (AnsibleModule) -- object of AnsibleModule class
        cursor (cursor) -- cursor object of psycopg2 library
        changed (bool) --  something was changed after execution or not
        executed_queries (list) -- executed queries
        dst (str) -- data destination table (when copy_from)
        src (str) -- data source table (when copy_to)
        opt_need_quotes (tuple) -- values of these options must be passed
            to SQL in quotes
    """

    def __init__(self, module, cursor):
        self.module = module
        self.cursor = cursor
        self.executed_queries = []
        self.changed = False
        self.dst = ''
        self.src = ''
        self.opt_need_quotes = (
            'DELIMITER',
            'NULL',
            'QUOTE',
            'ESCAPE',
            'ENCODING',
        )

    def copy_from(self):
        """Implements COPY FROM command behavior."""
        self.src = self.module.params['copy_from']
        self.dst = self.module.params['dst']

        query_fragments = ['COPY %s' % pg_quote_identifier(self.dst, 'table')]

        if self.module.params.get('columns'):
            query_fragments.append('(%s)' % ','.join(self.module.params['columns']))

        query_fragments.append('FROM')

        if self.module.params.get('program'):
            query_fragments.append('PROGRAM')

        query_fragments.append("'%s'" % self.src)

        if self.module.params.get('options'):
            query_fragments.append(self.__transform_options())

        # Note: check mode is implemented here:
        if self.module.check_mode:
            self.changed = self.__check_table(self.dst)

            if self.changed:
                self.executed_queries.append(' '.join(query_fragments))
        else:
            if exec_sql(self, ' '.join(query_fragments), ddl=True):
                self.changed = True

    def copy_to(self):
        """Implements COPY TO command behavior."""
        self.src = self.module.params['src']
        self.dst = self.module.params['copy_to']

        if 'SELECT ' in self.src.upper():
            # If src is SQL SELECT statement:
            query_fragments = ['COPY (%s)' % self.src]
        else:
            # If src is a table:
            query_fragments = ['COPY %s' % pg_quote_identifier(self.src, 'table')]

        if self.module.params.get('columns'):
            query_fragments.append('(%s)' % ','.join(self.module.params['columns']))

        query_fragments.append('TO')

        if self.module.params.get('program'):
            query_fragments.append('PROGRAM')

        query_fragments.append("'%s'" % self.dst)

        if self.module.params.get('options'):
            query_fragments.append(self.__transform_options())

        # Note: check mode is implemented here:
        if self.module.check_mode:
            self.changed = self.__check_table(self.src)

            if self.changed:
                self.executed_queries.append(' '.join(query_fragments))
        else:
            if exec_sql(self, ' '.join(query_fragments), ddl=True):
                self.changed = True

    def __transform_options(self):
        """Transform options dict into a suitable string."""
        for (key, val) in iteritems(self.module.params['options']):
            if key.upper() in self.opt_need_quotes:
                self.module.params['options'][key] = "'%s'" % val

        opt = ['%s %s' % (key, val) for (key, val) in iteritems(self.module.params['options'])]
        return '(%s)' % ', '.join(opt)

    def __check_table(self, table):
        """Check table or SQL in transaction mode for check_mode.

        Return True if it is OK.

        Arguments:
            table (str) - Table name that needs to be checked.
                It can be SQL SELECT statement that was passed
                instead of the table name.
        """
        if 'SELECT ' in table.upper():
            # In this case table is actually SQL SELECT statement.
            # If SQL fails, it's handled by exec_sql():
            exec_sql(self, table, add_to_executed=False)
            # If exec_sql was passed, it means all is OK:
            return True

        exec_sql(self, 'SELECT 1 FROM %s' % pg_quote_identifier(table, 'table'),
                 add_to_executed=False)
        # If SQL was executed successfully:
        return True


# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        copy_to=dict(type='path', aliases=['to']),
        copy_from=dict(type='path', aliases=['from']),
        src=dict(type='str', aliases=['source']),
        dst=dict(type='str', aliases=['destination']),
        columns=dict(type='list', aliases=['column']),
        options=dict(type='dict'),
        program=dict(type='bool', default=False),
        db=dict(type='str', aliases=['login_db']),
        session_role=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['copy_from', 'copy_to'],
            ['copy_from', 'src'],
            ['copy_to', 'dst'],
        ]
    )

    # Note: we don't need to check mutually exclusive params here, because they are
    # checked automatically by AnsibleModule (mutually_exclusive=[] list above).
    if module.params.get('copy_from') and not module.params.get('dst'):
        module.fail_json(msg='dst param is necessary with copy_from')

    elif module.params.get('copy_to') and not module.params.get('src'):
        module.fail_json(msg='src param is necessary with copy_to')

    # Connect to DB and make cursor object:
    conn_params = get_conn_params(module, module.params)
    db_connection = connect_to_db(module, conn_params, autocommit=False)
    cursor = db_connection.cursor(cursor_factory=DictCursor)

    ##############
    # Create the object and do main job:
    data = PgCopyData(module, cursor)

    # Note: parameters like dst, src, etc. are got
    # from module object into data object of PgCopyData class.
    # Therefore not need to pass args to the methods below.
    # Note: check mode is implemented inside the methods below
    # by checking passed module.check_mode arg.
    if module.params.get('copy_to'):
        data.copy_to()

    elif module.params.get('copy_from'):
        data.copy_from()

    # Finish:
    if module.check_mode:
        db_connection.rollback()
    else:
        db_connection.commit()

    cursor.close()
    db_connection.close()

    # Return some values:
    module.exit_json(
        changed=data.changed,
        queries=data.executed_queries,
        src=data.src,
        dst=data.dst,
    )


if __name__ == '__main__':
    main()
