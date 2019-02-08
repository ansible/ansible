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
module: postgresql_slot
short_description: Add or remove slots from a PostgreSQL database.
description:
  - Adds or removes physical or logical slots from a PostgreSQL database.
version_added: "2.8"
options:
  slot_name:
    description:
      - name of the slot to add or remove
    required: true
  slot_type:
    description:
      - slots come in two distinct flavors, physical and logical
    required: False
    default: physical
    choices: [ "physical", "logical" ]
  immediately_reserve:
    description: Optional parameter the when True specifies that the LSN for this replication slot be reserved immediately, otherwise the default, False, specifies that the LSN is reserved on the first connection from a streaming replication client.
    required: False
    default: False
    choices: [ "True", "False" ]
  db:
    description:
      - Name of the database where you're connecting in order to add or remove only the logical slot to/from
    required: false
  output_plugin:
    description:
      - All logical slots must indicate which output plugin decoder they're using. This parameter does not apply to physical slots.
    required: false
    default: "test_decoding"
  login_user:
    description:
      - The username used to authenticate with
    default: postgres
  login_password:
    description:
      - The password used to authenticate with
  login_host:
    description:
      - Host running the database
    default: localhost
  port:
    description:
      - Database port to connect to.
    default: 5432
  login_unix_socket:
    description:
      - Specifies the directory of the Unix-domain socket(s) on which the server is to listen for connections from client applications.
    default: None
  ssl_mode:
    description:
      - Determines whether or with what priority a secure SSL TCP/IP connection will be negotiated with the server.
      - See https://www.postgresql.org/docs/current/static/libpq-ssl.html for more information on the modes.
      - Default of C(prefer) matches libpq default.
    default: prefer
    choices: ["disable", "allow", "prefer", "require", verify-ca", "verify-full"]
    version added: '2.3'
  ssl-rootcert:
    description:
      - Specifies the name of a file containing the SSL certificate authority (CA) certificate(s). If the file exists, the server's certificate will be verified to be signed by one of these authorities.
    default: None
    version_added: '2.3'
  session_role:
    description: Switch to session role after connecting. The specified session_role must be a role that the current login_user is a member. Permissions checking for SQL commands is carried out as though the session_role were the one that had logged in originally.
    default: None
    version_added: '2.8'
  state:
    description:
      - The slot state. Whether you wish the slot to be present in the system or to not be present there.
    default: present
    choices: [ "present", "absent" ]
notes:
  - The default authentication assumes that you are either logging in as or sudo'ing to the C(postgres) account on the host.
  - Physical replication slots were introduced to PostgreSQL with version 9.4, while logical replication slots were added beginning with version 10.0.
    Physical slots are explained in https://www.postgresql.org/docs/9.4/protocol-replication.html and logical slots which were a later edition are
    described in https://www.postgresql.org/docs/10/logicaldecoding-explanation.html
  - This module uses I(psycopg2), a Python PostgreSQL database adapter. You must ensure that psycopg2 is installed on
    the host before using this module. If the remote host is the PostgreSQL server (which is the default case), then PostgreSQL
    must also be installed on the remote host. For Ubuntu-based systems, install the C(postgresql), C(libpq-dev), and
    C(python-psycopg2) packages on the remote host before using this module.
requirements: [ psycopg2 ]
author: "John Scalia (@jscalia)"
'''

EXAMPLES = '''
# Adds physical_slot_one to the cluster running on target host default port 5432
- postgresql_slot:
    slot_name: physical_slot_one
    state: present

# Add a logical_slot_one to the database "acme" on target host default port 5432
- postgresql_slot:
    slot_name: logical_slot_one
    slot_type: logical
    state: present
    output_plugin: custom_decoder_one
    
- postgresql_slot:
    slot_name: physical_slot_two
    slot_type: physical
    login_host: mydatabase.example.org
    port: 5433
    login_user: ourSuperuser
    login_password: thePassword
    ssl_mode: require
    state: present
'''

RETURN = '''
slot_name:
    description: Name of the slot
    returned: success, changed
    type: str
    sample: "physical_slot_one"
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
from ansible.module_utils._text import to_native


class NotSupportedError(Exception):
    pass


# ===========================================
# PostgreSQL module specific support methods.
#

def slot_exists(cursor, slot):
    query = "SELECT * FROM pg_replication_slots WHERE slot_name='%s'" % slot
    cursor.execute(query, {'slot': slot})
    return cursor.rowcount == 1


def slot_delete(cursor, slot):
    if slot_exists(cursor, slot):
        query = "SELECT pg_drop_replication_slot('%s')" % slot
        cursor.execute(query)
        return True
    else:
        return False


def slot_create_physical(cursor, slot, immediately_reserve):
    if not slot_exists(cursor, slot):
        query = "SELECT pg_create_physical_replication_slot('%s', %s, False)" % (slot, immediately_reserve)
        cursor.execute(query)
        return True
    else:
        return False


def slot_create_logical(cursor, slot, output_plugin):
    if not slot_exists(cursor, slot):
        query = "SELECT pg_create_logical_replication_slot('%s', '%s')" % (slot, output_plugin)
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
            login_host=dict(default="localhost"),
            login_unix_socket=dict(default=""),
            port=dict(default="5432"),
            db=dict(required=False),
            ssl_mode=dict(default="prefer", choices=["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]),
            ssl_rootcert=dict(default=None),
            slot_name=dict(required=True),
            slot_type=dict(default="physical", choices=["physical", "logical"]),
            immediately_reserve=dict(default=False),
            session_role=dict(required=False),
            output_plugin=dict(default="test_decoding"),
            state=dict(default="present", choices=["absent", "present"]),
        ),
        supports_check_mode=True
    )

    if not postgresqldb_found:
        module.fail_json(msg="the python psycopg2 module is required")

    db = module.params["db"]
    slot = module.params["slot_name"]
    slot_type = module.params["slot_type"]
    immediately_reserve = module.params["immediately_reserve"]
    state = module.params["state"]
    ssl_mode = module.params["ssl_mode"]
    sslrootcert = module.params["ssl_rootcert"]
    output_plugin = module.params["output_plugin"]
    changed = False

    # To use defaults values, keyword arguments must be absent, so
    # check which values are empty and don't include in the **kw
    # dictionary
    params_map = {
        "login_host": "host",
        "login_user": "user",
        "login_password": "password",
        "port": "port",
        "sslmode": "ssl_mode",
        "ssl_rootcert": "sslrootcert"
    }
    kw = dict((params_map[k], v) for (k, v) in module.params.items()
              if k in params_map and v != '')
    
    # if a login_unix_socket is specified, incorporate it here
    is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    if psycopg2.__version__ < '2.4.3' and ssl_rootcert is not None:
      module.fail_json(
        msg='psycopg2 must be at least 2.4.3 in order to use the ssl_rootcert parameter')

    try:
        db_connection = psycopg2.connect(database=db, **kw)
        # Enable autocommit so we can create databases
        if psycopg2.__version__ >= '2.4.2':
            db_connection.autocommit = True

        cursor = db_connection.cursor(
            cursor_factory=psycopg2.extras.DictCursor)
    
    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='PostgreSQL server must be at least version 8.4 to support sslrootcert')
        module.fail_json(msg="Unable to connect to database: %s" % to_native(e), exception=traceback.format_exc())

    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e), exception=traceback.format_exc())

    try:
        if module.check_mode:
            if state == "present":
                changed = not slot_exists(cursor, slot)
            elif state == "absent":
                changed = slot_exists(cursor, slot)
        else:
            if state == "absent":
                changed = slot_delete(cursor, slot)
            elif state == "present":
                if slot_type == "physical":
                    changed = slot_create_physical(cursor, slot, immediately_reserve)
                else:
                    changed = slot_create_logical(cursor, slot, output_plugin)
    except NotSupportedError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except Exception as e:
        module.fail_json(msg="Database query failed: %s" % to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=changed, db=db, slot_name=slot)


if __name__ == '__main__':
    main()
