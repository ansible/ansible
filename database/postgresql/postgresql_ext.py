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
  login_user:
    description:
      - The username used to authenticate with
    required: false
    default: null
  login_password:
    description:
      - The password used to authenticate with
    required: false
    default: null
  login_host:
    description:
      - Host running the database
    required: false
    default: localhost
  port:
    description:
      - Database port to connect to.
    required: false
    default: 5432
  state:
    description:
      - The database extension state
    required: false
    default: present
    choices: [ "present", "absent" ]
notes:
   - The default authentication assumes that you are either logging in as or sudo'ing to the C(postgres) account on the host.
   - This module uses I(psycopg2), a Python PostgreSQL database adapter. You must ensure that psycopg2 is installed on
     the host before using this module. If the remote host is the PostgreSQL server (which is the default case), then PostgreSQL must also be installed on the remote host. For Ubuntu-based systems, install the C(postgresql), C(libpq-dev), and C(python-psycopg2) packages on the remote host before using this module.
requirements: [ psycopg2 ]
author: "Daniel Schep (@dschep)"
'''

EXAMPLES = '''
# Adds postgis to the database "acme"
- postgresql_ext: name=postgis db=acme
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
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default="postgres"),
            login_password=dict(default="", no_log=True),
            login_host=dict(default=""),
            port=dict(default="5432"),
            db=dict(required=True),
            ext=dict(required=True, aliases=['name']),
            state=dict(default="present", choices=["absent", "present"]),
        ),
        supports_check_mode = True
    )

    if not postgresqldb_found:
        module.fail_json(msg="the python psycopg2 module is required")

    db = module.params["db"]
    ext = module.params["ext"]
    port = module.params["port"]
    state = module.params["state"]
    changed = False

    # To use defaults values, keyword arguments must be absent, so 
    # check which values are empty and don't include in the **kw
    # dictionary
    params_map = {
        "login_host":"host",
        "login_user":"user",
        "login_password":"password",
        "port":"port"
    }
    kw = dict( (params_map[k], v) for (k, v) in module.params.iteritems() 
              if k in params_map and v != '' )
    try:
        db_connection = psycopg2.connect(database=db, **kw)
        # Enable autocommit so we can create databases
        if psycopg2.__version__ >= '2.4.2':
            db_connection.autocommit = True
        else:
            db_connection.set_isolation_level(psycopg2
                                              .extensions
                                              .ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = db_connection.cursor(
                cursor_factory=psycopg2.extras.DictCursor)
    except Exception:
        e = get_exception()
        module.fail_json(msg="unable to connect to database: %s" % e)

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
from ansible.module_utils.basic import *
from ansible.module_utils.pycompat24 import get_exception
main()

