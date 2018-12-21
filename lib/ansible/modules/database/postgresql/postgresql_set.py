#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: postgresql_set
short_description: Change a PostgreSQL server configuration parameter
description:
   - Allows to change PostgreSQL (9.4+) server configuration parameters
     using ALTER SYSTEM command and apply them by reload server configuration.
   - Changed parameter values are stored in PGDATA/postgresql.auto.conf.
   - Allows to reset parameter to boot_val (cluster initial value) or remove parameter
     string from postgresql.auto.conf and reload.
   - After change you can see in ansible output the previous and
     the new parameter value, and other information by using returned values.
version_added: "2.8"
options:
  name:
    description:
      - Name of PostgreSQL server parameter.
    required: true
  value:
    description:
      - Parameter value to set (may be 'default' to remove parameter string from postgresql.auto.conf).
  show:
    description:
      - Show parameter value.
    default: false
    type: bool
  reset:
    description:
      - Restore parameter to initial state (boot_val).
    default: false
    type: bool
  db:
    description:
      - Name of database to connect.
  port:
    description:
      - Database port to connect.
    default: 5432
  login_user:
    description:
      - User (role) used to authenticate with PostgreSQL.
    default: postgres
  login_password:
    description:
      - Password used to authenticate with PostgreSQL.
  login_host:
    description:
      - Host running PostgreSQL.
  login_unix_socket:
    description:
      - Path to a Unix domain socket for local connections.
  ssl_mode:
    description:
      - Determines whether or with what priority a secure SSL TCP/IP connection
        will be negotiated with the server.
      - See U(https://www.postgresql.org/docs/current/static/libpq-ssl.html) for
        more information on the modes.
      - Default of C(prefer) matches libpq default.
    default: prefer
    choices: ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
  ssl_rootcert:
    description:
      - Specifies the name of a file containing SSL certificate authority (CA)
        certificate(s). If the file exists, the server's certificate will be
        verified to be signed by one of these authorities.
notes:
   - Check_mode is not supported because ALTER SYSTEM cannot run inside a transaction block.
     You may use "show" parameter to know desired setting will be changed or not.
   - Supported version of PostgreSQL is 9.4 and later.
   - For some parameters restart of PostgreSQL server is required.
     See official documentation.
   - The default authentication assumes that you are either logging in as or
     sudo'ing to the postgres account on the host.
   - This module uses psycopg2, a Python PostgreSQL database adapter. You must
     ensure that psycopg2 is installed on the host before using this module. If
     the remote host is the PostgreSQL server (which is the default case), then
     PostgreSQL must also be installed on the remote host. For Ubuntu-based
     systems, install the postgresql, libpq-dev, and python-psycopg2 packages
     on the remote host before using this module.
requirements: [ psycopg2 ]
author: "Andrew Klychkov (@Andersson007)"
'''

EXAMPLES = '''
# Show current value of wal_keep_segments parameter
- postgresql_set:
    name: wal_keep_segments
    show: yes
  register: show_value

- debug:
    msg: "{{ show_value.info }}"

# Restore wal_keep_segments parameter to initial state
- postgresql_set:
    name: wal_keep_segments
    reset: yes

# Set work_mem parameter to 32MB and show what's been changed and restart is required or not
# (output example: "msg": "pg_test.lan work_mem 64MB => 32MB, restart_required: False")
- postgresql_set:
    name: work_mem
    value: 32mb
    register: set_value

- debug:
    msg: "{{ inventory_hostname }} {{ set_value.name }} {{ set_value.result }}, restart_required: {{ set_value.restart_required }}"
  when: set_value.changed

# Set log_min_duration_statement parameter to 1 second
- postgresql_set:
    name: log_min_duration_statement
    value: 1s

# Set wal_log_hints parameter to default value (remove parameter from postgresql.auto.conf)
- postgresql_set:
    name: wal_log_hints
    value: default
'''

RETURN = '''
name:
    description: Name of PostgreSQL server parameter.
    returned: always
    type: string
    sample: 'shared_buffers'
info:
    description: Information about parameter current state.
    returned: always
    type: string
    sample: 'shared_buffers'
restart_required:
    description: Information about parameter current state.
    returned: always
    type: boolean
    sample: True
result:
    description: Information what has been changed.
    returned: always
    type: string
    sample: 128MB => 254MB
'''


import traceback

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    postgresqldb_found = False
else:
    postgresqldb_found = True

import ansible.module_utils.postgres as pgutils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import SQLParseError
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems


# To allow to set value like 1mb instead of 1MB, etc:
POSSIBLE_SIZE_UNITS = ("mb", "gb", "tb")


# ===========================================
# PostgreSQL module specific support methods.
#


def param_get(cursor, module, name):
    query = "SELECT name, setting, unit, context, boot_val "\
            "FROM pg_settings WHERE name = '%s'" % name
    try:
        cursor.execute(query)
        info = cursor.fetchall()
        cursor.execute("SHOW %s" % name)
        val = cursor.fetchone()
    except SQLParseError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except psycopg2.ProgrammingError as e:
        module.fail_json(msg="Unable to get %s value due to : %s" % (name, to_native(e)),
                         exception=traceback.format_exc())

    return (val, info)


def param_set(cursor, module, name, value):
    try:
        if value in ('DEFAULT', 'default'):
            query = "ALTER SYSTEM SET %s = DEFAULT" % name
        else:
            query = "ALTER SYSTEM SET %s = '%s'" % (name, value)
        cursor.execute(query)
        cursor.execute("SELECT pg_reload_conf()")
    except SQLParseError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except psycopg2.ProgrammingError as e:
        module.fail_json(msg="Unable to get %s value due to : %s" % (name, to_native(e)),
                         exception=traceback.format_exc())
    return True

# ===========================================
# Module execution.
#


def main():
    argument_spec = pgutils.postgres_common_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        db=dict(default=''),
        ssl_mode=dict(default='prefer', choices=[
            'disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']),
        ssl_rootcert=dict(default=None),
        value=dict(default=None),
        show=dict(type=bool, default=False),
        reset=dict(type=bool, default=False)
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    name = module.params["name"]
    value = module.params["value"]
    show = module.params["show"]
    reset = module.params["reset"]
    sslrootcert = module.params["ssl_rootcert"]

    # Allow to pass values like 1mb instead of 1MB, etc:
    if value is not None:
        for unit in POSSIBLE_SIZE_UNITS:
            if unit in value:
                value = value.upper()

    if value is not None and reset:
        module.fail_json(msg="%s: value and reset params are mutual "
                             "exclusive" % name)

    if (value is not None and show) or (reset and show):
        module.fail_json(msg="%s: param value/reset is mutual "
                             "exclusive with show" % name)

    if value is None and not reset and not show:
        module.fail_json(msg="%s: at least one of value, show, or "
                             "reset param must be specified" % name)

    if not postgresqldb_found:
        module.fail_json(msg="the python psycopg2 module is required")

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
        "ssl_rootcert": "sslrootcert"
    }
    kw = dict((params_map[k], v) for (k, v) in iteritems(module.params)
              if k in params_map and v != "" and v is not None)

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    if psycopg2.__version__ < '2.4.3' and sslrootcert is not None:
        module.fail_json(
            msg='psycopg2 must be at least 2.4.3 in order to user the ssl_rootcert parameter')

    try:
        db_connection = psycopg2.connect(**kw)
        db_connection.set_session(autocommit=True)

        cursor = db_connection.cursor(
            cursor_factory=psycopg2.extras.DictCursor)
    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(
                msg='Postgresql server must be at least version 8.4 to support sslrootcert')
        module.fail_json(msg="unable to connect to database: %s" % to_native(e),
                         exception=traceback.format_exc())
    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e),
                         exception=traceback.format_exc())

    # Set default returned values:
    restart_required = False
    changed = False
    kw['name'] = name
    kw['restart_required'] = restart_required
    kw['result'] = 'nothing to change'

    # Get info about param state:
    res = param_get(cursor, module, name)
    current_value = res[0][0]
    raw_val = res[1][0][1]
    unit = res[1][0][2]
    if unit is None:
        unit = ''
    boot_val = res[1][0][4]
    context = res[1][0][3]

    kw['info'] = "name: %s, setting: %s, context: %s, "\
                 "boot_val: %s, unit: %s" % (name, current_value, context,
                                             boot_val, unit)
    # Do job
    # Show param:
    if show:
        module.exit_json(**kw)

    if context == "internal":
        module.fail_json(msg="%s: cannot be changed (internal context). "
                             "See documentation" % name)

    if context == "postmaster":
        restart_required = True

    # Set param:
    if value is not None and value != current_value:
        changed = param_set(cursor, module, name, value)
        kw['result'] = '%s => %s' % (current_value, value)
    # Reset param:
    elif reset:
        if raw_val == boot_val:
            # nothing to change, exit:
            module.exit_json(**kw)
        changed = param_set(cursor, module, name, boot_val)

        if unit:
            kw['result'] = '%s => %s (unit: %s)' % (current_value, boot_val, unit)
        else:
            kw['result'] = '%s => %s' % (current_value, boot_val)

    if changed:
        if not restart_required:
            new_value = param_get(cursor, module, name)[0][0]
            kw['result'] = '%s => %s' % (current_value, new_value)
            kw['info'] = "name: %s, setting: %s, context: %s, "\
                         "boot_val: %s, unit: %s" % (name, new_value, context,
                                                     boot_val, unit)

    kw['changed'] = changed
    kw['restart_required'] = restart_required
    module.exit_json(**kw)


if __name__ == '__main__':
    main()
