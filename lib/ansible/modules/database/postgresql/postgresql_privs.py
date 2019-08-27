#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: postgresql_privs
version_added: '1.2'
short_description: Grant or revoke privileges on PostgreSQL database objects
description:
- Grant or revoke privileges on PostgreSQL database objects.
- This module is basically a wrapper around most of the functionality of
  PostgreSQL's GRANT and REVOKE statements with detection of changes
  (GRANT/REVOKE I(privs) ON I(type) I(objs) TO/FROM I(roles)).
options:
  database:
    description:
    - Name of database to connect to.
    required: yes
    type: str
    aliases:
    - db
    - login_db
  state:
    description:
    - If C(present), the specified privileges are granted, if C(absent) they are revoked.
    type: str
    default: present
    choices: [ absent, present ]
  privs:
    description:
    - Comma separated list of privileges to grant/revoke.
    type: str
    aliases:
    - priv
  type:
    description:
    - Type of database object to set privileges on.
    - The `default_privs` choice is available starting at version 2.7.
    - The 'foreign_data_wrapper' and 'foreign_server' object types are available from Ansible version '2.8'.
    type: str
    default: table
    choices: [ database, default_privs, foreign_data_wrapper, foreign_server, function,
               group, language, table, tablespace, schema, sequence ]
  objs:
    description:
    - Comma separated list of database objects to set privileges on.
    - If I(type) is C(table), C(partition table), C(sequence) or C(function),
      the special valueC(ALL_IN_SCHEMA) can be provided instead to specify all
      database objects of type I(type) in the schema specified via I(schema).
      (This also works with PostgreSQL < 9.0.) (C(ALL_IN_SCHEMA) is available
       for C(function) and C(partition table) from version 2.8)
    - If I(type) is C(database), this parameter can be omitted, in which case
      privileges are set for the database specified via I(database).
    - 'If I(type) is I(function), colons (":") in object names will be
      replaced with commas (needed to specify function signatures, see examples)'
    type: str
    aliases:
    - obj
  schema:
    description:
    - Schema that contains the database objects specified via I(objs).
    - May only be provided if I(type) is C(table), C(sequence), C(function)
      or C(default_privs). Defaults to  C(public) in these cases.
    type: str
  roles:
    description:
    - Comma separated list of role (user/group) names to set permissions for.
    - The special value C(PUBLIC) can be provided instead to set permissions
      for the implicitly defined PUBLIC group.
    type: str
    required: yes
    aliases:
    - role
  fail_on_role:
    version_added: '2.8'
    description:
    - If C(yes), fail when target role (for whom privs need to be granted) does not exist.
      Otherwise just warn and continue.
    default: yes
    type: bool
  session_role:
    version_added: '2.8'
    description:
    - Switch to session_role after connecting.
    - The specified session_role must be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though the session_role were the one that had logged in originally.
    type: str
  target_roles:
    description:
    - A list of existing role (user/group) names to set as the
      default permissions for database objects subsequently created by them.
    - Parameter I(target_roles) is only available with C(type=default_privs).
    type: str
    version_added: '2.8'
  grant_option:
    description:
    - Whether C(role) may grant/revoke the specified privileges/group memberships to others.
    - Set to C(no) to revoke GRANT OPTION, leave unspecified to make no changes.
    - I(grant_option) only has an effect if I(state) is C(present).
    type: bool
    aliases:
    - admin_option
  host:
    description:
    - Database host address. If unspecified, connect via Unix socket.
    type: str
    aliases:
    - login_host
  port:
    description:
    - Database port to connect to.
    type: int
    default: 5432
    aliases:
    - login_port
  unix_socket:
    description:
    - Path to a Unix domain socket for local connections.
    type: str
    aliases:
    - login_unix_socket
  login:
    description:
    - The username to authenticate with.
    type: str
    default: postgres
    aliases:
    - login_user
  password:
    description:
    - The password to authenticate with.
    type: str
    aliases:
    - login_password
  ssl_mode:
    description:
    - Determines whether or with what priority a secure SSL TCP/IP connection will be negotiated with the server.
    - See https://www.postgresql.org/docs/current/static/libpq-ssl.html for more information on the modes.
    - Default of C(prefer) matches libpq default.
    type: str
    default: prefer
    choices: [ allow, disable, prefer, require, verify-ca, verify-full ]
    version_added: '2.3'
  ca_cert:
    description:
    - Specifies the name of a file containing SSL certificate authority (CA) certificate(s).
    - If the file exists, the server's certificate will be verified to be signed by one of these authorities.
    version_added: '2.3'
    type: str
    aliases:
    - ssl_rootcert

notes:
- Default authentication assumes that postgresql_privs is run by the
  C(postgres) user on the remote host. (Ansible's C(user) or C(sudo-user)).
- This module requires Python package I(psycopg2) to be installed on the
  remote host. In the default case of the remote host also being the
  PostgreSQL server, PostgreSQL has to be installed there as well, obviously.
  For Debian/Ubuntu-based systems, install packages I(postgresql) and I(python-psycopg2).
- Parameters that accept comma separated lists (I(privs), I(objs), I(roles))
  have singular alias names (I(priv), I(obj), I(role)).
- To revoke only C(GRANT OPTION) for a specific object, set I(state) to
  C(present) and I(grant_option) to C(no) (see examples).
- Note that when revoking privileges from a role R, this role  may still have
  access via privileges granted to any role R is a member of including C(PUBLIC).
- Note that when revoking privileges from a role R, you do so as the user
  specified via I(login). If R has been granted the same privileges by
  another user also, R can still access database objects via these privileges.
- When revoking privileges, C(RESTRICT) is assumed (see PostgreSQL docs).
- The ca_cert parameter requires at least Postgres version 8.4 and I(psycopg2) version 2.4.3.

requirements:
- psycopg2

extends_documentation_fragment:
- postgres

author:
- Bernhard Weitzhofer (@b6d)
'''

EXAMPLES = r'''
# On database "library":
# GRANT SELECT, INSERT, UPDATE ON TABLE public.books, public.authors
# TO librarian, reader WITH GRANT OPTION
- name: Grant privs to librarian and reader on database library
  postgresql_privs:
    database: library
    state: present
    privs: SELECT,INSERT,UPDATE
    type: table
    objs: books,authors
    schema: public
    roles: librarian,reader
    grant_option: yes

- name: Same as above leveraging default values
  postgresql_privs:
    db: library
    privs: SELECT,INSERT,UPDATE
    objs: books,authors
    roles: librarian,reader
    grant_option: yes

# REVOKE GRANT OPTION FOR INSERT ON TABLE books FROM reader
# Note that role "reader" will be *granted* INSERT privilege itself if this
# isn't already the case (since state: present).
- name: Revoke privs from reader
  postgresql_privs:
    db: library
    state: present
    priv: INSERT
    obj: books
    role: reader
    grant_option: no

# "public" is the default schema. This also works for PostgreSQL 8.x.
- name: REVOKE INSERT, UPDATE ON ALL TABLES IN SCHEMA public FROM reader
  postgresql_privs:
    db: library
    state: absent
    privs: INSERT,UPDATE
    objs: ALL_IN_SCHEMA
    role: reader

- name: GRANT ALL PRIVILEGES ON SCHEMA public, math TO librarian
  postgresql_privs:
    db: library
    privs: ALL
    type: schema
    objs: public,math
    role: librarian

# Note the separation of arguments with colons.
- name: GRANT ALL PRIVILEGES ON FUNCTION math.add(int, int) TO librarian, reader
  postgresql_privs:
    db: library
    privs: ALL
    type: function
    obj: add(int:int)
    schema: math
    roles: librarian,reader

# Note that group role memberships apply cluster-wide and therefore are not
# restricted to database "library" here.
- name: GRANT librarian, reader TO alice, bob WITH ADMIN OPTION
  postgresql_privs:
    db: library
    type: group
    objs: librarian,reader
    roles: alice,bob
    admin_option: yes

# Note that here "db: postgres" specifies the database to connect to, not the
# database to grant privileges on (which is specified via the "objs" param)
- name: GRANT ALL PRIVILEGES ON DATABASE library TO librarian
  postgresql_privs:
    db: postgres
    privs: ALL
    type: database
    obj: library
    role: librarian

# If objs is omitted for type "database", it defaults to the database
# to which the connection is established
- name: GRANT ALL PRIVILEGES ON DATABASE library TO librarian
  postgresql_privs:
    db: library
    privs: ALL
    type: database
    role: librarian

# Available since version 2.7
# Objs must be set, ALL_DEFAULT to TABLES/SEQUENCES/TYPES/FUNCTIONS
# ALL_DEFAULT works only with privs=ALL
# For specific
- name: ALTER DEFAULT PRIVILEGES ON DATABASE library TO librarian
  postgresql_privs:
    db: library
    objs: ALL_DEFAULT
    privs: ALL
    type: default_privs
    role: librarian
    grant_option: yes

# Available since version 2.7
# Objs must be set, ALL_DEFAULT to TABLES/SEQUENCES/TYPES/FUNCTIONS
# ALL_DEFAULT works only with privs=ALL
# For specific
- name: ALTER DEFAULT PRIVILEGES ON DATABASE library TO reader, step 1
  postgresql_privs:
    db: library
    objs: TABLES,SEQUENCES
    privs: SELECT
    type: default_privs
    role: reader

- name: ALTER DEFAULT PRIVILEGES ON DATABASE library TO reader, step 2
  postgresql_privs:
    db: library
    objs: TYPES
    privs: USAGE
    type: default_privs
    role: reader

# Available since version 2.8
- name: GRANT ALL PRIVILEGES ON FOREIGN DATA WRAPPER fdw TO reader
  postgresql_privs:
    db: test
    objs: fdw
    privs: ALL
    type: foreign_data_wrapper
    role: reader

# Available since version 2.8
- name: GRANT ALL PRIVILEGES ON FOREIGN SERVER fdw_server TO reader
  postgresql_privs:
    db: test
    objs: fdw_server
    privs: ALL
    type: foreign_server
    role: reader

# Available since version 2.8
# Grant 'execute' permissions on all functions in schema 'common' to role 'caller'
- name: GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA common TO caller
  postgresql_privs:
    type: function
    state: present
    privs: EXECUTE
    roles: caller
    objs: ALL_IN_SCHEMA
    schema: common

# Available since version 2.8
# ALTER DEFAULT PRIVILEGES FOR ROLE librarian IN SCHEMA library GRANT SELECT ON TABLES TO reader
# GRANT SELECT privileges for new TABLES objects created by librarian as
# default to the role reader.
# For specific
- name: ALTER privs
  postgresql_privs:
    db: library
    schema: library
    objs: TABLES
    privs: SELECT
    type: default_privs
    role: reader
    target_roles: librarian

# Available since version 2.8
# ALTER DEFAULT PRIVILEGES FOR ROLE librarian IN SCHEMA library REVOKE SELECT ON TABLES FROM reader
# REVOKE SELECT privileges for new TABLES objects created by librarian as
# default from the role reader.
# For specific
- name: ALTER privs
  postgresql_privs:
    db: library
    state: absent
    schema: library
    objs: TABLES
    privs: SELECT
    type: default_privs
    role: reader
    target_roles: librarian
'''

RETURN = r'''
queries:
  description: List of executed queries.
  returned: always
  type: list
  sample: ['REVOKE GRANT OPTION FOR INSERT ON TABLE "books" FROM "reader";']
  version_added: '2.8'
'''

import traceback

PSYCOPG2_IMP_ERR = None
try:
    import psycopg2
    import psycopg2.extensions
except ImportError:
    PSYCOPG2_IMP_ERR = traceback.format_exc()
    psycopg2 = None

# import module snippets
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.database import pg_quote_identifier
from ansible.module_utils.postgres import postgres_common_argument_spec
from ansible.module_utils._text import to_native

VALID_PRIVS = frozenset(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                         'REFERENCES', 'TRIGGER', 'CREATE', 'CONNECT',
                         'TEMPORARY', 'TEMP', 'EXECUTE', 'USAGE', 'ALL', 'USAGE'))
VALID_DEFAULT_OBJS = {'TABLES': ('ALL', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER'),
                      'SEQUENCES': ('ALL', 'SELECT', 'UPDATE', 'USAGE'),
                      'FUNCTIONS': ('ALL', 'EXECUTE'),
                      'TYPES': ('ALL', 'USAGE')}

executed_queries = []


class Error(Exception):
    pass


def role_exists(module, cursor, rolname):
    """Check user exists or not"""
    query = "SELECT 1 FROM pg_roles WHERE rolname = '%s'" % rolname
    try:
        cursor.execute(query)
        return cursor.rowcount > 0

    except Exception as e:
        module.fail_json(msg="Cannot execute SQL '%s': %s" % (query, to_native(e)))

    return False


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

    def __init__(self, params, module):
        self.database = params.database
        self.module = module
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
            "ca_cert": "sslrootcert"
        }

        kw = dict((params_map[k], getattr(params, k)) for k in params_map
                  if getattr(params, k) != '' and getattr(params, k) is not None)

        # If a unix_socket is specified, incorporate it here.
        is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"
        if is_localhost and params.unix_socket != "":
            kw["host"] = params.unix_socket

        sslrootcert = params.ca_cert
        if psycopg2.__version__ < '2.4.3' and sslrootcert is not None:
            raise ValueError('psycopg2 must be at least 2.4.3 in order to user the ca_cert parameter')

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
                   WHERE nspname = %s AND relkind in ('r', 'v', 'm', 'p')"""
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

    def get_all_functions_in_schema(self, schema):
        if not self.schema_exists(schema):
            raise Error('Schema "%s" does not exist.' % schema)
        query = """SELECT p.proname, oidvectortypes(p.proargtypes)
                    FROM pg_catalog.pg_proc p
                    JOIN pg_namespace n ON n.oid = p.pronamespace
                    WHERE nspname = %s"""
        self.cursor.execute(query, (schema,))
        return ["%s(%s)" % (t[0], t[1]) for t in self.cursor.fetchall()]

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
                   WHERE nspname = %s AND relkind in ('r','p','v','m') AND relname = ANY (%s)
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

    def get_foreign_data_wrapper_acls(self, fdws):
        query = """SELECT fdwacl FROM pg_catalog.pg_foreign_data_wrapper
                   WHERE fdwname = ANY (%s) ORDER BY fdwname"""
        self.cursor.execute(query, (fdws,))
        return [t[0] for t in self.cursor.fetchall()]

    def get_foreign_server_acls(self, fs):
        query = """SELECT srvacl FROM pg_catalog.pg_foreign_server
                   WHERE srvname = ANY (%s) ORDER BY srvname"""
        self.cursor.execute(query, (fs,))
        return [t[0] for t in self.cursor.fetchall()]

    # Manipulating privileges

    def manipulate_privs(self, obj_type, privs, objs, roles, target_roles,
                         state, grant_option, schema_qualifier=None, fail_on_role=True):
        """Manipulate database object privileges.

        :param obj_type: Type of database object to grant/revoke
                         privileges for.
        :param privs: Either a list of privileges to grant/revoke
                      or None if type is "group".
        :param objs: List of database objects to grant/revoke
                     privileges for.
        :param roles: Either a list of role names or "PUBLIC"
                      for the implicitly defined "PUBLIC" group
        :param target_roles: List of role names to grant/revoke
                             default privileges as.
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
        elif obj_type == 'foreign_data_wrapper':
            get_status = self.get_foreign_data_wrapper_acls
        elif obj_type == 'foreign_server':
            get_status = self.get_foreign_server_acls
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
            # Note: Underscores are replaced with spaces to support multi-word obj_type
            set_what = '%s ON %s %s' % (','.join(privs), obj_type.replace('_', ' '),
                                        ','.join(obj_ids))

        # for_whom: SQL-fragment specifying for whom to set the above
        if roles == 'PUBLIC':
            for_whom = 'PUBLIC'
        else:
            for_whom = []
            for r in roles:
                if not role_exists(self.module, self.cursor, r):
                    if fail_on_role:
                        self.module.fail_json(msg="Role '%s' does not exist" % r.strip())

                    else:
                        self.module.warn("Role '%s' does not exist, pass it" % r.strip())
                else:
                    for_whom.append(pg_quote_identifier(r, 'role'))

            if not for_whom:
                return False

            for_whom = ','.join(for_whom)

        # as_who:
        as_who = None
        if target_roles:
            as_who = ','.join(pg_quote_identifier(r, 'role') for r in target_roles)

        status_before = get_status(objs)

        query = QueryBuilder(state) \
            .for_objtype(obj_type) \
            .with_grant_option(grant_option) \
            .for_whom(for_whom) \
            .as_who(as_who) \
            .for_schema(schema_qualifier) \
            .set_what(set_what) \
            .for_objs(objs) \
            .build()

        executed_queries.append(query)
        self.cursor.execute(query)
        status_after = get_status(objs)
        return status_before != status_after


class QueryBuilder(object):
    def __init__(self, state):
        self._grant_option = None
        self._for_whom = None
        self._as_who = None
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

    def as_who(self, target_roles):
        self._as_who = target_roles
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
            if self._as_who:
                self.query.append(
                    'ALTER DEFAULT PRIVILEGES FOR ROLE {0} IN SCHEMA {1} REVOKE ALL ON {2} FROM {3};'.format(self._as_who,
                                                                                                             self._schema, obj,
                                                                                                             self._for_whom))
            else:
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
            if self._as_who:
                self.query.append(
                    'ALTER DEFAULT PRIVILEGES FOR ROLE {0} IN SCHEMA {1} GRANT {2} ON {3} TO {4}'.format(self._as_who,
                                                                                                         self._schema,
                                                                                                         self._set_what,
                                                                                                         obj,
                                                                                                         self._for_whom))
            else:
                self.query.append(
                    'ALTER DEFAULT PRIVILEGES IN SCHEMA {0} GRANT {1} ON {2} TO {3}'.format(self._schema,
                                                                                            self._set_what,
                                                                                            obj,
                                                                                            self._for_whom))
            self.add_grant_option()
        if self._as_who:
            self.query.append(
                'ALTER DEFAULT PRIVILEGES FOR ROLE {0} IN SCHEMA {1} GRANT USAGE ON TYPES TO {2}'.format(self._as_who,
                                                                                                         self._schema,
                                                                                                         self._for_whom))
        else:
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
                if self._as_who:
                    self.query.append(
                        'ALTER DEFAULT PRIVILEGES FOR ROLE {0} IN SCHEMA {1} REVOKE ALL ON {2} FROM {3};'.format(self._as_who,
                                                                                                                 self._schema, obj,
                                                                                                                 self._for_whom))
                else:
                    self.query.append(
                        'ALTER DEFAULT PRIVILEGES IN SCHEMA {0} REVOKE ALL ON {1} FROM {2};'.format(self._schema, obj,
                                                                                                    self._for_whom))
        else:
            self.query.append('REVOKE {0} FROM {1};'.format(self._set_what, self._for_whom))


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        database=dict(required=True, aliases=['db', 'login_db']),
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
                           'default_privs',
                           'foreign_data_wrapper',
                           'foreign_server']),
        objs=dict(required=False, aliases=['obj']),
        schema=dict(required=False),
        roles=dict(required=True, aliases=['role']),
        session_role=dict(required=False),
        target_roles=dict(required=False),
        grant_option=dict(required=False, type='bool',
                          aliases=['admin_option']),
        host=dict(default='', aliases=['login_host']),
        unix_socket=dict(default='', aliases=['login_unix_socket']),
        login=dict(default='postgres', aliases=['login_user']),
        password=dict(default='', aliases=['login_password'], no_log=True),
        fail_on_role=dict(type='bool', default=True),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    fail_on_role = module.params['fail_on_role']

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
        module.fail_json(msg=missing_required_lib('psycopg2'), exception=PSYCOPG2_IMP_ERR)
    try:
        conn = Connection(p, module)
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
        elif p.type == 'function' and p.objs == 'ALL_IN_SCHEMA':
            objs = conn.get_all_functions_in_schema(p.schema)
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

            if len(roles) == 1 and not role_exists(module, conn.cursor, roles[0]):
                module.exit_json(changed=False)

                if fail_on_role:
                    module.fail_json(msg="Role '%s' does not exist" % roles[0].strip())

                else:
                    module.warn("Role '%s' does not exist, nothing to do" % roles[0].strip())

        # check if target_roles is set with type: default_privs
        if p.target_roles and not p.type == 'default_privs':
            module.warn('"target_roles" will be ignored '
                        'Argument "type: default_privs" is required for usage of "target_roles".')

        # target roles
        if p.target_roles:
            target_roles = p.target_roles.split(',')
        else:
            target_roles = None

        changed = conn.manipulate_privs(
            obj_type=p.type,
            privs=privs,
            objs=objs,
            roles=roles,
            target_roles=target_roles,
            state=p.state,
            grant_option=p.grant_option,
            schema_qualifier=p.schema,
            fail_on_role=fail_on_role,
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
    module.exit_json(changed=changed, queries=executed_queries)


if __name__ == '__main__':
    main()
