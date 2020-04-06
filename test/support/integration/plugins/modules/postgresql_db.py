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
module: postgresql_db
short_description: Add or remove PostgreSQL databases from a remote host.
description:
   - Add or remove PostgreSQL databases from a remote host.
version_added: '0.6'
options:
  name:
    description:
      - Name of the database to add or remove
    type: str
    required: true
    aliases: [ db ]
  port:
    description:
      - Database port to connect (if needed)
    type: int
    default: 5432
    aliases:
      - login_port
  owner:
    description:
      - Name of the role to set as owner of the database
    type: str
  template:
    description:
      - Template used to create the database
    type: str
  encoding:
    description:
      - Encoding of the database
    type: str
  lc_collate:
    description:
      - Collation order (LC_COLLATE) to use in the database. Must match collation order of template database unless C(template0) is used as template.
    type: str
  lc_ctype:
    description:
      - Character classification (LC_CTYPE) to use in the database (e.g. lower, upper, ...) Must match LC_CTYPE of template database unless C(template0)
        is used as template.
    type: str
  session_role:
    description:
    - Switch to session_role after connecting. The specified session_role must be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though the session_role were the one that had logged in originally.
    type: str
    version_added: '2.8'
  state:
    description:
    - The database state.
    - C(present) implies that the database should be created if necessary.
    - C(absent) implies that the database should be removed if present.
    - C(dump) requires a target definition to which the database will be backed up. (Added in Ansible 2.4)
      Note that in some PostgreSQL versions of pg_dump, which is an embedded PostgreSQL utility and is used by the module,
      returns rc 0 even when errors occurred (e.g. the connection is forbidden by pg_hba.conf, etc.),
      so the module returns changed=True but the dump has not actually been done. Please, be sure that your version of
      pg_dump returns rc 1 in this case.
    - C(restore) also requires a target definition from which the database will be restored. (Added in Ansible 2.4)
    - The format of the backup will be detected based on the target name.
    - Supported compression formats for dump and restore include C(.pgc), C(.bz2), C(.gz) and C(.xz)
    - Supported formats for dump and restore include C(.sql) and C(.tar)
    type: str
    choices: [ absent, dump, present, restore ]
    default: present
  target:
    description:
    - File to back up or restore from.
    - Used when I(state) is C(dump) or C(restore).
    type: path
    version_added: '2.4'
  target_opts:
    description:
    - Further arguments for pg_dump or pg_restore.
    - Used when I(state) is C(dump) or C(restore).
    type: str
    version_added: '2.4'
  maintenance_db:
    description:
      - The value specifies the initial database (which is also called as maintenance DB) that Ansible connects to.
    type: str
    default: postgres
    version_added: '2.5'
  conn_limit:
    description:
      - Specifies the database connection limit.
    type: str
    version_added: '2.8'
  tablespace:
    description:
      - The tablespace to set for the database
        U(https://www.postgresql.org/docs/current/sql-alterdatabase.html).
      - If you want to move the database back to the default tablespace,
        explicitly set this to pg_default.
    type: path
    version_added: '2.9'
  dump_extra_args:
    description:
      - Provides additional arguments when I(state) is C(dump).
      - Cannot be used with dump-file-format-related arguments like ``--format=d``.
    type: str
    version_added: '2.10'
seealso:
- name: CREATE DATABASE reference
  description: Complete reference of the CREATE DATABASE command documentation.
  link: https://www.postgresql.org/docs/current/sql-createdatabase.html
- name: DROP DATABASE reference
  description: Complete reference of the DROP DATABASE command documentation.
  link: https://www.postgresql.org/docs/current/sql-dropdatabase.html
- name: pg_dump reference
  description: Complete reference of pg_dump documentation.
  link: https://www.postgresql.org/docs/current/app-pgdump.html
- name: pg_restore reference
  description: Complete reference of pg_restore documentation.
  link: https://www.postgresql.org/docs/current/app-pgrestore.html
- module: postgresql_tablespace
- module: postgresql_info
- module: postgresql_ping
notes:
- State C(dump) and C(restore) don't require I(psycopg2) since version 2.8.
author: "Ansible Core Team"
extends_documentation_fragment:
- postgres
'''

EXAMPLES = r'''
- name: Create a new database with name "acme"
  postgresql_db:
    name: acme

# Note: If a template different from "template0" is specified, encoding and locale settings must match those of the template.
- name: Create a new database with name "acme" and specific encoding and locale # settings.
  postgresql_db:
    name: acme
    encoding: UTF-8
    lc_collate: de_DE.UTF-8
    lc_ctype: de_DE.UTF-8
    template: template0

# Note: Default limit for the number of concurrent connections to a specific database is "-1", which means "unlimited"
- name: Create a new database with name "acme" which has a limit of 100 concurrent connections
  postgresql_db:
    name: acme
    conn_limit: "100"

- name: Dump an existing database to a file
  postgresql_db:
    name: acme
    state: dump
    target: /tmp/acme.sql

- name: Dump an existing database to a file excluding the test table
  postgresql_db:
    name: acme
    state: dump
    target: /tmp/acme.sql
    dump_extra_args: --exclude-table=test

- name: Dump an existing database to a file (with compression)
  postgresql_db:
    name: acme
    state: dump
    target: /tmp/acme.sql.gz

- name: Dump a single schema for an existing database
  postgresql_db:
    name: acme
    state: dump
    target: /tmp/acme.sql
    target_opts: "-n public"

# Note: In the example below, if database foo exists and has another tablespace
# the tablespace will be changed to foo. Access to the database will be locked
# until the copying of database files is finished.
- name: Create a new database called foo in tablespace bar
  postgresql_db:
    name: foo
    tablespace: bar
'''

RETURN = r'''
executed_commands:
  description: List of commands which tried to run.
  returned: always
  type: list
  sample: ["CREATE DATABASE acme"]
  version_added: '2.10'
'''


import os
import subprocess
import traceback

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    HAS_PSYCOPG2 = False
else:
    HAS_PSYCOPG2 = True

import ansible.module_utils.postgres as pgutils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import SQLParseError, pg_quote_identifier
from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_native

executed_commands = []


class NotSupportedError(Exception):
    pass

# ===========================================
# PostgreSQL module specific support methods.
#


def set_owner(cursor, db, owner):
    query = 'ALTER DATABASE %s OWNER TO "%s"' % (
            pg_quote_identifier(db, 'database'),
            owner)
    executed_commands.append(query)
    cursor.execute(query)
    return True


def set_conn_limit(cursor, db, conn_limit):
    query = "ALTER DATABASE %s CONNECTION LIMIT %s" % (
            pg_quote_identifier(db, 'database'),
            conn_limit)
    executed_commands.append(query)
    cursor.execute(query)
    return True


def get_encoding_id(cursor, encoding):
    query = "SELECT pg_char_to_encoding(%(encoding)s) AS encoding_id;"
    cursor.execute(query, {'encoding': encoding})
    return cursor.fetchone()['encoding_id']


def get_db_info(cursor, db):
    query = """
    SELECT rolname AS owner,
    pg_encoding_to_char(encoding) AS encoding, encoding AS encoding_id,
    datcollate AS lc_collate, datctype AS lc_ctype, pg_database.datconnlimit AS conn_limit,
    spcname AS tablespace
    FROM pg_database
    JOIN pg_roles ON pg_roles.oid = pg_database.datdba
    JOIN pg_tablespace ON pg_tablespace.oid = pg_database.dattablespace
    WHERE datname = %(db)s
    """
    cursor.execute(query, {'db': db})
    return cursor.fetchone()


def db_exists(cursor, db):
    query = "SELECT * FROM pg_database WHERE datname=%(db)s"
    cursor.execute(query, {'db': db})
    return cursor.rowcount == 1


def db_delete(cursor, db):
    if db_exists(cursor, db):
        query = "DROP DATABASE %s" % pg_quote_identifier(db, 'database')
        executed_commands.append(query)
        cursor.execute(query)
        return True
    else:
        return False


def db_create(cursor, db, owner, template, encoding, lc_collate, lc_ctype, conn_limit, tablespace):
    params = dict(enc=encoding, collate=lc_collate, ctype=lc_ctype, conn_limit=conn_limit, tablespace=tablespace)
    if not db_exists(cursor, db):
        query_fragments = ['CREATE DATABASE %s' % pg_quote_identifier(db, 'database')]
        if owner:
            query_fragments.append('OWNER "%s"' % owner)
        if template:
            query_fragments.append('TEMPLATE %s' % pg_quote_identifier(template, 'database'))
        if encoding:
            query_fragments.append('ENCODING %(enc)s')
        if lc_collate:
            query_fragments.append('LC_COLLATE %(collate)s')
        if lc_ctype:
            query_fragments.append('LC_CTYPE %(ctype)s')
        if tablespace:
            query_fragments.append('TABLESPACE %s' % pg_quote_identifier(tablespace, 'tablespace'))
        if conn_limit:
            query_fragments.append("CONNECTION LIMIT %(conn_limit)s" % {"conn_limit": conn_limit})
        query = ' '.join(query_fragments)
        executed_commands.append(cursor.mogrify(query, params))
        cursor.execute(query, params)
        return True
    else:
        db_info = get_db_info(cursor, db)
        if (encoding and get_encoding_id(cursor, encoding) != db_info['encoding_id']):
            raise NotSupportedError(
                'Changing database encoding is not supported. '
                'Current encoding: %s' % db_info['encoding']
            )
        elif lc_collate and lc_collate != db_info['lc_collate']:
            raise NotSupportedError(
                'Changing LC_COLLATE is not supported. '
                'Current LC_COLLATE: %s' % db_info['lc_collate']
            )
        elif lc_ctype and lc_ctype != db_info['lc_ctype']:
            raise NotSupportedError(
                'Changing LC_CTYPE is not supported.'
                'Current LC_CTYPE: %s' % db_info['lc_ctype']
            )
        else:
            changed = False

            if owner and owner != db_info['owner']:
                changed = set_owner(cursor, db, owner)

            if conn_limit and conn_limit != str(db_info['conn_limit']):
                changed = set_conn_limit(cursor, db, conn_limit)

            if tablespace and tablespace != db_info['tablespace']:
                changed = set_tablespace(cursor, db, tablespace)

            return changed


def db_matches(cursor, db, owner, template, encoding, lc_collate, lc_ctype, conn_limit, tablespace):
    if not db_exists(cursor, db):
        return False
    else:
        db_info = get_db_info(cursor, db)
        if (encoding and get_encoding_id(cursor, encoding) != db_info['encoding_id']):
            return False
        elif lc_collate and lc_collate != db_info['lc_collate']:
            return False
        elif lc_ctype and lc_ctype != db_info['lc_ctype']:
            return False
        elif owner and owner != db_info['owner']:
            return False
        elif conn_limit and conn_limit != str(db_info['conn_limit']):
            return False
        elif tablespace and tablespace != db_info['tablespace']:
            return False
        else:
            return True


def db_dump(module, target, target_opts="",
            db=None,
            dump_extra_args=None,
            user=None,
            password=None,
            host=None,
            port=None,
            **kw):

    flags = login_flags(db, host, port, user, db_prefix=False)
    cmd = module.get_bin_path('pg_dump', True)
    comp_prog_path = None

    if os.path.splitext(target)[-1] == '.tar':
        flags.append(' --format=t')
    elif os.path.splitext(target)[-1] == '.pgc':
        flags.append(' --format=c')
    if os.path.splitext(target)[-1] == '.gz':
        if module.get_bin_path('pigz'):
            comp_prog_path = module.get_bin_path('pigz', True)
        else:
            comp_prog_path = module.get_bin_path('gzip', True)
    elif os.path.splitext(target)[-1] == '.bz2':
        comp_prog_path = module.get_bin_path('bzip2', True)
    elif os.path.splitext(target)[-1] == '.xz':
        comp_prog_path = module.get_bin_path('xz', True)

    cmd += "".join(flags)

    if dump_extra_args:
        cmd += " {0} ".format(dump_extra_args)

    if target_opts:
        cmd += " {0} ".format(target_opts)

    if comp_prog_path:
        # Use a fifo to be notified of an error in pg_dump
        # Using shell pipe has no way to return the code of the first command
        # in a portable way.
        fifo = os.path.join(module.tmpdir, 'pg_fifo')
        os.mkfifo(fifo)
        cmd = '{1} <{3} > {2} & {0} >{3}'.format(cmd, comp_prog_path, shlex_quote(target), fifo)
    else:
        cmd = '{0} > {1}'.format(cmd, shlex_quote(target))

    return do_with_password(module, cmd, password)


def db_restore(module, target, target_opts="",
               db=None,
               user=None,
               password=None,
               host=None,
               port=None,
               **kw):

    flags = login_flags(db, host, port, user)
    comp_prog_path = None
    cmd = module.get_bin_path('psql', True)

    if os.path.splitext(target)[-1] == '.sql':
        flags.append(' --file={0}'.format(target))

    elif os.path.splitext(target)[-1] == '.tar':
        flags.append(' --format=Tar')
        cmd = module.get_bin_path('pg_restore', True)

    elif os.path.splitext(target)[-1] == '.pgc':
        flags.append(' --format=Custom')
        cmd = module.get_bin_path('pg_restore', True)

    elif os.path.splitext(target)[-1] == '.gz':
        comp_prog_path = module.get_bin_path('zcat', True)

    elif os.path.splitext(target)[-1] == '.bz2':
        comp_prog_path = module.get_bin_path('bzcat', True)

    elif os.path.splitext(target)[-1] == '.xz':
        comp_prog_path = module.get_bin_path('xzcat', True)

    cmd += "".join(flags)
    if target_opts:
        cmd += " {0} ".format(target_opts)

    if comp_prog_path:
        env = os.environ.copy()
        if password:
            env = {"PGPASSWORD": password}
        p1 = subprocess.Popen([comp_prog_path, target], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p2 = subprocess.Popen(cmd, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, env=env)
        (stdout2, stderr2) = p2.communicate()
        p1.stdout.close()
        p1.wait()
        if p1.returncode != 0:
            stderr1 = p1.stderr.read()
            return p1.returncode, '', stderr1, 'cmd: ****'
        else:
            return p2.returncode, '', stderr2, 'cmd: ****'
    else:
        cmd = '{0} < {1}'.format(cmd, shlex_quote(target))

    return do_with_password(module, cmd, password)


def login_flags(db, host, port, user, db_prefix=True):
    """
    returns a list of connection argument strings each prefixed
    with a space and quoted where necessary to later be combined
    in a single shell string with `"".join(rv)`

    db_prefix determines if "--dbname" is prefixed to the db argument,
    since the argument was introduced in 9.3.
    """
    flags = []
    if db:
        if db_prefix:
            flags.append(' --dbname={0}'.format(shlex_quote(db)))
        else:
            flags.append(' {0}'.format(shlex_quote(db)))
    if host:
        flags.append(' --host={0}'.format(host))
    if port:
        flags.append(' --port={0}'.format(port))
    if user:
        flags.append(' --username={0}'.format(user))
    return flags


def do_with_password(module, cmd, password):
    env = {}
    if password:
        env = {"PGPASSWORD": password}
    executed_commands.append(cmd)
    rc, stderr, stdout = module.run_command(cmd, use_unsafe_shell=True, environ_update=env)
    return rc, stderr, stdout, cmd


def set_tablespace(cursor, db, tablespace):
    query = "ALTER DATABASE %s SET TABLESPACE %s" % (
            pg_quote_identifier(db, 'database'),
            pg_quote_identifier(tablespace, 'tablespace'))
    executed_commands.append(query)
    cursor.execute(query)
    return True

# ===========================================
# Module execution.
#


def main():
    argument_spec = pgutils.postgres_common_argument_spec()
    argument_spec.update(
        db=dict(type='str', required=True, aliases=['name']),
        owner=dict(type='str', default=''),
        template=dict(type='str', default=''),
        encoding=dict(type='str', default=''),
        lc_collate=dict(type='str', default=''),
        lc_ctype=dict(type='str', default=''),
        state=dict(type='str', default='present', choices=['absent', 'dump', 'present', 'restore']),
        target=dict(type='path', default=''),
        target_opts=dict(type='str', default=''),
        maintenance_db=dict(type='str', default="postgres"),
        session_role=dict(type='str'),
        conn_limit=dict(type='str', default=''),
        tablespace=dict(type='path', default=''),
        dump_extra_args=dict(type='str', default=None),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    db = module.params["db"]
    owner = module.params["owner"]
    template = module.params["template"]
    encoding = module.params["encoding"]
    lc_collate = module.params["lc_collate"]
    lc_ctype = module.params["lc_ctype"]
    target = module.params["target"]
    target_opts = module.params["target_opts"]
    state = module.params["state"]
    changed = False
    maintenance_db = module.params['maintenance_db']
    session_role = module.params["session_role"]
    conn_limit = module.params['conn_limit']
    tablespace = module.params['tablespace']
    dump_extra_args = module.params['dump_extra_args']

    raw_connection = state in ("dump", "restore")

    if not raw_connection:
        pgutils.ensure_required_libs(module)

    # To use defaults values, keyword arguments must be absent, so
    # check which values are empty and don't include in the **kw
    # dictionary
    params_map = {
        "login_host": "host",
        "login_user": "user",
        "login_password": "password",
        "port": "port",
        "ssl_mode": "sslmode",
        "ca_cert": "sslrootcert"
    }
    kw = dict((params_map[k], v) for (k, v) in iteritems(module.params)
              if k in params_map and v != '' and v is not None)

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"

    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    if target == "":
        target = "{0}/{1}.sql".format(os.getcwd(), db)
        target = os.path.expanduser(target)

    if not raw_connection:
        try:
            db_connection = psycopg2.connect(database=maintenance_db, **kw)

            # Enable autocommit so we can create databases
            if psycopg2.__version__ >= '2.4.2':
                db_connection.autocommit = True
            else:
                db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

        except TypeError as e:
            if 'sslrootcert' in e.args[0]:
                module.fail_json(msg='Postgresql server must be at least version 8.4 to support sslrootcert. Exception: {0}'.format(to_native(e)),
                                 exception=traceback.format_exc())
            module.fail_json(msg="unable to connect to database: %s" % to_native(e), exception=traceback.format_exc())

        except Exception as e:
            module.fail_json(msg="unable to connect to database: %s" % to_native(e), exception=traceback.format_exc())

        if session_role:
            try:
                cursor.execute('SET ROLE "%s"' % session_role)
            except Exception as e:
                module.fail_json(msg="Could not switch role: %s" % to_native(e), exception=traceback.format_exc())

    try:
        if module.check_mode:
            if state == "absent":
                changed = db_exists(cursor, db)
            elif state == "present":
                changed = not db_matches(cursor, db, owner, template, encoding, lc_collate, lc_ctype, conn_limit, tablespace)
            module.exit_json(changed=changed, db=db, executed_commands=executed_commands)

        if state == "absent":
            try:
                changed = db_delete(cursor, db)
            except SQLParseError as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())

        elif state == "present":
            try:
                changed = db_create(cursor, db, owner, template, encoding, lc_collate, lc_ctype, conn_limit, tablespace)
            except SQLParseError as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())

        elif state in ("dump", "restore"):
            method = state == "dump" and db_dump or db_restore
            try:
                if state == 'dump':
                    rc, stdout, stderr, cmd = method(module, target, target_opts, db, dump_extra_args, **kw)
                else:
                    rc, stdout, stderr, cmd = method(module, target, target_opts, db, **kw)

                if rc != 0:
                    module.fail_json(msg=stderr, stdout=stdout, rc=rc, cmd=cmd)
                else:
                    module.exit_json(changed=True, msg=stdout, stderr=stderr, rc=rc, cmd=cmd,
                                     executed_commands=executed_commands)
            except SQLParseError as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    except NotSupportedError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except SystemExit:
        # Avoid catching this on Python 2.4
        raise
    except Exception as e:
        module.fail_json(msg="Database query failed: %s" % to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=changed, db=db, executed_commands=executed_commands)


if __name__ == '__main__':
    main()
