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
module: postgresql_owner
short_description: Change an owner of PostgreSQL database object
description:
- Change an owner of PostgreSQL database object.
- Also allows to reassign the ownership of database objects owned by a database role to another role.
- For more information about REASSIGN OWNED BY command
  see U(https://www.postgresql.org/docs/current/sql-reassign-owned.html).
version_added: '2.8'

options:
  new_owner:
    description:
    - Role (user/group) to set as an I(obj_name) owner.
    type: str
    required: yes
  obj_name:
    description:
    - Name of a database object to change ownership.
    - Mutually exclusive with I(reassign_owned_by).
    type: str
  obj_type:
    description:
    - Type of a database object.
    - Mutually exclusive with I(reassign_owned_by).
    type: str
    required: yes
    choices: [ database, function, matview, sequence, schema, table, tablespace, view ]
    aliases:
    - type
  reassign_owned_by:
    description:
    - The list of role names. The ownership of all the objects within the current database,
      and of all shared objects (databases, tablespaces), owned by this role(s) will be reassigned to I(owner).
    - Pay attention - it reassignes all objects owned by this role(s) in the I(db)!
    - If role(s) exists, always returns changed True.
    - Cannot reassign ownership of objects that are required by the database system.
    - For more information see U(https://www.postgresql.org/docs/current/sql-reassign-owned.html).
    - Mutually exclusive with C(obj_type).
    type: list
  fail_on_role:
    description:
    - If C(yes), fail when I(reassign_owned_by) role does not exist.
      Otherwise just warn and continue.
    - Mutually exclusive with I(obj_name) and I(obj_type).
    default: yes
    type: bool
  db:
    description:
    - Name of database to connect to.
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
- The default authentication assumes that you are either logging in as or
  sudo'ing to the postgres account on the host.
- To avoid "Peer authentication failed for user postgres" error,
  use postgres user as a I(become_user).
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
# Set owner as alice for function myfunc in database bar by ansible ad-hoc command:
# ansible -m postgresql_owner -a "db=bar new_owner=alice obj_name=myfunc obj_type=function"

- name: The same as above by playbook
  postgresql_owner:
    db: bar
    new_owner: alice
    obj_name: myfunc
    obj_type: function

- name: Set owner as bob for table acme in database bar
  postgresql_owner:
    db: bar
    new_owner: bob
    obj_name: acme
    obj_type: table

- name: Set owner as alice for view test_view in database bar
  postgresql_owner:
    db: bar
    new_owner: alice
    obj_name: test_view
    obj_type: view

- name: Set owner as bob for tablespace ssd in database foo
  postgresql_owner:
    db: foo
    new_owner: bob
    obj_name: ssd
    obj_type: tablespace

- name: Reassign all object in database bar owned by bob to alice
  postgresql_owner:
    db: bar
    new_owner: alice
    reassign_owned_by: bob

- name: Reassign all object in database bar owned by bob and bill to alice
  postgresql_owner:
    db: bar
    new_owner: alice
    reassign_owned_by:
    - bob
    - bill
'''

RETURN = r'''
queries:
  description: List of executed queries.
  returned: always
  type: str
  sample: [ 'REASSIGN OWNED BY "bob" TO "alice"' ]
'''

try:
    from psycopg2.extras import DictCursor
except ImportError:
    # psycopg2 is checked by connect_to_db()
    # from ansible.module_utils.postgres
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import SQLParseError, pg_quote_identifier
from ansible.module_utils.postgres import connect_to_db, get_conn_params, postgres_common_argument_spec
from ansible.module_utils._text import to_native


class PgOwnership(object):
    """
    If you want to add handling of a new type of database objects:
    1. Add a specific method for this like self.__set_db_owner(), etc.
    2. Add a condition with a check of ownership for new type objects to self.__is_owner()
    3. Add a condition with invocation of the specific method to self.set_owner()
    4. Add the information to the module documentation
    That's all.
    """
    def __init__(self, module, cursor, role):
        self.module = module
        self.cursor = cursor
        self.check_role_exists(role)
        self.role = role
        self.changed = False
        self.executed_queries = []
        self.obj_name = ''
        self.obj_type = ''

    def check_role_exists(self, role, fail_on_role=True):
        if not self.__role_exists(role):
            if fail_on_role:
                self.module.fail_json(msg="Role '%s' does not exist" % role)
            else:
                self.module.warn("Role '%s' does not exist, pass" % role)

            return False

        else:
            return True

    def reassign(self, old_owners, fail_on_role):
        roles = []
        for r in old_owners:
            if self.check_role_exists(r, fail_on_role):
                roles.append(pg_quote_identifier(r, 'role'))

        # Roles do not exist, nothing to do, exit:
        if not roles:
            return False

        old_owners = ','.join(roles)

        query = ['REASSIGN OWNED BY']
        query.append(old_owners)
        query.append('TO %s' % pg_quote_identifier(self.role, 'role'))
        query = ' '.join(query)

        self.changed = self.__exec_sql(query, ddl=True)

    def set_owner(self, obj_type, obj_name):
        self.obj_name = obj_name
        self.obj_type = obj_type

        # if a new_owner is the object owner now,
        # nothing to do:
        if self.__is_owner():
            return False

        if obj_type == 'database':
            self.__set_db_owner()

        elif obj_type == 'function':
            self.__set_func_owner()

        elif obj_type == 'sequence':
            self.__set_seq_owner()

        elif obj_type == 'schema':
            self.__set_schema_owner()

        elif obj_type == 'table':
            self.__set_table_owner()

        elif obj_type == 'tablespace':
            self.__set_tablespace_owner()

        elif obj_type == 'view':
            self.__set_view_owner()

        elif obj_type == 'matview':
            self.__set_mat_view_owner()

    def __is_owner(self):
        if self.obj_type == 'table':
            query = ("SELECT 1 FROM pg_tables WHERE tablename = '%s' "
                     "AND tableowner = '%s'" % (self.obj_name, self.role))

        elif self.obj_type == 'database':
            query = ("SELECT 1 FROM pg_database AS d "
                     "JOIN pg_roles AS r ON d.datdba = r.oid "
                     "WHERE d.datname = '%s' "
                     "AND r.rolname = '%s'" % (self.obj_name, self.role))

        elif self.obj_type == 'function':
            query = ("SELECT 1 FROM pg_proc AS f "
                     "JOIN pg_roles AS r ON f.proowner = r.oid "
                     "WHERE f.proname = '%s' "
                     "AND r.rolname = '%s'" % (self.obj_name, self.role))

        elif self.obj_type == 'sequence':
            query = ("SELECT 1 FROM pg_class AS c "
                     "JOIN pg_roles AS r ON c.relowner = r.oid "
                     "WHERE c.relkind = 'S' AND c.relname = '%s' "
                     "AND r.rolname = '%s'" % (self.obj_name, self.role))

        elif self.obj_type == 'schema':
            query = ("SELECT 1 FROM information_schema.schemata "
                     "WHERE schema_name = '%s' "
                     "AND schema_owner = '%s'" % (self.obj_name, self.role))

        elif self.obj_type == 'tablespace':
            query = ("SELECT 1 FROM pg_tablespace AS t "
                     "JOIN pg_roles AS r ON t.spcowner = r.oid "
                     "WHERE t.spcname = '%s' "
                     "AND r.rolname = '%s'" % (self.obj_name, self.role))

        elif self.obj_type == 'view':
            query = ("SELECT 1 FROM pg_views "
                     "WHERE viewname = '%s' "
                     "AND viewowner = '%s'" % (self.obj_name, self.role))

        elif self.obj_type == 'matview':
            query = ("SELECT 1 FROM pg_matviews "
                     "WHERE matviewname = '%s' "
                     "AND matviewowner = '%s'" % (self.obj_name, self.role))

        return self.__exec_sql(query, add_to_executed=False)

    def __set_db_owner(self):
        query = "ALTER DATABASE %s OWNER TO %s" % (pg_quote_identifier(self.obj_name, 'database'),
                                                   pg_quote_identifier(self.role, 'role'))
        self.changed = self.__exec_sql(query, ddl=True)

    def __set_func_owner(self):
        query = "ALTER FUNCTION %s OWNER TO %s" % (self.obj_name,
                                                   pg_quote_identifier(self.role, 'role'))
        self.changed = self.__exec_sql(query, ddl=True)

    def __set_seq_owner(self):
        query = "ALTER SEQUENCE %s OWNER TO %s" % (pg_quote_identifier(self.obj_name, 'table'),
                                                   pg_quote_identifier(self.role, 'role'))
        self.changed = self.__exec_sql(query, ddl=True)

    def __set_schema_owner(self):
        query = "ALTER SCHEMA %s OWNER TO %s" % (pg_quote_identifier(self.obj_name, 'schema'),
                                                 pg_quote_identifier(self.role, 'role'))
        self.changed = self.__exec_sql(query, ddl=True)

    def __set_table_owner(self):
        query = "ALTER TABLE %s OWNER TO %s" % (pg_quote_identifier(self.obj_name, 'table'),
                                                pg_quote_identifier(self.role, 'role'))
        self.changed = self.__exec_sql(query, ddl=True)

    def __set_tablespace_owner(self):
        query = "ALTER TABLESPACE %s OWNER TO %s" % (pg_quote_identifier(self.obj_name, 'database'),
                                                     pg_quote_identifier(self.role, 'role'))
        self.changed = self.__exec_sql(query, ddl=True)

    def __set_view_owner(self):
        query = "ALTER VIEW %s OWNER TO %s" % (pg_quote_identifier(self.obj_name, 'table'),
                                               pg_quote_identifier(self.role, 'role'))
        self.changed = self.__exec_sql(query, ddl=True)

    def __set_mat_view_owner(self):
        query = "ALTER MATERIALIZED VIEW %s OWNER TO %s" % (pg_quote_identifier(self.obj_name, 'table'),
                                                            pg_quote_identifier(self.role, 'role'))
        self.changed = self.__exec_sql(query, ddl=True)

    def __role_exists(self, role):
        return self.__exec_sql("SELECT 1 FROM pg_roles WHERE rolname = '%s'" % role, add_to_executed=False)

    def __exec_sql(self, query, ddl=False, add_to_executed=True):
        try:
            self.cursor.execute(query)

            if add_to_executed:
                self.executed_queries.append(query)

            if not ddl:
                res = self.cursor.fetchall()
                return res
            return True
        except Exception as e:
            self.module.fail_json(msg="Cannot execute SQL '%s': %s" % (query, to_native(e)))
        return False


# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        new_owner=dict(type='str', required=True),
        obj_name=dict(type='str'),
        obj_type=dict(type='str', aliases=['type'], choices=[
            'database', 'function', 'matview', 'sequence', 'schema', 'table', 'tablespace', 'view']),
        reassign_owned_by=dict(type='list'),
        fail_on_role=dict(type='bool', default=True),
        db=dict(type='str', aliases=['login_db']),
        session_role=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['obj_name', 'reassign_owned_by'],
            ['obj_type', 'reassign_owned_by'],
            ['obj_name', 'fail_on_role'],
            ['obj_type', 'fail_on_role'],
        ],
        supports_check_mode=True,
    )

    new_owner = module.params['new_owner']
    obj_name = module.params['obj_name']
    obj_type = module.params['obj_type']
    reassign_owned_by = module.params['reassign_owned_by']
    fail_on_role = module.params['fail_on_role']

    conn_params = get_conn_params(module, module.params)
    db_connection = connect_to_db(module, conn_params, autocommit=False)
    cursor = db_connection.cursor(cursor_factory=DictCursor)

    ##############
    # Create the object and do main job:
    pg_ownership = PgOwnership(module, cursor, new_owner)

    # if we want to change ownership:
    if obj_name:
        pg_ownership.set_owner(obj_type, obj_name)

    # if we want to reassign objects owned by roles:
    elif reassign_owned_by:
        pg_ownership.reassign(reassign_owned_by, fail_on_role)

    # Rollback if it's possible and check_mode:
    if module.check_mode:
        db_connection.rollback()
    else:
        db_connection.commit()

    cursor.close()
    db_connection.close()

    module.exit_json(
        changed=pg_ownership.changed,
        queries=pg_ownership.executed_queries,
    )


if __name__ == '__main__':
    main()
