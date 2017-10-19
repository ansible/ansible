#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: postgresql_publication
short_description: Add or remove PostgreSQL publication from a remote host
description:
   - Add or remove PostgreSQL publication from a remote host.
version_added: "2.5"
options:
  name:
    description:
      - Name of the publication to add or remove.
    required: true
    default: null
  database:
    description:
      - Name of the database to connect to.
    required: false
    default: postgres
  login_user:
    description:
      - The username used to authenticate with.
    required: false
    default: null
  login_password:
    description:
      - The password used to authenticate with.
    required: false
    default: null
  login_host:
    description:
      - Host running the database.
    required: false
    default: localhost
  login_unix_socket:
    description:
      - Path to a Unix domain socket for local connections.
    required: false
    default: null
  tables:
    description:
      - List of the tables to target for publication.
    required: false
    default: null
  port:
    description:
      - Database port to connect to.
    required: false
    default: 5432
  state:
    description:
      - The publication state.
    required: false
    default: present
    choices: [ "present", "absent" ]
notes:
   - This module uses I(psycopg2), a Python PostgreSQL database adapter. You must ensure that psycopg2 is installed on
     the host before using this module. If the remote host is the PostgreSQL server (which is the default case),
     then PostgreSQL must also be installed on the remote host. For Ubuntu-based systems, install the C(postgresql),
     C(libpq-dev), and C(python-psycopg2) packages on the remote host before
     using this module.
   - PostgreSQL version should be C(10.0) or greater.
requirements: [ psycopg2 ]
author: "Loic Blot <loic.blot@unix-experience.fr>"
'''

EXAMPLES = '''
# Create a new publication with name "acme" targeting all tables
- postgresql_publication:
    name: acme

# Create a new publication "acme" publishing only prices and vehicles tables.
- postgresql_publication:
    name: acme
    tables:
      - prices
      - vehicles

'''

RETURN = '''
publication:
    description: Name of the publication
    returned: success, changed
    type: string
    sample: "acme"
'''

import traceback

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    postgresqldb_found = False
else:
    postgresqldb_found = True

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import SQLParseError, pg_quote_identifier
from ansible.module_utils._text import to_native


class NotSupportedError(Exception):
    pass


# ===========================================
# PostgreSQL module specific support methods.
#
def get_publication_info(cursor, publication):
    query = """
    SELECT pubname AS name, pubowner AS owner, puballtables AS alltables, pubinsert, pubupdate, pubdelete
    FROM pg_publication
    WHERE pubname = %(publication)s
    """
    cursor.execute(query, {'publication': publication})
    cur_result = cursor.fetchone()
    if cur_result is None:
        return None

    result = {
        "name": cur_result['name'],
        "owner": cur_result['owner'],
        "alltables": cur_result['alltables'],
        "insert": cur_result['pubinsert'],
        "update": cur_result['pubupdate'],
        "delete": cur_result['pubdelete'],
        "tables": []
    }

    if result['alltables'] == 't':
        return result

    query = """
    SELECT schemaname, tablename FROM pg_publication_tables WHERE pubname = %(publication)s
    """
    cursor.execute(query, {'publication': publication})
    result['tables'] = cursor.fetchall()
    return result


def publication_exists(cursor, publication):
    query = "SELECT pubname FROM pg_publication WHERE pubname = %(publication)s"
    cursor.execute(query, {'publication': publication})
    return cursor.rowcount == 1


def publication_delete(cursor, publication):
    if publication_exists(cursor, publication):
        query = "DROP PUBLICATION %s" % pg_quote_identifier(publication, 'publication')
        cursor.execute(query)
        return True
    else:
        return False


def publication_modify_tables(cursor, publication, tables):
    if not publication_exists(cursor, publication):
        raise AssertionError("Modifying inexistant publication.")

    table_quoted_list = []
    for table in tables:
        table_quoted_list.append('%s' % pg_quote_identifier(table, 'table'))

    cursor.execute("ALTER PUBLICATION %s SET TABLE %s" % (pg_quote_identifier(publication, 'publication'),
                   ', '.join(table_quoted_list)))
    return True


def publication_create(cursor, publication, tables):
    if not publication_exists(cursor, publication):
        query_fragments = ['CREATE PUBLICATION %s FOR' % pg_quote_identifier(publication, 'publication')]
        if tables:
            table_quoted_list = []
            for table in tables:
                table_quoted_list.append('%s' % pg_quote_identifier(table, 'table'))
                query_fragments.append('TABLE %s' % ', '.join(table_quoted_list))
        else:
            query_fragments.append('ALL TABLES')
        query = ' '.join(query_fragments)
        cursor.execute(query)
        return True
    else:
        publication_info = get_publication_info(cursor, publication)
        # If publication switch from targeted tables to all tables (or invert), recreate it
        if publication_info['alltables'] is True and not tables or publication_info['alltables'] is True and not tables:
            publication_delete(cursor, publication)
            return publication_create(cursor, publication, tables)

        return publication_modify_tables(cursor, publication, tables)


def publication_matches(cursor, publication, owner):
    if not publication_exists(cursor, publication):
        return False
    else:
        publication_info = get_publication_info(cursor, publication)
        if owner and owner != publication_info['owner']:
            return False
        else:
            return True

# ===========================================
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default="postgres"),
            login_password=dict(default="", no_log=True),
            login_host=dict(default=""),
            login_unix_socket=dict(default=""),
            port=dict(default="5432"),
            name=dict(required=True),
            database=dict(default="postgres"),
            state=dict(default="present", choices=["absent", "present"]),
            tables=dict(default=None, type="list")
        ),
        supports_check_mode=True
    )

    if not postgresqldb_found:
        module.fail_json(msg="the python psycopg2 module is required")

    publication = module.params["name"]
    state = module.params["state"]
    database = module.params["database"]
    tables = module.params["tables"]
    changed = False

    # To use defaults values, keyword arguments must be absent, so
    # check which values are empty and don't include in the **kw
    # dictionary
    params_map = {
        "login_host": "host",
        "login_user": "user",
        "login_password": "password",
        "port": "port"
    }
    kw = dict((params_map[k], v) for (k, v) in module.params.items()
              if k in params_map and v != '')

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    try:
        db_connection = psycopg2.connect(database=database, **kw)
        # Enable autocommit so we can create databases
        if psycopg2.__version__ >= '2.4.2':
            db_connection.autocommit = True
        else:
            db_connection.set_isolation_level(psycopg2
                                              .extensions
                                              .ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = db_connection.cursor(
            cursor_factory=psycopg2.extras.DictCursor)
    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e), exception=traceback.format_exc())

    current_version = cursor.connection.server_version
    if current_version < 100000:
        module.fail_json(msg="PostgreSQL server version should be 10.0 or greater")

    try:
        if module.check_mode:
            if state == "absent":
                changed = not publication_exists(cursor, publication)
            elif state == "present":
                changed = not publication_matches(cursor, publication, tables)
            module.exit_json(changed=changed, publication=publication)

        if state == "absent":
            try:
                changed = publication_delete(cursor, publication)
            except SQLParseError as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())

        elif state == "present":
            try:
                changed = publication_create(cursor, publication, tables)
            except SQLParseError as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except NotSupportedError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except Exception as e:
        module.fail_json(msg="Database query failed: %s" % to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=changed, publication=publication)


if __name__ == '__main__':
    main()
