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

try:
    from psycopg2.extras import DictCursor
except ImportError:
    # psycopg2 is checked by connect_to_db()
    # from ansible.module_utils.postgres
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.postgres import (
    connect_to_db,
    get_conn_params,
    postgres_common_argument_spec,
)
from ansible.module_utils._text import to_native

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

    ext = module.params["ext"]
    schema = module.params["schema"]
    state = module.params["state"]
    cascade = module.params["cascade"]
    changed = False

    conn_params = get_conn_params(module, module.params)
    db_connection = connect_to_db(module, conn_params, autocommit=True)
    cursor = db_connection.cursor(cursor_factory=DictCursor)

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

    except Exception as e:
        db_connection.close()
        module.fail_json(msg="Database query failed: %s" % to_native(e), exception=traceback.format_exc())

    db_connection.close()
    module.exit_json(changed=changed, db=module.params["db"], ext=ext, queries=executed_queries)


if __name__ == '__main__':
    main()
