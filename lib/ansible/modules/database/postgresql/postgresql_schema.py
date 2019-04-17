#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: postgresql_schema
short_description: Add or remove PostgreSQL schema
description:
- Add or remove PostgreSQL schema.
version_added: '2.3'
options:
  name:
    description:
    - Name of the schema to add or remove.
    required: true
    type: str
    aliases:
    - schema
  database:
    description:
    - Name of the database to connect to and add or remove the schema.
    type: str
    default: postgres
    aliases:
    - db
    - login_db
  owner:
    description:
    - Name of the role to set as owner of the schema.
    type: str
  session_role:
    version_added: '2.8'
    description:
    - Switch to session_role after connecting.
    - The specified session_role must be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though the session_role
      were the one that had logged in originally.
    type: str
  state:
    description:
    - The schema state.
    type: str
    default: present
    choices: [ absent, present ]
  cascade_drop:
    description:
    - Drop schema with CASCADE to remove child objects.
    type: bool
    default: false
    version_added: '2.8'
  ssl_mode:
    description:
      - Determines whether or with what priority a secure SSL TCP/IP connection will be negotiated with the server.
      - See https://www.postgresql.org/docs/current/static/libpq-ssl.html for more information on the modes.
      - Default of C(prefer) matches libpq default.
    type: str
    default: prefer
    choices: [ allow, disable, prefer, require, verify-ca, verify-full ]
    version_added: '2.8'
  ca_cert:
    description:
      - Specifies the name of a file containing SSL certificate authority (CA) certificate(s).
      - If the file exists, the server's certificate will be verified to be signed by one of these authorities.
    type: str
    aliases: [ ssl_rootcert ]
    version_added: '2.8'
notes:
- This module uses I(psycopg2), a Python PostgreSQL database adapter.
- You must ensure that psycopg2 is installed on the host before using this module.
- If the remote host is the PostgreSQL server (which is the default case),
  then PostgreSQL must also be installed on the remote host.
- For Ubuntu-based systems, install the C(postgresql), C(libpq-dev),
  and C(python-psycopg2) packages on the remote host before using this module.
requirements: [ psycopg2 ]
author:
- Flavien Chantelot (@Dorn-) <contact@flavien.io>
- Thomas O'Donnell (@andytom)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Create a new schema with name acme in test database
  postgresql_schema:
    db: test
    name: acme

- name: Create a new schema acme with a user bob who will own it
  postgresql_schema:
    name: acme
    owner: bob

- name: Drop schema "acme" with cascade
  postgresql_schema:
    name: acme
    ensure: absent
    cascade_drop: yes
'''

RETURN = r'''
schema:
  description: Name of the schema.
  returned: success, changed
  type: str
  sample: "acme"
queries:
  description: List of executed queries.
  returned: always
  type: list
  sample: ["CREATE SCHEMA \"acme\""]
'''

import traceback

PSYCOPG2_IMP_ERR = None
try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    PSYCOPG2_IMP_ERR = traceback.format_exc()
    HAS_PSYCOPG2 = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.postgres import postgres_common_argument_spec
from ansible.module_utils.database import SQLParseError, pg_quote_identifier
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native

executed_queries = []


class NotSupportedError(Exception):
    pass


# ===========================================
# PostgreSQL module specific support methods.
#

def set_owner(cursor, schema, owner):
    query = "ALTER SCHEMA %s OWNER TO %s" % (
            pg_quote_identifier(schema, 'schema'),
            pg_quote_identifier(owner, 'role'))
    cursor.execute(query)
    executed_queries.append(query)
    return True


def get_schema_info(cursor, schema):
    query = ("SELECT schema_owner AS owner "
             "FROM information_schema.schemata "
             "WHERE schema_name = '%s'" % schema)
    cursor.execute(query)
    return cursor.fetchone()


def schema_exists(cursor, schema):
    query = ("SELECT schema_name FROM information_schema.schemata "
             "WHERE schema_name = '%s'" % schema)
    cursor.execute(query)
    return cursor.rowcount == 1


def schema_delete(cursor, schema, cascade):
    if schema_exists(cursor, schema):
        query = "DROP SCHEMA %s" % pg_quote_identifier(schema, 'schema')
        if cascade:
            query += " CASCADE"
        cursor.execute(query)
        executed_queries.append(query)
        return True
    else:
        return False


def schema_create(cursor, schema, owner):
    if not schema_exists(cursor, schema):
        query_fragments = ['CREATE SCHEMA %s' % pg_quote_identifier(schema, 'schema')]
        if owner:
            query_fragments.append('AUTHORIZATION %s' % pg_quote_identifier(owner, 'role'))
        query = ' '.join(query_fragments)
        cursor.execute(query)
        executed_queries.append(query)
        return True
    else:
        schema_info = get_schema_info(cursor, schema)
        if owner and owner != schema_info['owner']:
            return set_owner(cursor, schema, owner)
        else:
            return False


def schema_matches(cursor, schema, owner):
    if not schema_exists(cursor, schema):
        return False
    else:
        schema_info = get_schema_info(cursor, schema)
        if owner and owner != schema_info['owner']:
            return False
        else:
            return True

# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        login_user=dict(type="str", default="postgres"),
        login_password=dict(type="str", default="", no_log=True),
        login_host=dict(type="str", default=""),
        login_unix_socket=dict(type="str", default=""),
        port=dict(type="int", default=5432, aliases=["login_port"]),
        schema=dict(type="str", required=True, aliases=['name']),
        owner=dict(type="str", default=""),
        database=dict(type="str", default="postgres", aliases=["db", "login_db"]),
        cascade_drop=dict(type="bool", default=False),
        state=dict(type="str", default="present", choices=["absent", "present"]),
        ssl_mode=dict(type="str", default='prefer', choices=[
                      'disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']),
        ca_cert=dict(type="str", default=None, aliases=['ssl_rootcert']),
        session_role=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg=missing_required_lib('psycopg2'), exception=PSYCOPG2_IMP_ERR)

    schema = module.params["schema"]
    owner = module.params["owner"]
    state = module.params["state"]
    sslrootcert = module.params["ca_cert"]
    cascade_drop = module.params["cascade_drop"]
    session_role = module.params["session_role"]
    changed = False

    # To use defaults values, keyword arguments must be absent, so
    # check which values are empty and don't include in the **kw
    # dictionary
    params_map = {
        "login_host": "host",
        "login_user": "user",
        "login_password": "password",
        "port": "port",
        "database": "database",
        "ssl_mode": "sslmode",
        "ca_cert": "sslrootcert"
    }
    kw = dict((params_map[k], v) for (k, v) in iteritems(module.params)
              if k in params_map and v != "" and v is not None)

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    if psycopg2.__version__ < '2.4.3' and sslrootcert is not None:
        module.fail_json(
            msg='psycopg2 must be at least 2.4.3 in order to user the ca_cert parameter')

    try:
        db_connection = psycopg2.connect(**kw)
        # Enable autocommit so we can create databases
        if psycopg2.__version__ >= '2.4.2':
            db_connection.autocommit = True
        else:
            db_connection.set_isolation_level(psycopg2
                                              .extensions
                                              .ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = db_connection.cursor(
            cursor_factory=psycopg2.extras.DictCursor)

    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(
                msg='Postgresql server must be at least version 8.4 to support sslrootcert')
        module.fail_json(msg="unable to connect to database: %s" % to_native(e), exception=traceback.format_exc())

    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e), exception=traceback.format_exc())

    if session_role:
        try:
            cursor.execute('SET ROLE %s' % pg_quote_identifier(session_role, 'role'))
        except Exception as e:
            module.fail_json(msg="Could not switch role: %s" % to_native(e), exception=traceback.format_exc())

    try:
        if module.check_mode:
            if state == "absent":
                changed = not schema_exists(cursor, schema)
            elif state == "present":
                changed = not schema_matches(cursor, schema, owner)
            module.exit_json(changed=changed, schema=schema)

        if state == "absent":
            try:
                changed = schema_delete(cursor, schema, cascade_drop)
            except SQLParseError as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())

        elif state == "present":
            try:
                changed = schema_create(cursor, schema, owner)
            except SQLParseError as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except NotSupportedError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except SystemExit:
        # Avoid catching this on Python 2.4
        raise
    except Exception as e:
        module.fail_json(msg="Database query failed: %s" % to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=changed, schema=schema, queries=executed_queries)


if __name__ == '__main__':
    main()
