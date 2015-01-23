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

DOCUMENTATION = '''
---
module: postgresql_user
short_description: Adds or removes a users (roles) from a PostgreSQL database.
description:
   - Add or remove PostgreSQL users (roles) from a remote host and, optionally,
     grant the users access to an existing database or tables.
   - The fundamental function of the module is to create, or delete, roles from
     a PostgreSQL cluster. Privilege assignment, or removal, is an optional
     step, which works on one database at a time. This allows for the module to
     be called several times in the same module to modify the permissions on
     different databases, or to grant permissions to already existing users.
   - A user cannot be removed until all the privileges have been stripped from
     the user. In such situation, if the module tries to remove the user it
     will fail. To avoid this from happening the fail_on_user option signals
     the module to try to remove the user, but if not possible keep going; the
     module will report if changes happened and separately if the user was
     removed or not.
version_added: "0.6"
options:
  name:
    description:
      - name of the user (role) to add or remove
    required: true
    default: null
  password:
    description:
      - set the user's password, before 1.4 this was required.
      - "When passing an encrypted password, the encrypted parameter must also be true, and it must be generated with the format C('str[\\"md5\\"] + md5[ password + username ]'), resulting in a total of 35 characters.  An easy way to do this is: C(echo \\"md5`echo -n \\"verysecretpasswordJOE\\" | md5`\\")."
    required: false
    default: null
  db:
    description:
      - name of database where permissions will be granted
    required: false
    default: null
  fail_on_user:
    description:
      - if C(yes), fail when user can't be removed. Otherwise just log and continue
    required: false
    default: 'yes'
    choices: [ "yes", "no" ]
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
  login_unix_socket:
    description:
      - Path to a Unix domain socket for local connections
    required: false
    default: null
  priv:
    description:
      - "PostgreSQL privileges string in the format: C(table:priv1,priv2)"
    required: false
    default: null
  role_attr_flags:
    description:
      - "PostgreSQL role attributes string in the format: CREATEDB,CREATEROLE,SUPERUSER"
    required: false
    default: null
    choices: [ "[NO]SUPERUSER","[NO]CREATEROLE", "[NO]CREATEUSER", "[NO]CREATEDB",
                    "[NO]INHERIT", "[NO]LOGIN", "[NO]REPLICATION" ]
  state:
    description:
      - The user (role) state
    required: false
    default: present
    choices: [ "present", "absent" ]
  encrypted:
    description:
      - denotes if the password is already encrypted. boolean.
    required: false
    default: false
    version_added: '1.4'
  expires:
    description:
      - sets the user's password expiration.
    required: false
    default: null
    version_added: '1.4'
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
requirements: [ psycopg2 ]
author: Lorin Hochstein
'''

EXAMPLES = '''
# Create django user and grant access to database and products table
- postgresql_user: db=acme name=django password=ceec4eif7ya priv=CONNECT/products:ALL

# Create rails user, grant privilege to create other databases and demote rails from super user status
- postgresql_user: name=rails password=secret role_attr_flags=CREATEDB,NOSUPERUSER

# Remove test user privileges from acme
- postgresql_user: db=acme name=test priv=ALL/products:ALL state=absent fail_on_user=no

# Remove test user from test database and the cluster
- postgresql_user: db=test name=test priv=ALL state=absent

# Example privileges string format
INSERT,UPDATE/table:SELECT/anothertable:ALL

# Remove an existing user's password
- postgresql_user: db=test user=test password=NULL
'''

import re
import itertools

try:
    import psycopg2
except ImportError:
    postgresqldb_found = False
else:
    postgresqldb_found = True

_flags = ('SUPERUSER', 'CREATEROLE', 'CREATEUSER', 'CREATEDB', 'INHERIT', 'LOGIN', 'REPLICATION')
VALID_FLAGS = frozenset(itertools.chain(_flags, ('NO%s' % f for f in _flags)))

VALID_PRIVS = dict(table=frozenset(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER', 'ALL', 'USAGE')),
        database=frozenset(('CREATE', 'CONNECT', 'TEMPORARY', 'TEMP', 'ALL', 'USAGE')),
        )

class InvalidFlagsError(Exception):
    pass

class InvalidPrivsError(Exception):
    pass

# ===========================================
# PostgreSQL module specific support methods.
#


def user_exists(cursor, user):
    # The PUBLIC user is a special case that is always there
    if user == 'PUBLIC':
        return True
    query = "SELECT rolname FROM pg_roles WHERE rolname=%(user)s"
    cursor.execute(query, {'user': user})
    return cursor.rowcount > 0


def user_add(cursor, user, password, role_attr_flags, encrypted, expires):
    """Create a new database user (role)."""
    # Note: role_attr_flags escaped by parse_role_attrs and encrypted is a literal
    query_password_data = dict(password=password, expires=expires)
    query = ['CREATE USER %(user)s' % { "user": pg_quote_identifier(user, 'role')}]
    if password is not None:
        query.append("WITH %(crypt)s" % { "crypt": encrypted })
        query.append("PASSWORD %(password)s")
    if expires is not None:
        query.append("VALID UNTIL %(expires)s")
    query.append(role_attr_flags)
    query = ' '.join(query)
    cursor.execute(query, query_password_data)
    return True

def user_alter(cursor, module, user, password, role_attr_flags, encrypted, expires):
    """Change user password and/or attributes. Return True if changed, False otherwise."""
    changed = False

    # Note: role_attr_flags escaped by parse_role_attrs and encrypted is a literal
    if user == 'PUBLIC':
        if password is not None:
            module.fail_json(msg="cannot change the password for PUBLIC user")
        elif role_attr_flags != '':
            module.fail_json(msg="cannot change the role_attr_flags for PUBLIC user")
        else:
            return False

    # Handle passwords.
    if password is not None or role_attr_flags is not None:
        # Select password and all flag-like columns in order to verify changes.
        query_password_data = dict(password=password, expires=expires)
        select = "SELECT * FROM pg_authid where rolname=%(user)s"
        cursor.execute(select, {"user": user})
        # Grab current role attributes.
        current_role_attrs = cursor.fetchone()

        alter = ['ALTER USER %(user)s' % {"user": pg_quote_identifier(user, 'role')}]
        if password is not None:
            alter.append("WITH %(crypt)s" % {"crypt": encrypted})
            alter.append("PASSWORD %(password)s")
            alter.append(role_attr_flags)
        elif role_attr_flags:
            alter.append('WITH %s' % role_attr_flags)
        if expires is not None:
            alter.append("VALID UNTIL %(expires)s")

        try:
            cursor.execute(' '.join(alter), query_password_data)
        except psycopg2.InternalError, e:
            if e.pgcode == '25006':
                # Handle errors due to read-only transactions indicated by pgcode 25006
                # ERROR:  cannot execute ALTER ROLE in a read-only transaction
                changed = False
                module.fail_json(msg=e.pgerror)
                return changed
            else:
                raise psycopg2.InternalError, e

        # Grab new role attributes.
        cursor.execute(select, {"user": user})
        new_role_attrs = cursor.fetchone()

        # Detect any differences between current_ and new_role_attrs.
        for i in range(len(current_role_attrs)):
            if current_role_attrs[i] != new_role_attrs[i]:
                changed = True

    return changed

def user_delete(cursor, user):
    """Try to remove a user. Returns True if successful otherwise False"""
    cursor.execute("SAVEPOINT ansible_pgsql_user_delete")
    try:
        cursor.execute("DROP USER %s" % pg_quote_identifier(user, 'role'))
    except:
        cursor.execute("ROLLBACK TO SAVEPOINT ansible_pgsql_user_delete")
        cursor.execute("RELEASE SAVEPOINT ansible_pgsql_user_delete")
        return False

    cursor.execute("RELEASE SAVEPOINT ansible_pgsql_user_delete")
    return True

def has_table_privilege(cursor, user, table, priv):
    query = 'SELECT has_table_privilege(%s, %s, %s)'
    cursor.execute(query, (user, table, priv))
    return cursor.fetchone()[0]

def get_table_privileges(cursor, user, table):
    if '.' in table:
        schema, table = table.split('.', 1)
    else:
        schema = 'public'
    query = '''SELECT privilege_type FROM information_schema.role_table_grants
    WHERE grantee=%s AND table_name=%s AND table_schema=%s'''
    cursor.execute(query, (user, table, schema))
    return set([x[0] for x in cursor.fetchall()])

def grant_table_privilege(cursor, user, table, priv):
    # Note: priv escaped by parse_privs
    prev_priv = get_table_privileges(cursor, user, table)
    query = 'GRANT %s ON TABLE %s TO %s' % (
        priv, pg_quote_identifier(table, 'table'), pg_quote_identifier(user, 'role') )
    cursor.execute(query)
    curr_priv = get_table_privileges(cursor, user, table)
    return len(curr_priv) > len(prev_priv)

def revoke_table_privilege(cursor, user, table, priv):
    # Note: priv escaped by parse_privs
    prev_priv = get_table_privileges(cursor, user, table)
    query = 'REVOKE %s ON TABLE %s FROM %s' % (
        priv, pg_quote_identifier(table, 'table'), pg_quote_identifier(user, 'role') )
    cursor.execute(query)
    curr_priv = get_table_privileges(cursor, user, table)
    return len(curr_priv) < len(prev_priv)


def get_database_privileges(cursor, user, db):
    priv_map = {
        'C':'CREATE',
        'T':'TEMPORARY',
        'c':'CONNECT',
    }
    query = 'SELECT datacl FROM pg_database WHERE datname = %s'
    cursor.execute(query, (db,))
    datacl = cursor.fetchone()[0]
    if datacl is None:
        return []
    r = re.search('%s=(C?T?c?)/[a-z]+\,?' % user, datacl)
    if r is None:
        return []
    o = []
    for v in r.group(1):
        o.append(priv_map[v])
    return o

def has_database_privilege(cursor, user, db, priv):
    query = 'SELECT has_database_privilege(%s, %s, %s)'
    cursor.execute(query, (user, db, priv))
    return cursor.fetchone()[0]

def grant_database_privilege(cursor, user, db, priv):
    # Note: priv escaped by parse_privs
    prev_priv = get_database_privileges(cursor, user, db)
    if user == "PUBLIC":
        query = 'GRANT %s ON DATABASE %s TO PUBLIC' % (
                priv, pg_quote_identifier(db, 'database'))
    else:
        query = 'GRANT %s ON DATABASE %s TO %s' % (
                priv, pg_quote_identifier(db, 'database'),
                pg_quote_identifier(user, 'role'))
    cursor.execute(query)
    curr_priv = get_database_privileges(cursor, user, db)
    return len(curr_priv) > len(prev_priv)

def revoke_database_privilege(cursor, user, db, priv):
    # Note: priv escaped by parse_privs
    prev_priv = get_database_privileges(cursor, user, db)
    if user == "PUBLIC":
        query = 'REVOKE %s ON DATABASE %s FROM PUBLIC' % (
                priv, pg_quote_identifier(db, 'database'))
    else:
        query = 'REVOKE %s ON DATABASE %s FROM %s' % (
                priv, pg_quote_identifier(db, 'database'),
                pg_quote_identifier(user, 'role'))
    cursor.execute(query)
    curr_priv = get_database_privileges(cursor, user, db)
    return len(curr_priv) < len(prev_priv)

def revoke_privileges(cursor, user, privs):
    if privs is None:
        return False

    changed = False
    for type_ in privs:
        revoke_func = {
            'table':revoke_table_privilege,
            'database':revoke_database_privilege
        }[type_]
        for name, privileges in privs[type_].iteritems():
            for privilege in privileges:
                changed = revoke_func(cursor, user, name, privilege)\
                        or changed

    return changed

def grant_privileges(cursor, user, privs):
    if privs is None:
        return False

    changed = False
    for type_ in privs:
        grant_func = {
            'table':grant_table_privilege,
            'database':grant_database_privilege
        }[type_]
        for name, privileges in privs[type_].iteritems():
            for privilege in privileges:
                changed = grant_func(cursor, user, name, privilege)\
                        or changed

    return changed

def parse_role_attrs(role_attr_flags):
    """
    Parse role attributes string for user creation.
    Format:

        attributes[,attributes,...]

    Where:

        attributes := CREATEDB,CREATEROLE,NOSUPERUSER,...
        [ "[NO]SUPERUSER","[NO]CREATEROLE", "[NO]CREATEUSER", "[NO]CREATEDB",
                            "[NO]INHERIT", "[NO]LOGIN", "[NO]REPLICATION" ]

    """
    if ',' in role_attr_flags:
        flag_set = frozenset(r.upper() for r in role_attr_flags.split(","))
    elif role_attr_flags:
        flag_set = frozenset((role_attr_flags.upper(),))
    else:
        flag_set = frozenset()
    if not flag_set.issubset(VALID_FLAGS):
        raise InvalidFlagsError('Invalid role_attr_flags specified: %s' %
                ' '.join(flag_set.difference(VALID_FLAGS)))
    o_flags = ' '.join(flag_set)
    return o_flags

def parse_privs(privs, db):
    """
    Parse privilege string to determine permissions for database db.
    Format:

        privileges[/privileges/...]

    Where:

        privileges := DATABASE_PRIVILEGES[,DATABASE_PRIVILEGES,...] |
            TABLE_NAME:TABLE_PRIVILEGES[,TABLE_PRIVILEGES,...]
    """
    if privs is None:
        return privs

    o_privs = {
        'database':{},
        'table':{}
    }
    for token in privs.split('/'):
        if ':' not in token:
            type_ = 'database'
            name = db
            priv_set = frozenset(x.strip().upper() for x in token.split(',') if x.strip())
        else:
            type_ = 'table'
            name, privileges = token.split(':', 1)
            priv_set = frozenset(x.strip().upper() for x in privileges.split(',') if x.strip())

        if not priv_set.issubset(VALID_PRIVS[type_]):
            raise InvalidPrivsError('Invalid privs specified for %s: %s' %
                (type_, ' '.join(priv_set.difference(VALID_PRIVS[type_]))))
        o_privs[type_][name] = priv_set

    return o_privs

# ===========================================
# Module execution.
#

def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default="postgres"),
            login_password=dict(default=""),
            login_host=dict(default=""),
            login_unix_socket=dict(default=""),
            user=dict(required=True, aliases=['name']),
            password=dict(default=None),
            state=dict(default="present", choices=["absent", "present"]),
            priv=dict(default=None),
            db=dict(default=''),
            port=dict(default='5432'),
            fail_on_user=dict(type='bool', default='yes'),
            role_attr_flags=dict(default=''),
            encrypted=dict(type='bool', default='no'),
            expires=dict(default=None)
        ),
        supports_check_mode = True
    )

    user = module.params["user"]
    password = module.params["password"]
    state = module.params["state"]
    fail_on_user = module.params["fail_on_user"]
    db = module.params["db"]
    if db == '' and module.params["priv"] is not None:
        module.fail_json(msg="privileges require a database to be specified")
    privs = parse_privs(module.params["priv"], db)
    port = module.params["port"]
    try:
        role_attr_flags = parse_role_attrs(module.params["role_attr_flags"])
    except InvalidFlagsError, e:
        module.fail_json(msg=str(e))
    if module.params["encrypted"]:
        encrypted = "ENCRYPTED"
    else:
        encrypted = "UNENCRYPTED"
    expires = module.params["expires"]

    if not postgresqldb_found:
        module.fail_json(msg="the python psycopg2 module is required")

    # To use defaults values, keyword arguments must be absent, so
    # check which values are empty and don't include in the **kw
    # dictionary
    params_map = {
        "login_host":"host",
        "login_user":"user",
        "login_password":"password",
        "port":"port",
        "db":"database"
    }
    kw = dict( (params_map[k], v) for (k, v) in module.params.iteritems()
              if k in params_map and v != "" )

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    try:
        db_connection = psycopg2.connect(**kw)
        cursor = db_connection.cursor()
    except Exception, e:
        module.fail_json(msg="unable to connect to database: %s" % e)

    kw = dict(user=user)
    changed = False
    user_removed = False

    if state == "present":
        if user_exists(cursor, user):
            try:
                changed = user_alter(cursor, module, user, password, role_attr_flags, encrypted, expires)
            except SQLParseError, e:
                module.fail_json(msg=str(e))
        else:
            try:
                changed = user_add(cursor, user, password, role_attr_flags, encrypted, expires)
            except SQLParseError, e:
                module.fail_json(msg=str(e))
        try:
            changed = grant_privileges(cursor, user, privs) or changed
        except SQLParseError, e:
            module.fail_json(msg=str(e))
    else:
        if user_exists(cursor, user):
            if  module.check_mode:
                changed = True
                kw['user_removed'] = True
            else:
                try:
                    changed = revoke_privileges(cursor, user, privs)
                    user_removed = user_delete(cursor, user)
                except SQLParseError, e:
                    module.fail_json(msg=str(e))
                changed = changed or user_removed
                if fail_on_user and not user_removed:
                    msg = "unable to remove user"
                    module.fail_json(msg=msg)
                kw['user_removed'] = user_removed

    if changed:
        if module.check_mode:
            db_connection.rollback()
        else:
            db_connection.commit()

    kw['changed'] = changed
    module.exit_json(**kw)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.database import *
main()
