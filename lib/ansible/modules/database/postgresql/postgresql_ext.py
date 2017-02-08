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
module: postgresql_ext
short_description: Add or remove PostgreSQL extensions from a database.
description:
   - Add or remove PostgreSQL extensions from a database.
version_added: "1.9"
options:
  name:
    description:
      - name of the extension to add or remove
    required: true
    default: null
  db:
    description:
      - name of the database to add or remove the extension to/from
    required: true
    default: null
  state:
    description:
      - The database extension state
    required: false
    default: present
    choices: [ "present", "absent" ]
requirements: [ psycopg2 ]
author: "Daniel Schep (@dschep)"
extends_documentation_fragment:
- postgres
'''

EXAMPLES = '''
# Adds postgis to the database "acme"
- postgresql_ext:
    name: postgis
    db: acme
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

def ext_exists(cursor, ext):
    query = "SELECT * FROM pg_extension WHERE extname=%(ext)s"
    cursor.execute(query, {'ext': ext})
    return cursor.rowcount == 1

def ext_delete(cursor, ext):
    if ext_exists(cursor, ext):
        query = "DROP EXTENSION \"%s\"" % ext
        cursor.execute(query)
        return True
    else:
        return False

def ext_create(cursor, ext):
    if not ext_exists(cursor, ext):
        query = 'CREATE EXTENSION "%s"' % ext
        cursor.execute(query)
        return True
    else:
        return False

# ===========================================
# Module execution.
#

def main():
    argument_spec = pgutils.postgres_common_argument_spec()
    argument_spec.update(dict(
        db=dict(required=True),
        ext=dict(required=True, aliases=['name']),
        state=dict(default="present", choices=["absent", "present"]),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode = True
    )

    if not postgresqldb_found:
        module.fail_json(msg="the python psycopg2 module is required")

    db = module.params["db"]
    ext = module.params["ext"]
    port = module.params["port"]
    state = module.params["state"]
    changed = False

    kw = pgutils.params_to_kwmap(module)

    db_connection = pgutils.postgres_conn(module, database=db, kw=kw, enable_autocommit=True)
    cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        if module.check_mode:
            if state == "present":
                changed = not ext_exists(cursor, ext)
            elif state == "absent":
                changed = ext_exists(cursor, ext)
        else:
            if state == "absent":
                changed = ext_delete(cursor, ext)

            elif state == "present":
                changed = ext_create(cursor, ext)
    except NotSupportedError:
        e = get_exception()
        module.fail_json(msg=str(e))
    except Exception:
        e = get_exception()
        module.fail_json(msg="Database query failed: %s" % e)

    module.exit_json(changed=changed, db=db, ext=ext)

# import module snippets
from ansible.module_utils.basic import AnsibleModule,get_exception
import ansible.module_utils.postgres as pgutils

if __name__ == '__main__':
    main()
