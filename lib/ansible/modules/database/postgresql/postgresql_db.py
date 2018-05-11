#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: postgresql_db
short_description: Add or remove PostgreSQL databases from a remote host.
description:
   - Add or remove PostgreSQL databases from a remote host.
version_added: "0.6"
options:
  name:
    description:
      - name of the database to add or remove
    required: true
    aliases: [ db ]
  owner:
    description:
      - Name of the role to set as owner of the database
  template:
    description:
      - Template used to create the database
  encoding:
    description:
      - Encoding of the database
  lc_collate:
    description:
      - Collation order (LC_COLLATE) to use in the database. Must match collation order of template database unless C(template0) is used as template.
  lc_ctype:
    description:
      - Character classification (LC_CTYPE) to use in the database (e.g. lower, upper, ...) Must match LC_CTYPE of template database unless C(template0)
        is used as template.
  state:
    description: |
        The database state. present implies that the database should be created if necessary.
        absent implies that the database should be removed if present.
        dump requires a target definition to which the database will be backed up.
        (Added in 2.4) restore also requires a target definition from which the database will be restored.
        (Added in 2.4) The format of the backup will be detected based on the target name.
        Supported compression formats for dump and restore are: .bz2, .gz, and .xz
        Supported formats for dump and restore are: .sql and .tar
    default: present
    choices: [ "present", "absent", "dump", "restore" ]
  target:
    version_added: "2.4"
    description:
      - File to back up or restore from. Used when state is "dump" or "restore"
  target_opts:
    version_added: "2.4"
    description:
      - Further arguments for pg_dump or pg_restore. Used when state is "dump" or "restore"
  maintenance_db:
    version_added: "2.5"
    description:
      - The value specifies the initial database (which is also called as maintenance DB) that Ansible connects to.
    default: postgres
author: "Ansible Core Team"
extends_documentation_fragment:
- postgres
'''

EXAMPLES = '''
# Create a new database with name "acme"
- postgresql_db:
    name: acme

# Create a new database with name "acme" and specific encoding and locale
# settings. If a template different from "template0" is specified, encoding
# and locale settings must match those of the template.
- postgresql_db:
    name: acme
    encoding: UTF-8
    lc_collate: de_DE.UTF-8
    lc_ctype: de_DE.UTF-8
    template: template0

# Dump an existing database to a file
- postgresql_db:
    name: acme
    state: dump
    target: /tmp/acme.sql

# Dump an existing database to a file (with compression)
- postgresql_db:
    name: acme
    state: dump
    target: /tmp/acme.sql.gz

# Dump a single schema for an existing database
- postgresql_db:
    name: acme
    state: dump
    target: /tmp/acme.sql
    target_opts: "-n public"
'''

import os
import pipes
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
from ansible.module_utils._text import to_native


class NotSupportedError(Exception):
    pass


# ===========================================
# PostgreSQL module specific support methods.
#

def set_owner(cursor, db, owner):
    query = "ALTER DATABASE %s OWNER TO %s" % (
            pg_quote_identifier(db, 'database'),
            pg_quote_identifier(owner, 'role'))
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
    datcollate AS lc_collate, datctype AS lc_ctype
    FROM pg_database JOIN pg_roles ON pg_roles.oid = pg_database.datdba
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
        cursor.execute(query)
        return True
    else:
        return False


def db_create(cursor, db, owner, template, encoding, lc_collate, lc_ctype):
    params = dict(enc=encoding, collate=lc_collate, ctype=lc_ctype)
    if not db_exists(cursor, db):
        query_fragments = ['CREATE DATABASE %s' % pg_quote_identifier(db, 'database')]
        if owner:
            query_fragments.append('OWNER %s' % pg_quote_identifier(owner, 'role'))
        if template:
            query_fragments.append('TEMPLATE %s' % pg_quote_identifier(template, 'database'))
        if encoding:
            query_fragments.append('ENCODING %(enc)s')
        if lc_collate:
            query_fragments.append('LC_COLLATE %(collate)s')
        if lc_ctype:
            query_fragments.append('LC_CTYPE %(ctype)s')
        query = ' '.join(query_fragments)
        cursor.execute(query, params)
        return True
    else:
        db_info = get_db_info(cursor, db)
        if (encoding and
                get_encoding_id(cursor, encoding) != db_info['encoding_id']):
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
        elif owner and owner != db_info['owner']:
            return set_owner(cursor, db, owner)
        else:
            return False


def db_matches(cursor, db, owner, template, encoding, lc_collate, lc_ctype):
    if not db_exists(cursor, db):
        return False
    else:
        db_info = get_db_info(cursor, db)
        if (encoding and
                get_encoding_id(cursor, encoding) != db_info['encoding_id']):
            return False
        elif lc_collate and lc_collate != db_info['lc_collate']:
            return False
        elif lc_ctype and lc_ctype != db_info['lc_ctype']:
            return False
        elif owner and owner != db_info['owner']:
            return False
        else:
            return True


def db_dump(module, target, target_opts="",
            db=None,
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
    if target_opts:
        cmd += " {0} ".format(target_opts)

    if comp_prog_path:
        cmd = '{0}|{1} > {2}'.format(cmd, comp_prog_path, pipes.quote(target))
    else:
        cmd = '{0} > {1}'.format(cmd, pipes.quote(target))

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
        cmd = '{0} < {1}'.format(cmd, pipes.quote(target))

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
            flags.append(' --dbname={0}'.format(pipes.quote(db)))
        else:
            flags.append(' {0}'.format(pipes.quote(db)))
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
    rc, stderr, stdout = module.run_command(cmd, use_unsafe_shell=True, environ_update=env)
    return rc, stderr, stdout, cmd

# ===========================================
# Module execution.
#


def main():
    argument_spec = pgutils.postgres_common_argument_spec()
    argument_spec.update(dict(
        db=dict(required=True, aliases=['name']),
        owner=dict(default=""),
        template=dict(default=""),
        encoding=dict(default=""),
        lc_collate=dict(default=""),
        lc_ctype=dict(default=""),
        state=dict(default="present", choices=["absent", "present", "dump", "restore"]),
        target=dict(default="", type="path"),
        target_opts=dict(default=""),
        maintenance_db=dict(default="postgres"),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg="the python psycopg2 module is required")

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

    # To use defaults values, keyword arguments must be absent, so
    # check which values are empty and don't include in the **kw
    # dictionary
    params_map = {
        "login_host": "host",
        "login_user": "user",
        "login_password": "password",
        "port": "port",
        "ssl_mode": "sslmode",
        "ssl_rootcert": "sslrootcert"
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

    try:
        pgutils.ensure_libs(sslrootcert=module.params.get('ssl_rootcert'))
        db_connection = psycopg2.connect(database=maintenance_db, **kw)

        # Enable autocommit so we can create databases
        if psycopg2.__version__ >= '2.4.2':
            db_connection.autocommit = True
        else:
            db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    except pgutils.LibraryError as e:
        module.fail_json(msg="unable to connect to database: {0}".format(to_native(e)), exception=traceback.format_exc())

    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least version 8.4 to support sslrootcert. Exception: {0}'.format(to_native(e)),
                             exception=traceback.format_exc())
        module.fail_json(msg="unable to connect to database: %s" % to_native(e), exception=traceback.format_exc())

    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e), exception=traceback.format_exc())

    try:
        if module.check_mode:
            if state == "absent":
                changed = db_exists(cursor, db)
            elif state == "present":
                changed = not db_matches(cursor, db, owner, template, encoding, lc_collate, lc_ctype)
            module.exit_json(changed=changed, db=db)

        if state == "absent":
            try:
                changed = db_delete(cursor, db)
            except SQLParseError as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())

        elif state == "present":
            try:
                changed = db_create(cursor, db, owner, template, encoding, lc_collate, lc_ctype)
            except SQLParseError as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())

        elif state in ("dump", "restore"):
            method = state == "dump" and db_dump or db_restore
            try:
                rc, stdout, stderr, cmd = method(module, target, target_opts, db, **kw)
                if rc != 0:
                    module.fail_json(msg=stderr, stdout=stdout, rc=rc, cmd=cmd)
                else:
                    module.exit_json(changed=True, msg=stdout, stderr=stderr, rc=rc, cmd=cmd)
            except SQLParseError as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    except NotSupportedError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except SystemExit:
        # Avoid catching this on Python 2.4
        raise
    except Exception as e:
        module.fail_json(msg="Database query failed: %s" % to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=changed, db=db)

if __name__ == '__main__':
    main()
