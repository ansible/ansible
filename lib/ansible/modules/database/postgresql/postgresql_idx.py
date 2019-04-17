#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Andrey Klychkov (@Andersson007) <aaklychkov@mail.ru>
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
module: postgresql_idx
short_description: Create or drop indexes from a PostgreSQL database
description:
- Create or drop indexes from a PostgreSQL database.
- For more information see U(https://www.postgresql.org/docs/current/sql-createindex.html),
  U(https://www.postgresql.org/docs/current/sql-dropindex.html).
version_added: '2.8'

options:
  idxname:
    description:
    - Name of the index to create or drop.
    type: str
    required: true
    aliases:
    - name
  db:
    description:
    - Name of database to connect to and where the index will be created/dropped.
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
  schema:
    description:
    - Name of a database schema where the index will be created.
    type: str
  state:
    description:
    - Index state.
    - I(state=present) implies the index will be created if it does not exist.
    - I(state=absent) implies the index will be dropped if it exists.
    type: str
    default: present
    choices: [ absent, present ]
  table:
    description:
    - Table to create index on it.
    - Mutually exclusive with I(state=absent).
    type: str
    required: true
  columns:
    description:
    - List of index columns that need to be covered by index.
    - Mutually exclusive with I(state=absent).
    type: list
    aliases:
    - column
  cond:
    description:
    - Index conditions.
    - Mutually exclusive with I(state=absent).
    type: str
  idxtype:
    description:
    - Index type (like btree, gist, gin, etc.).
    - Mutually exclusive with I(state=absent).
    type: str
    aliases:
    - type
  concurrent:
    description:
    - Enable or disable concurrent mode (CREATE / DROP INDEX CONCURRENTLY).
    - Pay attention, if I(concurrent=no), the table will be locked (ACCESS EXCLUSIVE) during the building process.
      For more information about the lock levels see U(https://www.postgresql.org/docs/current/explicit-locking.html).
    - If the building process was interrupted for any reason when I(cuncurrent=yes), the index becomes invalid.
      In this case it should be dropped and created again.
    - Mutually exclusive with I(cascade=yes).
    type: bool
    default: yes
  tablespace:
    description:
    - Set a tablespace for the index.
    - Mutually exclusive with I(state=absent).
    required: false
    type: str
  storage_params:
    description:
    - Storage parameters like fillfactor, vacuum_cleanup_index_scale_factor, etc.
    - Mutually exclusive with I(state=absent).
    type: list
  cascade:
    description:
    - Automatically drop objects that depend on the index,
      and in turn all objects that depend on those objects U(https://www.postgresql.org/docs/current/sql-dropindex.html).
    - It used only with I(state=absent).
    - Mutually exclusive with I(concurrent=yes)
    type: bool
    default: no

notes:
- The index building process can affect database performance.
- To avoid table locks on production databases, use I(concurrent=yes) (default behavior).
- The default authentication assumes that you are either logging in as or
  sudo'ing to the postgres account on the host.
- This module uses psycopg2, a Python PostgreSQL database adapter. You must
  ensure that psycopg2 is installed on the host before using this module.
- If the remote host is the PostgreSQL server (which is the default case), then
  PostgreSQL must also be installed on the remote host.
- For Ubuntu-based systems, install the postgresql, libpq-dev, and python-psycopg2 packages
  on the remote host before using this module.

requirements:
- psycopg2

author:
- Andrew Klychkov (@Andersson007)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Create btree index if not exists test_idx concurrently covering columns id and name of table products
  postgresql_idx:
    db: acme
    table: products
    columns: id,name
    name: test_idx

- name: Create btree index test_idx concurrently with tablespace called ssd and storage parameter
  postgresql_idx:
    db: acme
    table: products
    columns:
    - id
    - name
    idxname: test_idx
    tablespace: ssd
    storage_params:
    - fillfactor=90

- name: Create gist index test_gist_idx concurrently on column geo_data of table map
  postgresql_idx:
    db: somedb
    table: map
    idxtype: gist
    columns: geo_data
    idxname: test_gist_idx

# Note: for the example below pg_trgm extension must be installed for gin_trgm_ops
- name: Create gin index gin0_idx not concurrently on column comment of table test
  postgresql_idx:
    idxname: gin0_idx
    table: test
    columns: comment gin_trgm_ops
    concurrent: no
    idxtype: gin

- name: Drop btree test_idx concurrently
  postgresql_idx:
    db: mydb
    idxname: test_idx
    state: absent

- name: Drop test_idx cascade
  postgresql_idx:
    db: mydb
    idxname: test_idx
    state: absent
    cascade: yes
    concurrent: no

- name: Create btree index test_idx concurrently on columns id,comment where column id > 1
  postgresql_idx:
    db: mydb
    table: test
    columns: id,comment
    idxname: test_idx
    cond: id > 1
'''

RETURN = r'''
name:
  description: Index name.
  returned: always
  type: str
  sample: 'foo_idx'
state:
  description: Index state.
  returned: always
  type: str
  sample: 'present'
schema:
  description: Schema where index exists.
  returned: always
  type: str
  sample: 'public'
tablespace:
  description: Tablespace where index exists.
  returned: always
  type: str
  sample: 'ssd'
query:
  description: Query that was tried to be executed.
  returned: always
  type: str
  sample: 'CREATE INDEX CONCURRENTLY foo_idx ON test_table USING BTREE (id)'
storage_params:
  description: Index storage parameters.
  returned: always
  type: list
  sample: [ "fillfactor=90" ]
valid:
  description: Index validity.
  returned: always
  type: bool
  sample: true
'''

import traceback

PSYCOPG2_IMP_ERR = None
try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    PSYCOPG2_IMP_ERR = traceback.format_exc()

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.database import SQLParseError
from ansible.module_utils.postgres import postgres_common_argument_spec
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems


VALID_IDX_TYPES = ('BTREE', 'HASH', 'GIST', 'SPGIST', 'GIN', 'BRIN')


# ===========================================
# PostgreSQL module specific support methods.
#

class Index(object):
    def __init__(self, module, cursor, schema, name):
        self.name = name
        if schema:
            self.schema = schema
        else:
            self.schema = 'public'
        self.module = module
        self.cursor = cursor
        self.info = {
            'name': self.name,
            'state': 'absent',
            'schema': '',
            'tblname': '',
            'tblspace': '',
            'valid': True,
            'storage_params': [],
        }
        self.exists = False
        self.__exists_in_db()
        self.executed_query = ''

    def get_info(self):
        """
        Getter to refresh and return table info
        """
        self.__exists_in_db()
        return self.info

    def __exists_in_db(self):
        """
        Check index and collect info
        """
        query = ("SELECT i.schemaname, i.tablename, i.tablespace, "
                 "pi.indisvalid, c.reloptions "
                 "FROM pg_catalog.pg_indexes AS i "
                 "JOIN pg_catalog.pg_class AS c "
                 "ON i.indexname = c.relname "
                 "JOIN pg_catalog.pg_index AS pi "
                 "ON c.oid = pi.indexrelid "
                 "WHERE i.indexname = '%s'" % self.name)

        res = self.__exec_sql(query)
        if res:
            self.exists = True
            self.info = dict(
                name=self.name,
                state='present',
                schema=res[0][0],
                tblname=res[0][1],
                tblspace=res[0][2] if res[0][2] else '',
                valid=res[0][3],
                storage_params=res[0][4] if res[0][4] else [],
            )
            return True

        else:
            self.exists = False
            return False

    def create(self, tblname, idxtype, columns, cond, tblspace, storage_params, concurrent=True):
        """
        Create PostgreSQL index.
        """
        # To change existing index we should write
        # 'postgresql_alter_table' standalone module.

        if self.exists:
            return False

        changed = False
        if idxtype is None:
            idxtype = "BTREE"

        query = 'CREATE INDEX'

        if concurrent:
            query += ' CONCURRENTLY'

        query += ' %s' % self.name

        if self.schema:
            query += ' ON %s.%s ' % (self.schema, tblname)
        else:
            query += 'public.%s ' % tblname

        query += 'USING %s (%s)' % (idxtype, columns)

        if storage_params:
            query += ' WITH (%s)' % storage_params

        if tblspace:
            query += ' TABLESPACE %s' % tblspace

        if cond:
            query += ' WHERE %s' % cond

        self.executed_query = query

        if self.__exec_sql(query, ddl=True):
            return True

        return False

    def drop(self, schema, cascade=False, concurrent=True):
        """
        Drop PostgreSQL index.
        """

        changed = False
        if not self.exists:
            return False

        query = 'DROP INDEX'

        if concurrent:
            query += ' CONCURRENTLY'

        if not schema:
            query += ' public.%s' % self.name
        else:
            query += ' %s.%s' % (schema, self.name)

        if cascade:
            query += ' CASCADE'

        self.executed_query = query

        if self.__exec_sql(query, ddl=True):
            return True

        return False

    def __exec_sql(self, query, ddl=False):
        try:
            self.cursor.execute(query)
            if not ddl:
                res = self.cursor.fetchall()
                return res
            return True
        except SQLParseError as e:
            self.module.fail_json(msg=to_native(e))
        except Exception as e:
            self.module.fail_json(msg="Cannot execute SQL '%s': %s" % (query, to_native(e)))

        return False


# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        idxname=dict(type='str', required=True, aliases=['name']),
        db=dict(type='str', aliases=['login_db']),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        concurrent=dict(type='bool', default=True),
        table=dict(type='str'),
        idxtype=dict(type='str', aliases=['type']),
        columns=dict(type='list', aliases=['column']),
        cond=dict(type='str'),
        session_role=dict(type='str'),
        tablespace=dict(type='str'),
        storage_params=dict(type='list'),
        cascade=dict(type='bool', default=False),
        schema=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg=missing_required_lib('psycopg2'), exception=PSYCOPG2_IMP_ERR)

    idxname = module.params["idxname"]
    state = module.params["state"]
    concurrent = module.params["concurrent"]
    table = module.params["table"]
    idxtype = module.params["idxtype"]
    columns = module.params["columns"]
    cond = module.params["cond"]
    sslrootcert = module.params["ca_cert"]
    session_role = module.params["session_role"]
    tablespace = module.params["tablespace"]
    storage_params = module.params["storage_params"]
    cascade = module.params["cascade"]
    schema = module.params["schema"]

    if concurrent and cascade:
        module.fail_json(msg="Cuncurrent mode and cascade parameters are mutually exclusive")

    if state == 'present':
        if not table:
            module.fail_json(msg="Table must be specified")
        if not columns:
            module.fail_json(msg="At least one column must be specified")
    else:
        if table or columns or cond or idxtype or tablespace:
            module.fail_json(msg="Index %s is going to be removed, so it does not "
                                 "make sense to pass a table name, columns, conditions, "
                                 "index type, or tablespace" % idxname)

    if cascade and state != 'absent':
        module.fail_json(msg="cascade parameter used only with state=absent")

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

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] is None or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    if psycopg2.__version__ < '2.4.3' and sslrootcert is not None:
        module.fail_json(msg='psycopg2 must be at least 2.4.3 in order to user the ca_cert parameter')

    try:
        db_connection = psycopg2.connect(**kw)
        if concurrent:
            if psycopg2.__version__ >= '2.4.2':
                db_connection.set_session(autocommit=True)
            else:
                db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least version 8.4 to support sslrootcert')

        module.fail_json(msg="Unable to connect to database: %s" % to_native(e))
    except Exception as e:
        module.fail_json(msg="Unable to connect to database: %s" % to_native(e))

    if session_role:
        try:
            cursor.execute('SET ROLE %s' % session_role)
        except Exception as e:
            module.fail_json(msg="Could not switch role: %s" % to_native(e))

    # Set defaults:
    changed = False

    # Do job:
    index = Index(module, cursor, schema, idxname)
    kw = index.get_info()
    kw['query'] = ''

    #
    # check_mode start
    if module.check_mode:
        if state == 'present' and index.exists:
            kw['changed'] = False
            module.exit_json(**kw)

        elif state == 'present' and not index.exists:
            kw['changed'] = True
            module.exit_json(**kw)

        elif state == 'absent' and not index.exists:
            kw['changed'] = False
            module.exit_json(**kw)

        elif state == 'absent' and index.exists:
            kw['changed'] = True
            module.exit_json(**kw)
    # check_mode end
    #

    if state == "present":
        if idxtype and idxtype.upper() not in VALID_IDX_TYPES:
            module.fail_json(msg="Index type '%s' of %s is not in valid types" % (idxtype, idxname))

        columns = ','.join(columns)

        if storage_params:
            storage_params = ','.join(storage_params)

        changed = index.create(table, idxtype, columns, cond, tablespace, storage_params, concurrent)

        if changed:
            kw = index.get_info()
            kw['state'] = 'present'
            kw['query'] = index.executed_query

    else:
        changed = index.drop(schema, cascade, concurrent)

        if changed:
            kw['state'] = 'absent'
            kw['query'] = index.executed_query

    if not kw['valid']:
        db_connection.rollback()
        module.warn("Index %s is invalid! ROLLBACK" % idxname)

    if not concurrent:
        db_connection.commit()

    kw['changed'] = changed
    module.exit_json(**kw)


if __name__ == '__main__':
    main()
