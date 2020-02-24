#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: postgresql_table
short_description: Create, drop, or modify a PostgreSQL table
description:
- Allows to create, drop, rename, truncate a table, or change some table attributes.
version_added: '2.8'
options:
  table:
    description:
    - Table name.
    required: true
    aliases:
    - name
    type: str
  state:
    description:
    - The table state. I(state=absent) is mutually exclusive with I(tablespace), I(owner), I(unlogged),
      I(like), I(including), I(columns), I(truncate), I(storage_params) and, I(rename).
    type: str
    default: present
    choices: [ absent, present ]
  tablespace:
    description:
    - Set a tablespace for the table.
    required: false
    type: str
  owner:
    description:
    - Set a table owner.
    type: str
  unlogged:
    description:
    - Create an unlogged table.
    type: bool
    default: no
  like:
    description:
    - Create a table like another table (with similar DDL).
      Mutually exclusive with I(columns), I(rename), and I(truncate).
    type: str
  including:
    description:
    - Keywords that are used with like parameter, may be DEFAULTS, CONSTRAINTS, INDEXES, STORAGE, COMMENTS or ALL.
      Needs I(like) specified. Mutually exclusive with I(columns), I(rename), and I(truncate).
    type: str
  columns:
    description:
    - Columns that are needed.
    type: list
    elements: str
  rename:
    description:
    - New table name. Mutually exclusive with I(tablespace), I(owner),
      I(unlogged), I(like), I(including), I(columns), I(truncate), and I(storage_params).
    type: str
  truncate:
    description:
    - Truncate a table. Mutually exclusive with I(tablespace), I(owner), I(unlogged),
      I(like), I(including), I(columns), I(rename), and I(storage_params).
    type: bool
    default: no
  storage_params:
    description:
    - Storage parameters like fillfactor, autovacuum_vacuum_treshold, etc.
      Mutually exclusive with I(rename) and I(truncate).
    type: list
    elements: str
  db:
    description:
    - Name of database to connect and where the table will be created.
    type: str
    aliases:
    - login_db
  session_role:
    description:
    - Switch to session_role after connecting.
      The specified session_role must be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though
      the session_role were the one that had logged in originally.
    type: str
  cascade:
    description:
    - Automatically drop objects that depend on the table (such as views).
      Used with I(state=absent) only.
    type: bool
    default: no
    version_added: '2.9'
notes:
- If you do not pass db parameter, tables will be created in the database
  named postgres.
- PostgreSQL allows to create columnless table, so columns param is optional.
- Unlogged tables are available from PostgreSQL server version 9.1.
seealso:
- module: postgresql_sequence
- module: postgresql_idx
- module: postgresql_info
- module: postgresql_tablespace
- module: postgresql_owner
- module: postgresql_privs
- module: postgresql_copy
- name: CREATE TABLE reference
  description: Complete reference of the CREATE TABLE command documentation.
  link: https://www.postgresql.org/docs/current/sql-createtable.html
- name: ALTER TABLE reference
  description: Complete reference of the ALTER TABLE  command documentation.
  link: https://www.postgresql.org/docs/current/sql-altertable.html
- name: DROP TABLE reference
  description: Complete reference of the DROP TABLE command documentation.
  link: https://www.postgresql.org/docs/current/sql-droptable.html
- name: PostgreSQL data types
  description: Complete reference of the PostgreSQL data types documentation.
  link: https://www.postgresql.org/docs/current/datatype.html
author:
- Andrei Klychkov (@Andersson007)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Create tbl2 in the acme database with the DDL like tbl1 with testuser as an owner
  postgresql_table:
    db: acme
    name: tbl2
    like: tbl1
    owner: testuser

- name: Create tbl2 in the acme database and tablespace ssd with the DDL like tbl1 including comments and indexes
  postgresql_table:
    db: acme
    table: tbl2
    like: tbl1
    including: comments, indexes
    tablespace: ssd

- name: Create test_table with several columns in ssd tablespace with fillfactor=10 and autovacuum_analyze_threshold=1
  postgresql_table:
    name: test_table
    columns:
    - id bigserial primary key
    - num bigint
    - stories text
    tablespace: ssd
    storage_params:
    - fillfactor=10
    - autovacuum_analyze_threshold=1

- name: Create an unlogged table in schema acme
  postgresql_table:
    name: acme.useless_data
    columns: waste_id int
    unlogged: true

- name: Rename table foo to bar
  postgresql_table:
    table: foo
    rename: bar

- name: Rename table foo from schema acme to bar
  postgresql_table:
    name: acme.foo
    rename: bar

- name: Set owner to someuser
  postgresql_table:
    name: foo
    owner: someuser

- name: Change tablespace of foo table to new_tablespace and set owner to new_user
  postgresql_table:
    name: foo
    tablespace: new_tablespace
    owner: new_user

- name: Truncate table foo
  postgresql_table:
    name: foo
    truncate: yes

- name: Drop table foo from schema acme
  postgresql_table:
    name: acme.foo
    state: absent

- name: Drop table bar cascade
  postgresql_table:
    name: bar
    state: absent
    cascade: yes
'''

RETURN = r'''
table:
  description: Name of a table.
  returned: always
  type: str
  sample: 'foo'
state:
  description: Table state.
  returned: always
  type: str
  sample: 'present'
owner:
  description: Table owner.
  returned: always
  type: str
  sample: 'postgres'
tablespace:
  description: Tablespace.
  returned: always
  type: str
  sample: 'ssd_tablespace'
queries:
  description: List of executed queries.
  returned: always
  type: str
  sample: [ 'CREATE TABLE "test_table" (id bigint)' ]
storage_params:
  description: Storage parameters.
  returned: always
  type: list
  sample: [ "fillfactor=100", "autovacuum_analyze_threshold=1" ]
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


# ===========================================
# PostgreSQL module specific support methods.
#

class Table(object):
    def __init__(self, name, module, cursor):
        self.name = name
        self.module = module
        self.cursor = cursor
        self.info = {
            'owner': '',
            'tblspace': '',
            'storage_params': [],
        }
        self.exists = False
        self.__exists_in_db()
        self.executed_queries = []

    def get_info(self):
        """Getter to refresh and get table info"""
        self.__exists_in_db()

    def __exists_in_db(self):
        """Check table exists and refresh info"""
        if "." in self.name:
            schema = self.name.split('.')[-2]
            tblname = self.name.split('.')[-1]
        else:
            schema = 'public'
            tblname = self.name

        query = ("SELECT t.tableowner, t.tablespace, c.reloptions "
                 "FROM pg_tables AS t "
                 "INNER JOIN pg_class AS c ON  c.relname = t.tablename "
                 "INNER JOIN pg_namespace AS n ON c.relnamespace = n.oid "
                 "WHERE t.tablename = %(tblname)s "
                 "AND n.nspname = %(schema)s")
        res = exec_sql(self, query, query_params={'tblname': tblname, 'schema': schema},
                       add_to_executed=False)
        if res:
            self.exists = True
            self.info = dict(
                owner=res[0][0],
                tblspace=res[0][1] if res[0][1] else '',
                storage_params=res[0][2] if res[0][2] else [],
            )

            return True
        else:
            self.exists = False
            return False

    def create(self, columns='', params='', tblspace='',
               unlogged=False, owner=''):
        """
        Create table.
        If table exists, check passed args (params, tblspace, owner) and,
        if they're different from current, change them.
        Arguments:
        params - storage params (passed by "WITH (...)" in SQL),
            comma separated.
        tblspace - tablespace.
        owner - table owner.
        unlogged - create unlogged table.
        columns - column string (comma separated).
        """
        name = pg_quote_identifier(self.name, 'table')

        changed = False

        if self.exists:
            if tblspace == 'pg_default' and self.info['tblspace'] is None:
                pass  # Because they have the same meaning
            elif tblspace and self.info['tblspace'] != tblspace:
                self.set_tblspace(tblspace)
                changed = True

            if owner and self.info['owner'] != owner:
                self.set_owner(owner)
                changed = True

            if params:
                param_list = [p.strip(' ') for p in params.split(',')]

                new_param = False
                for p in param_list:
                    if p not in self.info['storage_params']:
                        new_param = True

                if new_param:
                    self.set_stor_params(params)
                    changed = True

            if changed:
                return True
            return False

        query = "CREATE"
        if unlogged:
            query += " UNLOGGED TABLE %s" % name
        else:
            query += " TABLE %s" % name

        if columns:
            query += " (%s)" % columns
        else:
            query += " ()"

        if params:
            query += " WITH (%s)" % params

        if tblspace:
            query += " TABLESPACE %s" % pg_quote_identifier(tblspace, 'database')

        if exec_sql(self, query, ddl=True):
            changed = True

        if owner:
            changed = self.set_owner(owner)

        return changed

    def create_like(self, src_table, including='', tblspace='',
                    unlogged=False, params='', owner=''):
        """
        Create table like another table (with similar DDL).
        Arguments:
        src_table - source table.
        including - corresponds to optional INCLUDING expression
            in CREATE TABLE ... LIKE statement.
        params - storage params (passed by "WITH (...)" in SQL),
            comma separated.
        tblspace - tablespace.
        owner - table owner.
        unlogged - create unlogged table.
        """
        changed = False

        name = pg_quote_identifier(self.name, 'table')

        query = "CREATE"
        if unlogged:
            query += " UNLOGGED TABLE %s" % name
        else:
            query += " TABLE %s" % name

        query += " (LIKE %s" % pg_quote_identifier(src_table, 'table')

        if including:
            including = including.split(',')
            for i in including:
                query += " INCLUDING %s" % i

        query += ')'

        if params:
            query += " WITH (%s)" % params

        if tblspace:
            query += " TABLESPACE %s" % pg_quote_identifier(tblspace, 'database')

        if exec_sql(self, query, ddl=True):
            changed = True

        if owner:
            changed = self.set_owner(owner)

        return changed

    def truncate(self):
        query = "TRUNCATE TABLE %s" % pg_quote_identifier(self.name, 'table')
        return exec_sql(self, query, ddl=True)

    def rename(self, newname):
        query = "ALTER TABLE %s RENAME TO %s" % (pg_quote_identifier(self.name, 'table'),
                                                 pg_quote_identifier(newname, 'table'))
        return exec_sql(self, query, ddl=True)

    def set_owner(self, username):
        query = "ALTER TABLE %s OWNER TO %s" % (pg_quote_identifier(self.name, 'table'),
                                                pg_quote_identifier(username, 'role'))
        return exec_sql(self, query, ddl=True)

    def drop(self, cascade=False):
        if not self.exists:
            return False

        query = "DROP TABLE %s" % pg_quote_identifier(self.name, 'table')
        if cascade:
            query += " CASCADE"
        return exec_sql(self, query, ddl=True)

    def set_tblspace(self, tblspace):
        query = "ALTER TABLE %s SET TABLESPACE %s" % (pg_quote_identifier(self.name, 'table'),
                                                      pg_quote_identifier(tblspace, 'database'))
        return exec_sql(self, query, ddl=True)

    def set_stor_params(self, params):
        query = "ALTER TABLE %s SET (%s)" % (pg_quote_identifier(self.name, 'table'), params)
        return exec_sql(self, query, ddl=True)


# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        table=dict(type='str', required=True, aliases=['name']),
        state=dict(type='str', default="present", choices=["absent", "present"]),
        db=dict(type='str', default='', aliases=['login_db']),
        tablespace=dict(type='str'),
        owner=dict(type='str'),
        unlogged=dict(type='bool', default=False),
        like=dict(type='str'),
        including=dict(type='str'),
        rename=dict(type='str'),
        truncate=dict(type='bool', default=False),
        columns=dict(type='list', elements='str'),
        storage_params=dict(type='list', elements='str'),
        session_role=dict(type='str'),
        cascade=dict(type='bool', default=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    table = module.params["table"]
    state = module.params["state"]
    tablespace = module.params["tablespace"]
    owner = module.params["owner"]
    unlogged = module.params["unlogged"]
    like = module.params["like"]
    including = module.params["including"]
    newname = module.params["rename"]
    storage_params = module.params["storage_params"]
    truncate = module.params["truncate"]
    columns = module.params["columns"]
    cascade = module.params["cascade"]

    if state == 'present' and cascade:
        module.warn("cascade=true is ignored when state=present")

    # Check mutual exclusive parameters:
    if state == 'absent' and (truncate or newname or columns or tablespace or like or storage_params or unlogged or owner or including):
        module.fail_json(msg="%s: state=absent is mutually exclusive with: "
                             "truncate, rename, columns, tablespace, "
                             "including, like, storage_params, unlogged, owner" % table)

    if truncate and (newname or columns or like or unlogged or storage_params or owner or tablespace or including):
        module.fail_json(msg="%s: truncate is mutually exclusive with: "
                             "rename, columns, like, unlogged, including, "
                             "storage_params, owner, tablespace" % table)

    if newname and (columns or like or unlogged or storage_params or owner or tablespace or including):
        module.fail_json(msg="%s: rename is mutually exclusive with: "
                             "columns, like, unlogged, including, "
                             "storage_params, owner, tablespace" % table)

    if like and columns:
        module.fail_json(msg="%s: like and columns params are mutually exclusive" % table)
    if including and not like:
        module.fail_json(msg="%s: including param needs like param specified" % table)

    conn_params = get_conn_params(module, module.params)
    db_connection = connect_to_db(module, conn_params, autocommit=False)
    cursor = db_connection.cursor(cursor_factory=DictCursor)

    if storage_params:
        storage_params = ','.join(storage_params)

    if columns:
        columns = ','.join(columns)

    ##############
    # Do main job:
    table_obj = Table(table, module, cursor)

    # Set default returned values:
    changed = False
    kw = {}
    kw['table'] = table
    kw['state'] = ''
    if table_obj.exists:
        kw = dict(
            table=table,
            state='present',
            owner=table_obj.info['owner'],
            tablespace=table_obj.info['tblspace'],
            storage_params=table_obj.info['storage_params'],
        )

    if state == 'absent':
        changed = table_obj.drop(cascade=cascade)

    elif truncate:
        changed = table_obj.truncate()

    elif newname:
        changed = table_obj.rename(newname)
        q = table_obj.executed_queries
        table_obj = Table(newname, module, cursor)
        table_obj.executed_queries = q

    elif state == 'present' and not like:
        changed = table_obj.create(columns, storage_params,
                                   tablespace, unlogged, owner)

    elif state == 'present' and like:
        changed = table_obj.create_like(like, including, tablespace,
                                        unlogged, storage_params)

    if changed:
        if module.check_mode:
            db_connection.rollback()
        else:
            db_connection.commit()

        # Refresh table info for RETURN.
        # Note, if table has been renamed, it gets info by newname:
        table_obj.get_info()
        db_connection.commit()
        if table_obj.exists:
            kw = dict(
                table=table,
                state='present',
                owner=table_obj.info['owner'],
                tablespace=table_obj.info['tblspace'],
                storage_params=table_obj.info['storage_params'],
            )
        else:
            # We just change the table state here
            # to keep other information about the dropped table:
            kw['state'] = 'absent'

    kw['queries'] = table_obj.executed_queries
    kw['changed'] = changed
    db_connection.close()
    module.exit_json(**kw)


if __name__ == '__main__':
    main()
