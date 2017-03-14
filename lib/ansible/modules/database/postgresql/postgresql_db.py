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

ANSIBLE_METADATA = {'metadata_version': '1.0',
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
    default: null
  owner:
    description:
      - Name of the role to set as owner of the database
    required: false
    default: null
  template:
    description:
      - Template used to create the database
    required: false
    default: null
  encoding:
    description:
      - Encoding of the database
    required: false
    default: null
  lc_collate:
    description:
      - Collation order (LC_COLLATE) to use in the database. Must match collation order of template database unless C(template0) is used as template.
    required: false
    default: null
  lc_ctype:
    description:
      - Character classification (LC_CTYPE) to use in the database (e.g. lower, upper, ...) Must match LC_CTYPE of template database unless C(template0) is used as template.
    required: false
    default: null
  state:
    description:
      - The database state
    required: false
    default: present
    choices: [ "present", "absent" ]
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
'''

HAS_PSYCOPG2 = False
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    pass
else:
    HAS_PSYCOPG2 = True
from ansible.module_utils.six import iteritems

import traceback

import ansible.module_utils.postgres as pgutils
from ansible.module_utils.database import SQLParseError, pg_quote_identifier
from ansible.module_utils.basic import get_exception, AnsibleModule


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
        state=dict(default="present", choices=["absent", "present"]),
    ))


    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode = True
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg="the python psycopg2 module is required")

    db = module.params["db"]
    port = module.params["port"]
    owner = module.params["owner"]
    template = module.params["template"]
    encoding = module.params["encoding"]
    lc_collate = module.params["lc_collate"]
    lc_ctype = module.params["lc_ctype"]
    state = module.params["state"]
    sslrootcert = module.params["ssl_rootcert"]
    changed = False

    # To use defaults values, keyword arguments must be absent, so
    # check which values are empty and don't include in the **kw
    # dictionary
    params_map = {
        "login_host":"host",
        "login_user":"user",
        "login_password":"password",
        "port":"port",
        "ssl_mode":"sslmode",
        "ssl_rootcert":"sslrootcert"
    }
    kw = dict( (params_map[k], v) for (k, v) in iteritems(module.params)
              if k in params_map and v != '' and v is not None)

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    try:
        pgutils.ensure_libs(sslrootcert=module.params.get('ssl_rootcert'))
        db_connection = psycopg2.connect(database="postgres", **kw)
        # Enable autocommit so we can create databases
        if psycopg2.__version__ >= '2.4.2':
            db_connection.autocommit = True
        else:
            db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    except pgutils.LibraryError:
        e = get_exception()
        module.fail_json(msg="unable to connect to database: {0}".format(str(e)), exception=traceback.format_exc())

    except TypeError:
        e = get_exception()
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least version 8.4 to support sslrootcert. Exception: {0}'.format(e), exception=traceback.format_exc())
        module.fail_json(msg="unable to connect to database: %s" % e, exception=traceback.format_exc())

    except Exception:
        e = get_exception()
        module.fail_json(msg="unable to connect to database: %s" % e, exception=traceback.format_exc())

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
            except SQLParseError:
                e = get_exception()
                module.fail_json(msg=str(e))

        elif state == "present":
            try:
                changed = db_create(cursor, db, owner, template, encoding, lc_collate, lc_ctype)
            except SQLParseError:
                e = get_exception()
                module.fail_json(msg=str(e))
    except NotSupportedError:
        e = get_exception()
        module.fail_json(msg=str(e))
    except SystemExit:
        # Avoid catching this on Python 2.4
        raise
    except Exception:
        e = get_exception()
        module.fail_json(msg="Database query failed: %s" % e)

    module.exit_json(changed=changed, db=db)

if __name__ == '__main__':
    main()
