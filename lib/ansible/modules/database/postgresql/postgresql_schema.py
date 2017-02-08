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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: postgresql_schema
short_description: Add or remove PostgreSQL schema from a remote host
description:
   - Add or remove PostgreSQL schema from a remote host.
version_added: "2.3"
options:
  name:
    description:
      - Name of the schema to add or remove.
    required: true
    default: null
  database:
    description:
      - Name of the database to connect to.
    required: false
    default: postgres
  owner:
    description:
      - Name of the role to set as owner of the schema.
    required: false
    default: null
  state:
    description:
      - The schema state.
    required: false
    default: present
    choices: [ "present", "absent" ]
requirements: [ psycopg2 ]
author: "Flavien Chantelot <contact@flavien.io>"
extends_documentation_fragment:
- postgres
'''

EXAMPLES = '''
# Create a new schema with name "acme"
- postgresql_schema:
    name: acme

# Create a new schema "acme" with a user "bob" who will own it
- postgresql_schema:
    name: acme
    owner: bob

'''

RETURN = '''
schema:
    description: Name of the schema
    returned: success, changed
    type: string
    sample: "acme"
'''


try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    postgresqldb_found = False
else:
    postgresqldb_found = True

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
    return True

def get_schema_info(cursor, schema):
    query = """
    SELECT schema_owner AS owner
    FROM information_schema.schemata
    WHERE schema_name = %(schema)s
    """
    cursor.execute(query, {'schema': schema})
    return cursor.fetchone()

def schema_exists(cursor, schema):
    query = "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %(schema)s"
    cursor.execute(query, {'schema': schema})
    return cursor.rowcount == 1

def schema_delete(cursor, schema):
    if schema_exists(cursor, schema):
        query = "DROP SCHEMA %s" % pg_quote_identifier(schema, 'schema')
        cursor.execute(query)
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
    argument_spec = pgutils.postgres_common_argument_spec()
    argument_spec.update(dict(
        schema=dict(required=True, aliases=['name']),
        owner=dict(default=""),
        database=dict(default="postgres"),
        state=dict(default="present", choices=["absent", "present"]),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode = True
    )

    if not postgresqldb_found:
        module.fail_json(msg="the python psycopg2 module is required")

    schema = module.params["schema"]
    owner = module.params["owner"]
    state = module.params["state"]
    database = module.params["database"]
    changed = False

    kw = pgutils.params_to_kwmap(module)

    db_connection = pgutils.postgres_conn(module, database=database, kw=kw, enable_autocommit=True)
    cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        if module.check_mode:
            if state == "absent":
                changed = not schema_exists(cursor, schema)
            elif state == "present":
                changed = not schema_matches(cursor, schema, owner)
            module.exit_json(changed=changed, schema=schema)

        if state == "absent":
            try:
                changed = schema_delete(cursor, schema)
            except SQLParseError:
                e = get_exception()
                module.fail_json(msg=str(e))

        elif state == "present":
            try:
                changed = schema_create(cursor, schema, owner)
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
        module.fail_json(msg="Database query failed: %s" %(text, str(e)))

    module.exit_json(changed=changed, schema=schema)

# import module snippets
from ansible.module_utils.basic import AnsibleModule,get_exception
import ansible.module_utils.postgres as pgutils
from ansible.module_utils.database import pg_quote_identifier

if __name__ == '__main__':
    main()
