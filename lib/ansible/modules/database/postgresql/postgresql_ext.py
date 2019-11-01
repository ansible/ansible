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
  version:
    description:
      - Extension version to add or update to. Has effect with I(state=present) only.
      - If not specified, the latest extension version will be created.
      - It can't downgrade an extension version.
        When version downgrade is needed, remove the extension and create new one with appropriate version.
      - Set I(version=latest) to update the extension to the latest available version.
    type: str
    version_added: '2.9'
seealso:
- name: PostgreSQL extensions
  description: General information about PostgreSQL extensions.
  link: https://www.postgresql.org/docs/current/external-extensions.html
- name: CREATE EXTENSION reference
  description: Complete reference of the CREATE EXTENSION command documentation.
  link: https://www.postgresql.org/docs/current/sql-createextension.html
- name: ALTER EXTENSION reference
  description: Complete reference of the ALTER EXTENSION command documentation.
  link: https://www.postgresql.org/docs/current/sql-alterextension.html
- name: DROP EXTENSION reference
  description: Complete reference of the DROP EXTENSION command documentation.
  link: https://www.postgresql.org/docs/current/sql-droppublication.html
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
- Sandro Santilli (@strk)
- Andrew Klychkov (@Andersson007)
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

- name: Create extension foo of version 1.2 or update it if it's already created
  postgresql_ext:
    db: acme
    name: foo
    version: 1.2

- name: Assuming extension foo is created, update it to the latest version
  postgresql_ext:
    db: acme
    name: foo
    version: latest
'''

RETURN = r'''
query:
  description: List of executed queries.
  returned: always
  type: list
  sample: ["DROP EXTENSION \"acme\""]

'''

import traceback

from distutils.version import LooseVersion

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


def ext_update_version(cursor, ext, version):
    """Update extension version.

    Return True if success.

    Args:
      cursor (cursor) -- cursor object of psycopg2 library
      ext (str) -- extension name
      version (str) -- extension version
    """
    if version != 'latest':
        query = ("ALTER EXTENSION \"%s\" UPDATE TO '%s'" % (ext, version))
    else:
        query = ("ALTER EXTENSION \"%s\" UPDATE" % ext)
    cursor.execute(query)
    executed_queries.append(query)
    return True


def ext_create(cursor, ext, schema, cascade, version):
    query = "CREATE EXTENSION \"%s\"" % ext
    if schema:
        query += " WITH SCHEMA \"%s\"" % schema
    if version:
        query += " VERSION '%s'" % version
    if cascade:
        query += " CASCADE"
    cursor.execute(query)
    executed_queries.append(query)
    return True


def ext_get_versions(cursor, ext):
    """
    Get the current created extension version and available versions.

    Return tuple (current_version, [list of available versions]).

    Note: the list of available versions contains only versions
          that higher than the current created version.
          If the extension is not created, this list will contain all
          available versions.

    Args:
      cursor (cursor) -- cursor object of psycopg2 library
      ext (str) -- extension name
    """

    # 1. Get the current extension version:
    query = ("SELECT extversion FROM pg_catalog.pg_extension "
             "WHERE extname = '%s'" % ext)

    current_version = '0'
    cursor.execute(query)
    res = cursor.fetchone()
    if res:
        current_version = res[0]

    # 2. Get available versions:
    query = ("SELECT version FROM pg_available_extension_versions "
             "WHERE name = '%s'" % ext)
    cursor.execute(query)
    res = cursor.fetchall()

    available_versions = []
    if res:
        # Make the list of available versions:
        for line in res:
            if LooseVersion(line[0]) > LooseVersion(current_version):
                available_versions.append(line['version'])

    if current_version == '0':
        current_version = False

    return (current_version, available_versions)

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
        version=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    ext = module.params["ext"]
    schema = module.params["schema"]
    state = module.params["state"]
    cascade = module.params["cascade"]
    version = module.params["version"]
    changed = False

    if version and state == 'absent':
        module.warn("Parameter version is ignored when state=absent")

    conn_params = get_conn_params(module, module.params)
    db_connection = connect_to_db(module, conn_params, autocommit=True)
    cursor = db_connection.cursor(cursor_factory=DictCursor)

    try:
        # Get extension info and available versions:
        curr_version, available_versions = ext_get_versions(cursor, ext)

        if state == "present":
            if version == 'latest':
                if available_versions:
                    version = available_versions[-1]
                else:
                    version = ''

            if version:
                # If the specific version is passed and it is not available for update:
                if version not in available_versions:
                    if not curr_version:
                        module.fail_json(msg="Passed version '%s' is not available" % version)

                    elif LooseVersion(curr_version) == LooseVersion(version):
                        changed = False

                    else:
                        module.fail_json(msg="Passed version '%s' is lower than "
                                             "the current created version '%s' or "
                                             "the passed version is not available" % (version, curr_version))

                # If the specific version is passed and it is higher that the current version:
                if curr_version and version:
                    if LooseVersion(curr_version) < LooseVersion(version):
                        if module.check_mode:
                            changed = True
                        else:
                            changed = ext_update_version(cursor, ext, version)

                    # If the specific version is passed and it is created now:
                    if curr_version == version:
                        changed = False

                # If the ext doesn't exist and installed:
                elif not curr_version and available_versions:
                    if module.check_mode:
                        changed = True
                    else:
                        changed = ext_create(cursor, ext, schema, cascade, version)

            # If version is not passed:
            else:
                if not curr_version:
                    # If the ext doesn't exist and it's installed:
                    if available_versions:
                        if module.check_mode:
                            changed = True
                        else:
                            changed = ext_create(cursor, ext, schema, cascade, version)

                    # If the ext doesn't exist and not installed:
                    else:
                        module.fail_json(msg="Extension %s is not installed" % ext)

        elif state == "absent":
            if curr_version:
                if module.check_mode:
                    changed = True
                else:
                    changed = ext_delete(cursor, ext, cascade)
            else:
                changed = False

    except Exception as e:
        db_connection.close()
        module.fail_json(msg="Database query failed: %s" % to_native(e), exception=traceback.format_exc())

    db_connection.close()
    module.exit_json(changed=changed, db=module.params["db"], ext=ext, queries=executed_queries)


if __name__ == '__main__':
    main()
