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
module: postgresql_tablespace
short_description: Add or remove PostgreSQL tablespace from a remote host.
description:
   - Add or remove PostgreSQL tablespace from a remote host.
version_added: "2.2"
options:
  name:
    description:
      - name of the tablespace to add or remove
    required: true
    default: null
  location:
    description:
      - location of the tablespace to add or remove
    required: true
    default: null
  database:
    description:
      - name of the database to connect to
    required: false
    default: postgres
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
  login_unix_socket:
    description:
      - Path to a Unix domain socket for local connections
    required: false
    default: null
  owner:
    description:
      - Name of the role to set as owner of the tablespace
    required: false
    default: null
  port:
    description:
      - Database port to connect to.
    required: false
    default: 5432
  state:
    description:
      - The tablespace state
    required: false
    default: present
    choices: [ "present", "absent" ]
notes:
   - This module uses I(psycopg2), a Python PostgreSQL database adapter. You must ensure that psycopg2 is installed on
     the host before using this module. If the remote host is the PostgreSQL server (which is the default case), then PostgreSQL must also be installed on the remote host. For Ubuntu-based systems, install the C(postgresql), C(libpq-dev), and C(python-psycopg2) packages on the remote host before using this module.
requirements: [ psycopg2 ]
author: "Flavien Chantelot <contact@flavien.io>"
'''

EXAMPLES = '''
# Create a new tablespace with name "acme"
- postgresql_tablespace: name=acme
# Create a new tablespace "acme" with a user "bob" who will own it
- postgresql_tablespace: name=acme owner=bob location=/data/foo

'''

RETURN = '''
tablespace:
    description: Name of the tablespace
    returned: success, changed
    type: string
    sample: "tbl_fizzbuzz"
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

def set_owner(cursor, tablespace, owner):
    query = "ALTER TABLESPACE %s OWNER TO %s" % (
            pg_quote_identifier(tablespace, 'database'),
            pg_quote_identifier(owner, 'role'))
    cursor.execute(query)
    return True

#def set_location(cursor, tablespace, location):
#    query = "ALTER TABLESPACE %s OWNER TO %s" % (
#            pg_quote_identifier(tablespace, 'database'),
#            pg_quote_identifier(owner, 'role'))
#    cursor.execute(query)
#    return True

def get_tablespace_info(cursor, tablespace):
    query = """
    SELECT spcname as name, pg_catalog.pg_get_userbyid(spcowner) as owner, pg_catalog.pg_tablespace_location(oid) as location
    FROM pg_catalog.pg_tablespace
    WHERE spcname = %(tablespace)s
    """
    cursor.execute(query, {'tablespace': tablespace})
    return cursor.fetchone()

def tablespace_exists(cursor, tablespace):
    query = "SELECT spcname FROM pg_catalog.pg_tablespace WHERE spcname = %(tablespace)s"
    cursor.execute(query, {'tablespace': tablespace})
    return cursor.rowcount == 1

def tablespace_delete(cursor, tablespace):
    if tablespace_exists(cursor, tablespace):
        query = "DROP TABLESPACE %s" % pg_quote_identifier(tablespace, 'tablespace')
        cursor.execute(query)
        return True
    else:
        return False

def tablespace_create(cursor, tablespace, location, owner):
    if not tablespace_exists(cursor, tablespace):
        query_fragments = ['CREATE TABLESPACE %s' % pg_quote_identifier(tablespace, 'database')]
        if owner:
            query_fragments.append('OWNER %s' % pg_quote_identifier(owner, 'role'))
        if location:
            query_fragments.append("LOCATION '%s'" % location)
        query = ' '.join(query_fragments)
        cursor.execute(query)
        return True
    else:
        tablespace_info = get_tablespace_info(cursor, tablespace)
        if owner and owner != tablespace_info['owner']:
            return set_owner(cursor, tablespace, owner)
        else:
            return False

def tablespace_matches(cursor, tablespace, location, owner):
    if not tablespace_exists(cursor, tablespace):
        return False
    else:
        tablespace_info = get_tablespace_info(cursor, tablespace)
        if owner and owner != tablespace_info['owner']:
            return False
        if location and location != tablespace_info['location']:
            return False
        return True

# ===========================================
# Module execution.
#

def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default="postgres"),
            login_password=dict(default=""),
            login_host=dict(default=""),
            login_unix_socket=dict(default=""),
            port=dict(default="5432"),
            tablespace=dict(required=True, aliases=['name']),
            location=dict(required=True),
            owner=dict(default=""),
            database=dict(default="postgres"),
            state=dict(default="present", choices=["absent", "present"]),
        ),
        supports_check_mode = True
    )

    if not postgresqldb_found:
        module.fail_json(msg="the python psycopg2 module is required")

    tablespace = module.params["tablespace"]
    owner = module.params["owner"]
    state = module.params["state"]
    database = module.params["database"]
    location = module.params["location"]
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
    except Exception:
        e = get_exception()
        module.fail_json(msg="unable to connect to database: %s" %(text, str(e)))

    try:
        if module.check_mode:
            if state == "absent":
                changed = not tablespace_exists(cursor, tablespace)
            elif state == "present":
                changed = not tablespace_matches(cursor, tablespace, location, owner)
            module.exit_json(changed=changed, tablespace=tablespace)

        if state == "absent":
            try:
                changed = tablespace_delete(cursor, tablespace)
            except SQLParseError:
                e = get_exception()
                module.fail_json(msg=str(e))

        elif state == "present":
            try:
                changed = tablespace_create(cursor, tablespace, location, owner)
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

    module.exit_json(changed=changed, tablespace=tablespace)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.database import *
if __name__ == '__main__':
    main()

