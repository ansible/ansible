#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: postgresql_ext
short_description: Add or remove PostgreSQL extensions from a database
description:
- Add or remove PostgreSQL extensions from a database.
version_added: '1.9'
options:
  name:
    description:
    - Name of the extension to add or remove.
    required: true
    type: str
    aliases:
    - ext
  db:
    description:
    - Name of the database to add or remove the extension to/from.
    required: true
    type: str
    aliases:
    - login_db
  schema:
    description:
    - Name of the schema to add the extension to.
    version_added: '2.8'
    type: str
  session_role:
    description:
    - Switch to session_role after connecting.
    - The specified session_role must be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though the session_role were the one that had logged in originally.
    type: str
    version_added: '2.8'
  state:
    description:
    - The database extension state.
    default: present
    choices: [ absent, present ]
    type: str
  cascade:
    description:
    - Automatically install/remove any extensions that this extension depends on
      that are not already installed/removed (supported since PostgreSQL 9.6).
    type: bool
    default: no
    version_added: '2.8'
  login_unix_socket:
    description:
      - Path to a Unix domain socket for local connections.
    type: str
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
- The default authentication assumes that you are either logging in as
  or sudo'ing to the C(postgres) account on the host.
- This module uses I(psycopg2), a Python PostgreSQL database adapter.
- You must ensure that psycopg2 is installed on the host before using this module.
- If the remote host is the PostgreSQL server (which is the default case),
  then PostgreSQL must also be installed on the remote host.
- For Ubuntu-based systems, install the C(postgresql), C(libpq-dev),
  and C(python-psycopg2) packages on the remote host before using this module.
requirements: [ psycopg2 ]
author:
- Daniel Schep (@dschep)
- Thomas O'Donnell (@andytom)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Adds postgis extension to the database acme in the schema foo
  postgresql_ext:
    name: postgis
    db: acme
    schema: foo

- name: Removes postgis extension to the database acme
  postgresql_ext:
    name: postgis
    db: acme
    state: absent

- name: Adds earthdistance extension to the database template1 cascade
  postgresql_ext:
    name: earthdistance
    db: template1
    cascade: true

# In the example below, if earthdistance extension is installed,
# it will be removed too because it depends on cube:
- name: Removes cube extension from the database acme cascade
  postgresql_ext:
    name: cube
    db: acme
    cascade: yes
    state: absent
'''

RETURN = r'''
query:
  description: List of executed queries.
  returned: always
  type: list
  sample: ["DROP EXTENSION \"acme\""]

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
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native
from ansible.module_utils.database import pg_quote_identifier

executed_queries = []


class NotSupportedError(Exception):
    pass


# ===========================================
# PostgreSQL module specific support methods.
#

def ext_exists(cursor, ext):
    query = "SELECT * FROM pg_extension WHERE extname=%(ext)s"
    cursor.execute(query, {'ext': ext})
    return cursor.rowcount == 1


def ext_delete(cursor, ext, cascade):
    if ext_exists(cursor, ext):
        query = "DROP EXTENSION \"%s\"" % ext
        if cascade:
            query += " CASCADE"
        cursor.execute(query)
        executed_queries.append(query)
        return True
    else:
        return False


def ext_create(cursor, ext, schema, cascade):
    if not ext_exists(cursor, ext):
        query = "CREATE EXTENSION \"%s\"" % ext
        if schema:
            query += " WITH SCHEMA \"%s\"" % schema
        if cascade:
            query += " CASCADE"
        cursor.execute(query)
        executed_queries.append(query)
        return True
    else:
        return False

# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        db=dict(type="str", required=True, aliases=["login_db"]),
        ext=dict(type="str", required=True, aliases=["name"]),
        schema=dict(type="str"),
        state=dict(type="str", default="present", choices=["absent", "present"]),
        cascade=dict(type="bool", default=False),
        session_role=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg=missing_required_lib('psycopg2'), exception=PSYCOPG2_IMP_ERR)

    db = module.params["db"]
    ext = module.params["ext"]
    schema = module.params["schema"]
    state = module.params["state"]
    cascade = module.params["cascade"]
    sslrootcert = module.params["ca_cert"]
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
        "db": "database",
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
        module.fail_json(msg='psycopg2 must be at least 2.4.3 in order to user the ca_cert parameter')

    try:
        db_connection = psycopg2.connect(**kw)
        # Enable autocommit so we can create databases
        if psycopg2.__version__ >= '2.4.2':
            db_connection.autocommit = True
        else:
            db_connection.set_isolation_level(psycopg2
                                              .extensions
                                              .ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

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
            if state == "present":
                changed = not ext_exists(cursor, ext)
            elif state == "absent":
                changed = ext_exists(cursor, ext)
        else:
            if state == "absent":
                changed = ext_delete(cursor, ext, cascade)

            elif state == "present":
                changed = ext_create(cursor, ext, schema, cascade)
    except NotSupportedError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except Exception as e:
        module.fail_json(msg="Database query failed: %s" % to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=changed, db=db, ext=ext, queries=executed_queries)


if __name__ == '__main__':
    main()
