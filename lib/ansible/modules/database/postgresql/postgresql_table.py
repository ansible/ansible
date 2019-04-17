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
- Allows to create, drop, rename, truncate a table, or change some table attributes
  U(https://www.postgresql.org/docs/current/sql-createtable.html).
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
notes:
- If you do not pass db parameter, tables will be created in the database
  named postgres.
- PostgreSQL allows to create columnless table, so columns param is optional.
- The default authentication assumes that you are either logging in as or
  sudo'ing to the postgres account on the host.
- To avoid "Peer authentication failed for user postgres" error,
  use postgres user as a I(become_user).
- Unlogged tables are available from PostgreSQL server version 9.1
  U(https://www.postgresql.org/docs/9.1/sql-createtable.html).
- This module uses psycopg2, a Python PostgreSQL database adapter. You must
  ensure that psycopg2 is installed on the host before using this module.
- If the remote host is the PostgreSQL server (which is the default case), then
  PostgreSQL must also be installed on the remote host. For Ubuntu-based
  systems, install the postgresql, libpq-dev, and python-psycopg2 packages
  on the remote host before using this module.
requirements: [ psycopg2 ]
author:
- Andrew Klychkov (@Andersson007)
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

- name: Create an unlogged table
  postgresql_table:
    name: useless_data
    columns: waste_id int
    unlogged: true

- name: Rename table foo to bar
  postgresql_table:
    table: foo
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

- name: Drop table foo
  postgresql_table:
    name: foo
    state: absent
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
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.database import SQLParseError, pg_quote_identifier
from ansible.module_utils.postgres import postgres_common_argument_spec
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems


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
        query = ("SELECT t.tableowner, t.tablespace, c.reloptions "
                 "FROM pg_tables AS t "
                 "INNER JOIN pg_class AS c ON  c.relname = t.tablename "
                 "INNER JOIN pg_namespace AS n ON c.relnamespace = n.oid "
                 "WHERE t.tablename = '%s' "
                 "AND n.nspname = 'public'" % self.name)
        res = self.__exec_sql(query)
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

        if self.__exec_sql(query, ddl=True):
            self.executed_queries.append(query)
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

        if self.__exec_sql(query, ddl=True):
            self.executed_queries.append(query)
            changed = True

        if owner:
            changed = self.set_owner(owner)

        return changed

    def truncate(self):
        query = "TRUNCATE TABLE %s" % pg_quote_identifier(self.name, 'table')
        self.executed_queries.append(query)
        return self.__exec_sql(query, ddl=True)

    def rename(self, newname):
        query = "ALTER TABLE %s RENAME TO %s" % (pg_quote_identifier(self.name, 'table'),
                                                 pg_quote_identifier(newname, 'table'))
        self.executed_queries.append(query)
        return self.__exec_sql(query, ddl=True)

    def set_owner(self, username):
        query = "ALTER TABLE %s OWNER TO %s" % (pg_quote_identifier(self.name, 'table'),
                                                pg_quote_identifier(username, 'role'))
        self.executed_queries.append(query)
        return self.__exec_sql(query, ddl=True)

    def drop(self):
        query = "DROP TABLE %s" % pg_quote_identifier(self.name, 'table')
        self.executed_queries.append(query)
        return self.__exec_sql(query, ddl=True)

    def set_tblspace(self, tblspace):
        query = "ALTER TABLE %s SET TABLESPACE %s" % (pg_quote_identifier(self.name, 'table'),
                                                      pg_quote_identifier(tblspace, 'database'))
        self.executed_queries.append(query)
        return self.__exec_sql(query, ddl=True)

    def set_stor_params(self, params):
        query = "ALTER TABLE %s SET (%s)" % (pg_quote_identifier(self.name, 'table'), params)
        self.executed_queries.append(query)
        return self.__exec_sql(query, ddl=True)

    def __exec_sql(self, query, ddl=False):
        try:
            self.cursor.execute(query)
            if not ddl:
                res = self.cursor.fetchall()
                return res
            return True
        except SQLParseError as e:
            self.module.fail_json(msg=to_native(e))
        except psycopg2.ProgrammingError as e:
            self.module.fail_json(msg="Cannot execute SQL '%s': %s" % (query, to_native(e)))
        return False


# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        table=dict(type='str', required=True, aliases=['name']),
        state=dict(type='str', default="present", choices=["absent", "present"]),
        db=dict(type='str', default='', aliases=['login_db']),
        port=dict(type='int', default=5432, aliases=['login_port']),
        ssl_mode=dict(type='str', default='prefer', choices=['allow', 'disable', 'prefer', 'require', 'verify-ca', 'verify-full']),
        ca_cert=dict(type='str', aliases=['ssl_rootcert']),
        tablespace=dict(type='str'),
        owner=dict(type='str'),
        unlogged=dict(type='bool'),
        like=dict(type='str'),
        including=dict(type='str'),
        rename=dict(type='str'),
        truncate=dict(type='bool'),
        columns=dict(type='list'),
        storage_params=dict(type='list'),
        session_role=dict(type='str'),
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
    sslrootcert = module.params["ca_cert"]
    session_role = module.params["session_role"]

    # Check mutual exclusive parameters:
    if state == 'absent' and (truncate or newname or columns or tablespace or
                              like or storage_params or unlogged or
                              owner or including):
        module.fail_json(msg="%s: state=absent is mutually exclusive with: "
                             "truncate, rename, columns, tablespace, "
                             "including, like, storage_params, unlogged, owner" % table)

    if truncate and (newname or columns or like or unlogged or
                     storage_params or owner or tablespace or including):
        module.fail_json(msg="%s: truncate is mutually exclusive with: "
                             "rename, columns, like, unlogged, including, "
                             "storage_params, owner, tablespace" % table)

    if newname and (columns or like or unlogged or
                    storage_params or owner or tablespace or including):
        module.fail_json(msg="%s: rename is mutually exclusive with: "
                             "columns, like, unlogged, including, "
                             "storage_params, owner, tablespace" % table)

    if like and columns:
        module.fail_json(msg="%s: like and columns params are mutually exclusive" % table)
    if including and not like:
        module.fail_json(msg="%s: including param needs like param specified" % table)

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
        "ca_cert": "sslrootcert"
    }
    kw = dict((params_map[k], v) for (k, v) in iteritems(module.params)
              if k in params_map and v != "" and v is not None)

    if not HAS_PSYCOPG2:
        module.fail_json(msg=missing_required_lib("psycopg2"))

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] is None or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    if psycopg2.__version__ < '2.4.3' and sslrootcert is not None:
        module.fail_json(msg='psycopg2 must be at least 2.4.3 in order to user the ca_cert parameter')

    try:
        db_connection = psycopg2.connect(**kw)
        cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least version 8.4 to support sslrootcert')
        module.fail_json(msg="unable to connect to database: %s" % to_native(e))
    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e))

    if session_role:
        try:
            cursor.execute('SET ROLE %s' % session_role)
        except Exception as e:
            module.fail_json(msg="Could not switch role: %s" % to_native(e))

    if storage_params:
        storage_params = ','.join(storage_params)

    if columns:
        columns = ','.join(columns)

    ##############
    # Do main job:
    table_obj = Table(table, module, cursor)

    # Set default returned values:
    changed = False
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
        changed = table_obj.drop()

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
