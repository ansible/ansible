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
module: postgresql_vacuum
short_description: Garbage-collect and optionally analyze a PostgreSQL database
description:
- Garbage-collect and optionally analyze a PostgreSQL database
  U(https://www.postgresql.org/docs/current/sql-vacuum.html).
version_added: '2.9'

options:
  table:
    description:
    - Name of a table that needs to be vacuumed.
    type: str
  columns:
    description:
    - List of column names of I(table) that need to be vacuumed.
      Used only with I(table).
    type: list
  analyze:
    description:
    - Updates statistics used by the planner to determine the most efficient way to execute a query.
    - Mutually exclusive with I(analyze_only).
    type: bool
  analyze_only:
    description:
    - Only update optimizer statistics, no vacuum. Mutually exclusive with I(analyze).
    type: bool
  full:
    description:
    - Selects full vacuum, which can reclaim more space,
      but takes much longer and exclusively locks the table.
    - This method also requires extra disk space, since it writes a new copy
      of the table and doesn't release the old copy until the operation is complete.
    - Usually this should only be used when a significant amount of space needs
      to be reclaimed from within the table.
    - Mutually exclusive with I(analyze_only).
    type: bool
  disable_page_skipping:
    description:
    - Normally, VACUUM will skip pages based on the visibility map.
    - Pages where all tuples are known to be frozen can always be skipped,
      and those where all tuples are known to be visible to all transactions
      may be skipped except when performing an aggressive vacuum.
    - Furthermore, except when performing an aggressive vacuum,
      some pages may be skipped in order to avoid waiting for other sessions to finish using them.
    - This option disables all page-skipping behavior, and is intended to be used only when
      the contents of the visibility map are suspect, which should happen only if there is
      a hardware or software issue causing database corruption.
    - Available from PostgreSQL 9.6.
    - Mutually exclusive with I(analyze_only).
    type: bool
  freeze:
    description:
    - Selects aggressive freezing of tuples.
    - Specifying FREEZE is equivalent to performing VACUUM with
      the vacuum_freeze_min_age and vacuum_freeze_table_age parameters set to zero.
      Aggressive freezing is always performed when the table is rewritten,
      so this option is redundant when FULL is specified.
    - Mutually exclusive with I(analyze_only).
  db:
    description:
    - Name of a database for vacuum (used as a database to connect to).
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

author:
- Andrew Klychkov (@Andersson007)

extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Vacuum database acme
  postgresql_vacuum:
    db: acme

- name: Vacuum and analyze database acme
  postgresql_vacuum:
    db: acme
    analyze: yes

- name: Vacuum full and analyze database foo. Pay attention that the database will be locked
  postgresql_vacuum:
    db: foo
    full: yes
    analyze: yes

- name: Analyze table mytable in database bar
  postgresql_vacuum:
    db: bar
    table: mytable
    analyze_only: yes

- name: Vacuum and analyze columns col1, col2, and col3 of mytable in database acme
  postgresql_vacuum:
    db: acme
    table: mytable
    columns:
    - col1
    - col2
    - col3
    analyze: yes

- name: Vacuum of mytable with freeze
  postgresql_vacuum:
    db: acme
    table: mytable
    freeze: yes

- name: Vacuum of mytable with disabled page skipping
  postgresql_vacuum:
    db: acme
    table: mytable
    disable_page_skipping: yes
'''

RETURN = r'''
queries:
  description: List of executed queries.
  returned: always
  type: str
  sample: [ "VACUUM (ANALYZE) mytable (col1, col2, col3)" ]
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
    postgres_common_argument_spec,
)
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems


DISABLE_PAGE_SKIPPING_VER = 96000


class Vacuum(object):

    """Implements VACUUM [FULL] and/or ANALYZE PostgreSQL command behavior.

    args:
        module (AnsibleModule) -- object of AnsibleModule class
        cursor (cursor) -- cursor objec of psycopg2 library

    attrs:
        module (AnsibleModule) -- object of AnsibleModule class
        cursor (cursor) -- cursor objec of psycopg2 library
        changed (bool) --  something was changed after execution or not
        executed_queries (list) -- executed queries
        query_frag (list) -- list for making SQL query
    """

    def __init__(self, module, cursor):
        self.module = module
        self.cursor = cursor
        self.executed_queries = []
        self.changed = False
        self.query_frag = []

    def __check_obj(self):
        """
        Check the table or columns that need to be vacuumed/analyzed exist.
        """

        query_frag = ['SELECT']
        if self.module.params.get('columns'):
            query_frag.append(','.join(self.module.params['columns']))
        else:
            query_frag.append('*')

        query_frag.append('FROM %s LIMIT 1' % pg_quote_identifier(self.module.params['table'], 'table'))

        if exec_sql(self, ' '.join(query_frag), ddl=True, add_to_executed=False):
            return True

        return None

    def do_vacuum(self):
        """Do VACUUM."""

        self.query_frag.append('VACUUM')

        if (self.module.params.get('freeze') or
                self.module.params.get('disable_page_skipping') or
                self.module.params.get('analyze')):

            opt_list = []
            if self.module.params.get('freeze'):
                opt_list.append('FREEZE')

            if self.module.params.get('disable_page_skipping'):
                opt_list.append('DISABLE_PAGE_SKIPPING')

            if self.module.params.get('analyze'):
                opt_list.append('ANALYZE')

            self.query_frag.append('(%s)' % ', '.join(opt_list))

        self.__do_rest_of_task()

    def do_analyze(self):
        """Do ANALYZE."""

        self.query_frag.append('ANALYZE')

        self.__do_rest_of_task()

    def do_full_vacuum(self):
        """Do VACUUM FULL."""

        self.query_frag.append('VACUUM FULL')

        if self.module.params.get('analyze'):
            self.query_frag.append('ANALYZE')

        self.__do_rest_of_task()

    def __do_rest_of_task(self):
        """Do the rest of the task for all public methods.

        Complete query fragments list self.query_frag if needed and make SQL query.
        If check_mode, change self.changed and return None, otherwise, execute SQL.
        """

        if self.module.params.get('table'):
            self.query_frag.append('%s' % pg_quote_identifier(self.module.params['table'], 'table'))

        if self.module.params.get('columns'):
            self.query_frag.append('(%s)' % ', '.join(self.module.params['columns']))

        query = ' '.join(self.query_frag)

        if self.module.check_mode:
            if self.module.params.get('table'):
                if self.__check_obj():
                    # if the table or column doesn't exist,
                    # self.__check_obj will fail
                    self.changed = True
            else:
                # If a table hasn't been passed, it means that
                # the database will be vacuumed/analyzed.
                # The database exists if the module is able to connect to it,
                # so we don't need to check it:
                self.changed = True

            self.executed_queries.append(query)
            return None

        if exec_sql(self, query, ddl=True):
            self.changed = True

# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        table=dict(type='str'),
        columns=dict(type='list'),
        analyze=dict(type='bool'),
        analyze_only=dict(type='bool'),
        full=dict(type='bool'),
        freeze=dict(type='bool'),
        disable_page_skipping=dict(type='bool'),
        db=dict(type='str', aliases=['login_db']),
        session_role=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['analyze', 'analyze_only'],
            ['full', 'analyze_only'],
            ['freeze', 'analyze_only'],
            ['disable_page_skipping', 'analyze_only'],
        ]
    )

    # CHECK PARAMETERS:
    #
    # Note: we don't need to check mutually exclusive params here, because they are
    # checked automatically by AnsibleModule (mutually_exclusive=[] list above).
    if module.params.get('columns') and not module.params.get('table'):
        module.fail_json(msg='table param is necessary with columns')

    if module.params.get('columns') and (not module.params.get('analyze') and
                                         not module.params.get('analyze_only')):
        module.fail_json(msg='analyze option must be specified when a column list is provided')

    # Connect to DB and make cursor object:
    # (autocommit=True because VACUUM/ANALYZE cannot run inside a transaction block)
    db_connection = connect_to_db(module, autocommit=True)

    if module.params.get('disable_page_skipping'):
        # Check server version:
        if db_connection.server_version < DISABLE_PAGE_SKIPPING_VER:
            module.warn('DISABLE_PAGE_SKIPPING is supported from PostgreSQL 9.6, skipped')
            module.params['disable_page_skipping'] = ''

    cursor = db_connection.cursor(cursor_factory=DictCursor)

    ##############
    # Create the object and do main job:
    vacuum = Vacuum(module, cursor)

    # Note: parameters are got
    # from module object into data object of Vacuum class.
    # Therefore not need to pass args to the methods below.
    # Note: check mode is implemented inside the methods below
    # by checking passed module.check_mode arg.

    if module.params.get('full'):
        vacuum.do_full_vacuum()

    elif module.params.get('analyze_only'):
        vacuum.do_analyze()

    else:
        # Do common vacuum by default:
        vacuum.do_vacuum()

    # Clean up:
    cursor.close()
    db_connection.close()

    # Return values:
    module.exit_json(
        changed=vacuum.changed,
        queries=vacuum.executed_queries,
    )


if __name__ == '__main__':
    main()
