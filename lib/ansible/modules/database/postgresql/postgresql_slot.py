#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: postgresql_slot
short_description: Add or remove physical or logical slots from a PostgreSQL database.
description:
   - Add or remove slots from a postgresql database.
version_added: "2.4"
options:
  name:
    description:
      - name of the slot to add or remove
    required: true
  type:
    description:
      - slots come in two distinct flavors
    required: false
    default: physical
    choices: [ "physical", "logical" ]
  db:
    description:
      - name of the database to add or remove only the logical slot to/from
    required: false
  decoder:
    description:
      - all logical slots must indicate which decoder they're using
    required: false
    default: "test_decoding"
  login_user:
    description:
      - The username used to authenticate with
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
  state:
    description:
      - The slot state
    default: present
    choices: [ "present", "absent" ]
notes:
   - The default authentication assumes that you are either logging in as or sudo'ing to the C(postgres) account on the host.
   - This module uses I(psycopg2), a Python PostgreSQL database adapter. You must ensure that psycopg2 is installed on
     the host before using this module. If the remote host is the PostgreSQL server (which is the default case), then PostgreSQL mu
st also be installed
     on the remote host. For Ubuntu-based systems, install the C(postgresql), C(libpq-dev), and C(python-psycopg2) packages on the
remote host before using
     this module.
requirements: [ psycopg2 ]
author: "John Scalia (@jscalia)"
'''

EXAMPLES = '''
# Adds physical_slot_one to the cluster running on target host default port 5432
- postgresql_slot:
    name: physical_slot_one
    state: present

# Add a logical_slot_one to the database "acme" on target host default port 5432
- postgresql_slot:
    name: logical_slot_one
    type: logical
    state: present
    decoder: custom_decoder_one
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


def slot_create_physical(cursor, slot):
    if not slot_exists(cursor, slot):
        query = "SELECT pg_create_physical_replication_slot('%s')" % slot
        cursor.execute(query)
        return True
    else:
        return False


def slot_create_logical(cursor, slot, decoder):
    if not slot_exists(cursor, slot):
        query = "SELECT pg_create_logical_replication_slot('%s', '%s')" % (slot, decoder)
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
            db=dict(required=False),
            slot=dict(required=True, aliases=['name']),
            type=dict(default="physical", choices=["physical", "logical"]),
            decoder=dict(default="test_decoding"),
            state=dict(default="present", choices=["absent", "present"]),
        ),
        supports_check_mode=True
    )

    if not postgresqldb_found:
        module.fail_json(msg="the python psycopg2 module is required")

    db = module.params["db"]
    slot = module.params["slot"]
    type = module.params["type"]
    state = module.params["state"]
    decoder = module.params["decoder"]
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
    try:
        db_connection = psycopg2.connect(database=db, **kw)
        # Enable autocommit so we can create databases
        if psycopg2.__version__ >= '2.4.2':
            db_connection.autocommit = True

        cursor = db_connection.cursor(
            cursor_factory=psycopg2.extras.DictCursor)
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
                if type == "physical":
                    changed = slot_create_physical(cursor, slot)
                else:
                    changed = slot_create_logical(cursor, slot, decoder)
    except NotSupportedError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except Exception as e:
        module.fail_json(msg="Database query failed: %s" % to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=changed, db=db, slot=slot)


if __name__ == '__main__':
    main()
