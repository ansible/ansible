#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: postgresql_privs
version_added: "1.2"
short_description: Grant or revoke privileges on PostgreSQL database objects.
description:
  - Grant or revoke privileges on PostgreSQL database objects.
  - This module is basically a wrapper around most of the functionality of
    PostgreSQL's GRANT and REVOKE statements with detection of changes
    (GRANT/REVOKE I(privs) ON I(type) I(objs) TO/FROM I(roles))
options:
  database:
    description:
      - Name of database to connect to.
      - 'Alias: I(db)'
    required: yes
  state:
    description:
      - If C(present), the specified privileges are granted, if C(absent) they
        are revoked.
    default: present
    choices: [present, absent]
  privs:
    description:
      - Comma separated list of privileges to grant/revoke.
      - 'Alias: I(priv)'
  type:
    description:
      - Type of database object to set privileges on.
      - The `default_prives` choice is available starting at version 2.7.
    default: table
    choices: [table, sequence, function, database,
              schema, language, tablespace, group,
              default_privs]
  objs:
    description:
      - Comma separated list of database objects to set privileges on.
      - If I(type) is C(table) or C(sequence), the special value
        C(ALL_IN_SCHEMA) can be provided instead to specify all database
        objects of type I(type) in the schema specified via I(schema). (This
        also works with PostgreSQL < 9.0.)
      - If I(type) is C(database), this parameter can be omitted, in which case
        privileges are set for the database specified via I(database).
      - 'If I(type) is I(function), colons (":") in object names will be
        replaced with commas (needed to specify function signatures, see
        examples)'
      - 'Alias: I(obj)'
  schema:
    description:
      - Schema that contains the database objects specified via I(objs).
      - May only be provided if I(type) is C(table), C(sequence), C(function)
        or C(default_privs). Defaults to  C(public) in these cases.
  roles:
    description:
      - Comma separated list of role (user/group) names to set permissions for.
      - The special value C(PUBLIC) can be provided instead to set permissions
        for the implicitly defined PUBLIC group.
      - 'Alias: I(role)'
    required: yes
  session_role:
    version_added: "2.8"
    description: |
      Switch to session_role after connecting. The specified session_role must be a role that the current login_user is a member of.
      Permissions checking for SQL commands is carried out as though the session_role were the one that had logged in originally.
  grant_option:
    description:
      - Whether C(role) may grant/revoke the specified privileges/group
        memberships to others.
      - Set to C(no) to revoke GRANT OPTION, leave unspecified to
        make no changes.
      - I(grant_option) only has an effect if I(state) is C(present).
      - 'Alias: I(admin_option)'
    type: bool
  host:
    description:
      - Database host address. If unspecified, connect via Unix socket.
      - 'Alias: I(login_host)'
  port:
    description:
      - Database port to connect to.
    default: 5432
  unix_socket:
    description:
      - Path to a Unix domain socket for local connections.
      - 'Alias: I(login_unix_socket)'
  login:
    description:
      - The username to authenticate with.
      - 'Alias: I(login_user)'
    default: postgres
  password:
    description:
      - The password to authenticate with.
      - 'Alias: I(login_password))'
  ssl_mode:
    description:
      - Determines whether or with what priority a secure SSL TCP/IP connection will be negotiated with the server.
      - See https://www.postgresql.org/docs/current/static/libpq-ssl.html for more information on the modes.
      - Default of C(prefer) matches libpq default.
    default: prefer
    choices: [disable, allow, prefer, require, verify-ca, verify-full]
    version_added: '2.3'
  ssl_rootcert:
    description:
      - Specifies the name of a file containing SSL certificate authority (CA) certificate(s). If the file exists, the server's certificate will be
        verified to be signed by one of these authorities.
    version_added: '2.3'
notes:
  - Default authentication assumes that postgresql_privs is run by the
    C(postgres) user on the remote host. (Ansible's C(user) or C(sudo-user)).
  - This module requires Python package I(psycopg2) to be installed on the
    remote host. In the default case of the remote host also being the
    PostgreSQL server, PostgreSQL has to be installed there as well, obviously.
    For Debian/Ubuntu-based systems, install packages I(postgresql) and
    I(python-psycopg2).
  - Parameters that accept comma separated lists (I(privs), I(objs), I(roles))
    have singular alias names (I(priv), I(obj), I(role)).
  - To revoke only C(GRANT OPTION) for a specific object, set I(state) to
    C(present) and I(grant_option) to C(no) (see examples).
  - Note that when revoking privileges from a role R, this role  may still have
    access via privileges granted to any role R is a member of including
    C(PUBLIC).
  - Note that when revoking privileges from a role R, you do so as the user
    specified via I(login). If R has been granted the same privileges by
    another user also, R can still access database objects via these privileges.
  - When revoking privileges, C(RESTRICT) is assumed (see PostgreSQL docs).
  - The ssl_rootcert parameter requires at least Postgres version 8.4 and I(psycopg2) version 2.4.3.
requirements: [psycopg2]
extends_documentation_fragment:
  - postgres
author: "Bernhard Weitzhofer (@b6d)"
"""

EXAMPLES = """
# On database "library":
# GRANT SELECT, INSERT, UPDATE ON TABLE public.books, public.authors
# TO librarian, reader WITH GRANT OPTION
- postgresql_privs:
    database: library
    state: present
    privs: SELECT,INSERT,UPDATE
    type: table
    objs: books,authors
    schema: public
    roles: librarian,reader
    grant_option: yes

# Same as above leveraging default values:
- postgresql_privs:
    db: library
    privs: SELECT,INSERT,UPDATE
    objs: books,authors
    roles: librarian,reader
    grant_option: yes

# REVOKE GRANT OPTION FOR INSERT ON TABLE books FROM reader
# Note that role "reader" will be *granted* INSERT privilege itself if this
# isn't already the case (since state: present).
- postgresql_privs:
    db: library
    state: present
    priv: INSERT
    obj: books
    role: reader
    grant_option: no

# REVOKE INSERT, UPDATE ON ALL TABLES IN SCHEMA public FROM reader
# "public" is the default schema. This also works for PostgreSQL 8.x.
- postgresql_privs:
    db: library
    state: absent
    privs: INSERT,UPDATE
    objs: ALL_IN_SCHEMA
    role: reader

# GRANT ALL PRIVILEGES ON SCHEMA public, math TO librarian
- postgresql_privs:
    db: library
    privs: ALL
    type: schema
    objs: public,math
    role: librarian

# GRANT ALL PRIVILEGES ON FUNCTION math.add(int, int) TO librarian, reader
# Note the separation of arguments with colons.
- postgresql_privs:
    db: library
    privs: ALL
    type: function
    obj: add(int:int)
    schema: math
    roles: librarian,reader

# GRANT librarian, reader TO alice, bob WITH ADMIN OPTION
# Note that group role memberships apply cluster-wide and therefore are not
# restricted to database "library" here.
- postgresql_privs:
    db: library
    type: group
    objs: librarian,reader
    roles: alice,bob
    admin_option: yes

# GRANT ALL PRIVILEGES ON DATABASE library TO librarian
# Note that here "db: postgres" specifies the database to connect to, not the
# database to grant privileges on (which is specified via the "objs" param)
- postgresql_privs:
    db: postgres
    privs: ALL
    type: database
    obj: library
    role: librarian

# GRANT ALL PRIVILEGES ON DATABASE library TO librarian
# If objs is omitted for type "database", it defaults to the database
# to which the connection is established
- postgresql_privs:
    db: library
    privs: ALL
    type: database
    role: librarian

# Available since version 2.7
# ALTER DEFAULT PRIVILEGES ON DATABASE library TO librarian
# Objs must be set, ALL_DEFAULT to TABLES/SEQUENCES/TYPES/FUNCTIONS
# ALL_DEFAULT works only with privs=ALL
# For specific
- postgresql_privs:
    db: library
    objs: ALL_DEFAULT
    privs: ALL
    type: default_privs
    role: librarian
    grant_option: yes

# Available since version 2.7
# ALTER DEFAULT PRIVILEGES ON DATABASE library TO reader
# Objs must be set, ALL_DEFAULT to TABLES/SEQUENCES/TYPES/FUNCTIONS
# ALL_DEFAULT works only with privs=ALL
# For specific
- postgresql_privs:
    db: library
    objs: TABLES,SEQUENCES
    privs: SELECT
    type: default_privs
    role: reader

- postgresql_privs:
    db: library
    objs: TYPES
    privs: USAGE
    type: default_privs
    role: reader

"""

import traceback

try:
    import psycopg2
    import psycopg2.extensions
except ImportError:
    psycopg2 = None

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import pg_quote_identifier
from ansible.module_utils._text import to_native

VALID_PRIVS = frozenset(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                         'REFERENCES', 'TRIGGER', 'CREATE', 'CONNECT',
                         'TEMPORARY', 'TEMP', 'EXECUTE', 'USAGE', 'ALL', 'USAGE'))
VALID_DEFAULT_OBJS = {'TABLES': ('ALL', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER'),
                      'SEQUENCES': ('ALL', 'SELECT', 'UPDATE', 'USAGE'),
                      'FUNCTIONS': ('ALL', 'EXECUTE'),
                      'TYPES': ('ALL', 'USAGE')}


class Error(Exception):
    pass


# We don't have functools.partial in Python < 2.5
def partial(f, *args, **kwargs):
    """Partial function application"""

    def g(*g_args, **g_kwargs):
        new_kwargs = kwargs.copy()
        new_kwargs.update(g_kwargs)
        return f(*(args + g_args), **g_kwargs)

    g.f = f
    g.args = args
    g.kwargs = kwargs
    return g


class Connection(object):
    """Wrapper around a psycopg2 connection with some convenience methods"""

    def __init__(self, params):
        self.database = params.database
        # To use defaults values, keyword arguments must be absent, so
        # check which values are empty and don't include in the **kw
        # dictionary
        params_map = {
            "host": "host",
            "login": "user",
            "password": "password",
            "port": "port",
            "database": "database",
            "ssl_mode": "sslmode",
            "ssl_rootcert": "sslrootcert"
        }

        kw = dict((params_map[k], getattr(params, k)) for k in params_map
                  if getattr(params, k) != '' and getattr(params, k) is not None)

        # If a unix_socket is specified, incorporate it here.
        is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"
        if is_localhost and params.unix_socket != "":
            kw["host"] = params.unix_socket

        sslrootcert = params.ssl_rootcert
        if psycopg2.__version__ < '2.4.3' and sslrootcert is not None:
            raise ValueError('psycopg2 must be at least 2.4.3 in order to user the ssl_rootcert parameter')

        self.connection = psycopg2.connect(**kw)
        self.cursor = self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    @property
    def encoding(self):
        """Connection encoding in Python-compatible form"""
        return psycopg2.extensions.encodings[self.connection.encoding]

    # Methods for querying database objects

    # PostgreSQL < 9.0 doesn't support "ALL TABLES IN SCHEMA schema"-like
    # phrases in GRANT or REVOKE statements, therefore alternative methods are
    # provided here.

    def schema_exists(self, schema):
        query = """SELECT count(*)
                   FROM pg_catalog.pg_namespace WHERE nspname = %s"""
        self.cursor.execute(query, (schema,))
        return self.cursor.fetchone()[0] > 0

    def get_all_tables_in_schema(self, schema):
        if not self.schema_exists(schema):
            raise Error('Schema "%s" does not exist.' % schema)
        query = """SELECT relname
                   FROM pg_catalog.pg_class c
                   JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                   WHERE nspname = %s AND relkind in ('r', 'v')"""
        self.cursor.execute(query, (schema,))
        return [t[0] for t in self.cursor.fetchall()]

    def get_all_sequences_in_schema(self, schema):
        if not self.schema_exists(schema):
            raise Error('Schema "%s" does not exist.' % schema)
        query = """SELECT relname
                   FROM pg_catalog.pg_class c
                   JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                   WHERE nspname = %s AND relkind = 'S'"""
        self.cursor.execute(query, (schema,))
        return [t[0] for t in self.cursor.fetchall()]

    # Methods for getting access control lists and group membership info

    # To determine whether anything has changed after granting/revoking
    # privileges, we compare the access control lists of the specified database
    # objects before and afterwards. Python's list/string comparison should
    # suffice for change detection, we should not actually have to parse ACLs.
    # The same should apply to group membership information.

    def get_table_acls(self, schema, tables):
        query = """SELECT relacl
                   FROM pg_catalog.pg_class c
                   JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                   WHERE nspname = %s AND relkind = 'r' AND relname = ANY (%s)
                   ORDER BY relname"""
        self.cursor.execute(query, (schema, tables))
        return [t[0] for t in self.cursor.fetchall()]

    def get_sequence_acls(self, schema, sequences):
        query = """SELECT relacl
                   FROM pg_catalog.pg_class c
                   JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                   WHERE nspname = %s AND relkind = 'S' AND relname = ANY (%s)
                   ORDER BY relname"""
        self.cursor.execute(query, (schema, sequences))
        return [t[0] for t in self.cursor.fetchall()]

    def get_function_acls(self, schema, function_signatures):
        funcnames = [f.split('(', 1)[0] for f in function_signatures]
        query = """SELECT proacl
                   FROM pg_catalog.pg_proc p
                   JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
                   WHERE nspname = %s AND proname = ANY (%s)
                   ORDER BY proname, proargtypes"""
        self.cursor.execute(query, (schema, funcnames))
        return [t[0] for t in self.cursor.fetchall()]

    def get_schema_acls(self, schemas):
        query = """SELECT nspacl FROM pg_catalog.pg_namespace
                   WHERE nspname = ANY (%s) ORDER BY nspname"""
        self.cursor.execute(query, (schemas,))
        return [t[0] for t in self.cursor.fetchall()]

    def get_language_acls(self, languages):
        query = """SELECT lanacl FROM pg_catalog.pg_language
                   WHERE lanname = ANY (%s) ORDER BY lanname"""
        self.cursor.execute(query, (languages,))
        return [t[0] for t in self.cursor.fetchall()]

    def get_tablespace_acls(self, tablespaces):
        query = """SELECT spcacl FROM pg_catalog.pg_tablespace
                   WHERE spcname = ANY (%s) ORDER BY spcname"""
        self.cursor.execute(query, (tablespaces,))
        return [t[0] for t in self.cursor.fetchall()]

    def get_database_acls(self, databases):
        query = """SELECT datacl FROM pg_catalog.pg_database
                   WHERE datname = ANY (%s) ORDER BY datname"""
        self.cursor.execute(query, (databases,))
        return [t[0] for t in self.cursor.fetchall()]

    def get_group_memberships(self, groups):
        query = """SELECT roleid, grantor, member, admin_option
                   FROM pg_catalog.pg_auth_members am
                   JOIN pg_catalog.pg_roles r ON r.oid = am.roleid
                   WHERE r.rolname = ANY(%s)
                   ORDER BY roleid, grantor, member"""
        self.cursor.execute(query, (groups,))
        return self.cursor.fetchall()

    def get_default_privs(self, schema, *args):
        query = """SELECT defaclacl
                   FROM pg_default_acl a
                   JOIN pg_namespace b ON a.defaclnamespace=b.oid
                   WHERE b.nspname = %s;"""
        self.cursor.execute(query, (schema,))
        return [t[0] for t in self.cursor.fetchall()]

    # Manipulating privileges

    def manipulate_privs(self, obj_type, privs, objs, roles,
                         state, grant_option, schema_qualifier=None):
        """Manipulate database object privileges.

        :param obj_type: Type of database object to grant/revoke
                         privileges for.
        :param privs: Either a list of privileges to grant/revoke
                      or None if type is "group".
        :param objs: List of database objects to grant/revoke
                     privileges for.
        :param roles: Either a list of role names or "PUBLIC"
                      for the implicitly defined "PUBLIC" group
        :param state: "present" to grant privileges, "absent" to revoke.
        :param grant_option: Only for state "present": If True, set
                             grant/admin option. If False, revoke it.
                             If None, don't change grant option.
        :param schema_qualifier: Some object types ("TABLE", "SEQUENCE",
                                 "FUNCTION") must be qualified by schema.
                                 Ignored for other Types.
        """
        # get_status: function to get current status
        if obj_type == 'table':
            get_status = partial(self.get_table_acls, schema_qualifier)
        elif obj_type == 'sequence':
            get_status = partial(self.get_sequence_acls, schema_qualifier)
        elif obj_type == 'function':
            get_status = partial(self.get_function_acls, schema_qualifier)
        elif obj_type == 'schema':
            get_status = self.get_schema_acls
        elif obj_type == 'language':
            get_status = self.get_language_acls
        elif obj_type == 'tablespace':
            get_status = self.get_tablespace_acls
        elif obj_type == 'database':
            get_status = self.get_database_acls
        elif obj_type == 'group':
            get_status = self.get_group_memberships
        elif obj_type == 'default_privs':
            get_status = partial(self.get_default_privs, schema_qualifier)
        else:
            raise Error('Unsupported database object type "%s".' % obj_type)

        # Return False (nothing has changed) if there are no objs to work on.
        if not objs:
            return False

        # obj_ids: quoted db object identifiers (sometimes schema-qualified)
        if obj_type == 'function':
            obj_ids = []
            for obj in objs:
                try:
                    f, args = obj.split('(', 1)
                except Exception:
                    raise Error('Illegal function signature: "%s".' % obj)
                obj_ids.append('"%s"."%s"(%s' % (schema_qualifier, f, args))
        elif obj_type in ['table', 'sequence']:
            obj_ids = ['"%s"."%s"' % (schema_qualifier, o) for o in objs]
        else:
            obj_ids = ['"%s"' % o for o in objs]

        # set_what: SQL-fragment specifying what to set for the target roles:
        # Either group membership or privileges on objects of a certain type
        if obj_type == 'group':
            set_what = ','.join(pg_quote_identifier(i, 'role') for i in obj_ids)
        elif obj_type == 'default_privs':
            # We don't want privs to be quoted here
            set_what = ','.join(privs)
        else:
            # function types are already quoted above
            if obj_type != 'function':
                obj_ids = [pg_quote_identifier(i, 'table') for i in obj_ids]
            # Note: obj_type has been checked against a set of string literals
            # and privs was escaped when it was parsed
            set_what = '%s ON %s %s' % (','.join(privs), obj_type,
                                        ','.join(obj_ids))

        # for_whom: SQL-fragment specifying for whom to set the above
        if roles == 'PUBLIC':
            for_whom = 'PUBLIC'
        else:
            for_whom = ','.join(pg_quote_identifier(r, 'role') for r in roles)

        status_before = get_status(objs)

        query = QueryBuilder(state) \
            .for_objtype(obj_type) \
            .with_grant_option(grant_option) \
            .for_whom(for_whom) \
            .for_schema(schema_qualifier) \
            .set_what(set_what) \
            .for_objs(objs) \
            .build()

        self.cursor.execute(query)
        status_after = get_status(objs)
        return status_before != status_after


class QueryBuilder(object):
    def __init__(self, state):
        self._grant_option = None
        self._for_whom = None
        self._set_what = None
        self._obj_type = None
        self._state = state
        self._schema = None
        self._objs = None
        self.query = []

    def for_objs(self, objs):
        self._objs = objs
        return self

    def for_schema(self, schema):
        self._schema = schema
        return self

    def with_grant_option(self, option):
        self._grant_option = option
        return self

    def for_whom(self, who):
        self._for_whom = who
        return self

    def set_what(self, what):
        self._set_what = what
        return self

    def for_objtype(self, objtype):
        self._obj_type = objtype
        return self

    def build(self):
        if self._state == 'present':
            self.build_present()
        elif self._state == 'absent':
            self.build_absent()
        else:
            self.build_absent()
        return '\n'.join(self.query)

    def add_default_revoke(self):
        for obj in self._objs:
            self.query.append(
                'ALTER DEFAULT PRIVILEGES IN SCHEMA {0} REVOKE ALL ON {1} FROM {2};'.format(self._schema, obj,
                                                                                            self._for_whom))

    def add_grant_option(self):
        if self._grant_option:
            if self._obj_type == 'group':
                self.query[-1] += ' WITH ADMIN OPTION;'
            else:
                self.query[-1] += ' WITH GRANT OPTION;'
        else:
            self.query[-1] += ';'
            if self._obj_type == 'group':
                self.query.append('REVOKE ADMIN OPTION FOR {0} FROM {1};'.format(self._set_what, self._for_whom))
            elif not self._obj_type == 'default_privs':
                self.query.append('REVOKE GRANT OPTION FOR {0} FROM {1};'.format(self._set_what, self._for_whom))

    def add_default_priv(self):
        for obj in self._objs:
            self.query.append(
                'ALTER DEFAULT PRIVILEGES IN SCHEMA {0} GRANT {1} ON {2} TO {3}'.format(self._schema, self._set_what,
                                                                                        obj,
                                                                                        self._for_whom))
            self.add_grant_option()
        self.query.append(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA {0} GRANT USAGE ON TYPES TO {1}'.format(self._schema, self._for_whom))
        self.add_grant_option()

    def build_present(self):
        if self._obj_type == 'default_privs':
            self.add_default_revoke()
            self.add_default_priv()
        else:
            self.query.append('GRANT {0} TO {1}'.format(self._set_what, self._for_whom))
            self.add_grant_option()

    def build_absent(self):
        if self._obj_type == 'default_privs':
            self.query = []
            for obj in ['TABLES', 'SEQUENCES', 'TYPES']:
                self.query.append(
                    'ALTER DEFAULT PRIVILEGES IN SCHEMA {0} REVOKE ALL ON {1} FROM {2};'.format(self._schema, obj,
                                                                                                self._for_whom))
        else:
            self.query.append('REVOKE {0} FROM {1};'.format(self._set_what, self._for_whom))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            database=dict(required=True, aliases=['db']),
            state=dict(default='present', choices=['present', 'absent']),
            privs=dict(required=False, aliases=['priv']),
            type=dict(default='table',
                      choices=['table',
                               'sequence',
                               'function',
                               'database',
                               'schema',
                               'language',
                               'tablespace',
                               'group',
                               'default_privs']),
            objs=dict(required=False, aliases=['obj']),
            schema=dict(required=False),
            roles=dict(required=True, aliases=['role']),
            session_role=dict(required=False),
            grant_option=dict(required=False, type='bool',
                              aliases=['admin_option']),
            host=dict(default='', aliases=['login_host']),
            port=dict(type='int', default=5432),
            unix_socket=dict(default='', aliases=['login_unix_socket']),
            login=dict(default='postgres', aliases=['login_user']),
            password=dict(default='', aliases=['login_password'], no_log=True),
            ssl_mode=dict(default="prefer",
                          choices=['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']),
            ssl_rootcert=dict(default=None)
        ),
        supports_check_mode=True
    )

    # Create type object as namespace for module params
    p = type('Params', (), module.params)
    # param "schema": default, allowed depends on param "type"
    if p.type in ['table', 'sequence', 'function', 'default_privs']:
        p.schema = p.schema or 'public'
    elif p.schema:
        module.fail_json(msg='Argument "schema" is not allowed '
                             'for type "%s".' % p.type)

    # param "objs": default, required depends on param "type"
    if p.type == 'database':
        p.objs = p.objs or p.database
    elif not p.objs:
        module.fail_json(msg='Argument "objs" is required '
                             'for type "%s".' % p.type)

    # param "privs": allowed, required depends on param "type"
    if p.type == 'group':
        if p.privs:
            module.fail_json(msg='Argument "privs" is not allowed '
                                 'for type "group".')
    elif not p.privs:
        module.fail_json(msg='Argument "privs" is required '
                             'for type "%s".' % p.type)

    # Connect to Database
    if not psycopg2:
        module.fail_json(msg='Python module "psycopg2" must be installed.')
    try:
        conn = Connection(p)
    except psycopg2.Error as e:
        module.fail_json(msg='Could not connect to database: %s' % to_native(e), exception=traceback.format_exc())
    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least version 8.4 to support sslrootcert')
        module.fail_json(msg="unable to connect to database: %s" % to_native(e), exception=traceback.format_exc())
    except ValueError as e:
        # We raise this when the psycopg library is too old
        module.fail_json(msg=to_native(e))

    if p.session_role:
        try:
            conn.cursor.execute('SET ROLE %s' % pg_quote_identifier(p.session_role, 'role'))
        except Exception as e:
            module.fail_json(msg="Could not switch to role %s: %s" % (p.session_role, to_native(e)), exception=traceback.format_exc())

    try:
        # privs
        if p.privs:
            privs = frozenset(pr.upper() for pr in p.privs.split(','))
            if not privs.issubset(VALID_PRIVS):
                module.fail_json(msg='Invalid privileges specified: %s' % privs.difference(VALID_PRIVS))
        else:
            privs = None
        # objs:
        if p.type == 'table' and p.objs == 'ALL_IN_SCHEMA':
            objs = conn.get_all_tables_in_schema(p.schema)
        elif p.type == 'sequence' and p.objs == 'ALL_IN_SCHEMA':
            objs = conn.get_all_sequences_in_schema(p.schema)
        elif p.type == 'default_privs':
            if p.objs == 'ALL_DEFAULT':
                objs = frozenset(VALID_DEFAULT_OBJS.keys())
            else:
                objs = frozenset(obj.upper() for obj in p.objs.split(','))
                if not objs.issubset(VALID_DEFAULT_OBJS):
                    module.fail_json(
                        msg='Invalid Object set specified: %s' % objs.difference(VALID_DEFAULT_OBJS.keys()))
            # Again, do we have valid privs specified for object type:
            valid_objects_for_priv = frozenset(obj for obj in objs if privs.issubset(VALID_DEFAULT_OBJS[obj]))
            if not valid_objects_for_priv == objs:
                module.fail_json(
                    msg='Invalid priv specified. Valid object for priv: {0}. Objects: {1}'.format(
                        valid_objects_for_priv, objs))
        else:
            objs = p.objs.split(',')

        # function signatures are encoded using ':' to separate args
        if p.type == 'function':
            objs = [obj.replace(':', ',') for obj in objs]

        # roles
        if p.roles == 'PUBLIC':
            roles = 'PUBLIC'
        else:
            roles = p.roles.split(',')

        changed = conn.manipulate_privs(
            obj_type=p.type,
            privs=privs,
            objs=objs,
            roles=roles,
            state=p.state,
            grant_option=p.grant_option,
            schema_qualifier=p.schema
        )

    except Error as e:
        conn.rollback()
        module.fail_json(msg=e.message, exception=traceback.format_exc())

    except psycopg2.Error as e:
        conn.rollback()
        module.fail_json(msg=to_native(e.message))

    if module.check_mode:
        conn.rollback()
    else:
        conn.commit()
    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
