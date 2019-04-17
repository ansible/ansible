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

DOCUMENTATION = r'''
---
module: postgresql_set
short_description: Change a PostgreSQL server configuration parameter
description:
   - Allows to change a PostgreSQL server configuration parameter.
   - The module uses ALTER SYSTEM command U(https://www.postgresql.org/docs/current/sql-altersystem.html)
     and applies changes by reload server configuration.
   - ALTER SYSTEM is used for changing server configuration parameters across the entire database cluster.
   - It can be more convenient and safe than the traditional method of manually editing the postgresql.conf file.
   - ALTER SYSTEM writes the given parameter setting to the $PGDATA/postgresql.auto.conf file,
     which is read in addition to postgresql.conf U(https://www.postgresql.org/docs/current/sql-altersystem.html).
   - The module allows to reset parameter to boot_val (cluster initial value) by I(reset=yes) or remove parameter
     string from postgresql.auto.conf and reload I(value=default) (for settings with postmaster context restart is required).
   - After change you can see in the ansible output the previous and
     the new parameter value and other information using returned values and M(debug) module.
version_added: '2.8'
options:
  name:
    description:
    - Name of PostgreSQL server parameter.
    type: str
    required: true
  value:
    description:
    - Parameter value to set.
    - To remove parameter string from postgresql.auto.conf and
      reload the server configuration you must pass I(value=default).
      With I(value=default) the playbook always returns changed is true.
    type: str
    required: true
  reset:
    description:
    - Restore parameter to initial state (boot_val). Mutually exclusive with I(value).
    type: bool
    default: false
  session_role:
    description:
    - Switch to session_role after connecting. The specified session_role must
      be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though
      the session_role were the one that had logged in originally.
    type: str
  db:
    description:
    - Name of database to connect.
    type: str
    aliases:
    - login_db
notes:
- Supported version of PostgreSQL is 9.4 and later.
- Pay attention, change setting with 'postmaster' context can return changed is true
  when actually nothing changes because the same value may be presented in
  several different form, for example, 1024MB, 1GB, etc. However in pg_settings
  system view it can be defined like 131072 number of 8kB pages.
  The final check of the parameter value cannot compare it because the server was
  not restarted and the value in pg_settings is not updated yet.
- For some parameters restart of PostgreSQL server is required.
  See official documentation U(https://www.postgresql.org/docs/current/view-pg-settings.html).
- The default authentication assumes that you are either logging in as or
  sudo'ing to the postgres account on the host.
- This module uses psycopg2, a Python PostgreSQL database adapter. You must
  ensure that psycopg2 is installed on the host before using this module. If
  the remote host is the PostgreSQL server (which is the default case), then
  PostgreSQL must also be installed on the remote host. For Ubuntu-based
  systems, install the postgresql, libpq-dev, and python-psycopg2 packages
  on the remote host before using this module.
requirements: [ psycopg2 ]
author:
- Andrew Klychkov (@Andersson007)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Restore wal_keep_segments parameter to initial state
  postgresql_set:
    name: wal_keep_segments
    reset: yes

# Set work_mem parameter to 32MB and show what's been changed and restart is required or not
# (output example: "msg": "work_mem 4MB >> 64MB restart_req: False")
- name: Set work mem parameter
  postgresql_set:
    name: work_mem
    value: 32mb
    register: set

- debug:
    msg: "{{ set.name }} {{ set.prev_val_pretty }} >> {{ set.value_pretty }} restart_req: {{ set.restart_required }}"
  when: set.changed
# Ensure that the restart of PostgreSQL serever must be required for some parameters.
# In this situation you see the same parameter in prev_val and value_prettyue, but 'changed=True'
# (If you passed the value that was different from the current server setting).

- name: Set log_min_duration_statement parameter to 1 second
  postgresql_set:
    name: log_min_duration_statement
    value: 1s

- name: Set wal_log_hints parameter to default value (remove parameter from postgresql.auto.conf)
  postgresql_set:
    name: wal_log_hints
    value: default
'''

RETURN = r'''
name:
  description: Name of PostgreSQL server parameter.
  returned: always
  type: str
  sample: 'shared_buffers'
restart_required:
  description: Information about parameter current state.
  returned: always
  type: bool
  sample: true
prev_val_pretty:
  description: Information about previous state of the parameter.
  returned: always
  type: str
  sample: '4MB'
value_pretty:
  description: Information about current state of the parameter.
  returned: always
  type: str
  sample: '64MB'
value:
  description:
  - Dictionary that contains the current parameter value (at the time of playbook finish).
  - Pay attention that for real change some parameters restart of PostgreSQL server is required.
  - Returns the current value in the check mode.
  returned: always
  type: dict
  sample: { "value": 67108864, "unit": "b" }
context:
  description:
  - PostgreSQL setting context.
  returned: always
  type: str
  sample: user
'''

PG_REQ_VER = 90400

from copy import deepcopy

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import SQLParseError
from ansible.module_utils.postgres import postgres_common_argument_spec
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native


# To allow to set value like 1mb instead of 1MB, etc:
POSSIBLE_SIZE_UNITS = ("mb", "gb", "tb")

# ===========================================
# PostgreSQL module specific support methods.
#


def param_get(cursor, module, name):
    query = ("SELECT name, setting, unit, context, boot_val "
             "FROM pg_settings WHERE name = '%s'" % name)
    try:
        cursor.execute(query)
        info = cursor.fetchall()
        cursor.execute("SHOW %s" % name)
        val = cursor.fetchone()

    except Exception as e:
        module.fail_json(msg="Unable to get %s value due to : %s" % (name, to_native(e)))

    raw_val = info[0][1]
    unit = info[0][2]
    context = info[0][3]
    boot_val = info[0][4]

    if val[0] == 'True':
        val[0] = 'on'
    elif val[0] == 'False':
        val[0] = 'off'

    if unit == 'kB':
        if int(raw_val) > 0:
            raw_val = int(raw_val) * 1024
        if int(boot_val) > 0:
            boot_val = int(boot_val) * 1024

        unit = 'b'

    elif unit == 'MB':
        if int(raw_val) > 0:
            raw_val = int(raw_val) * 1024 * 1024
        if int(boot_val) > 0:
            boot_val = int(boot_val) * 1024 * 1024

        unit = 'b'

    return (val[0], raw_val, unit, boot_val, context)


def pretty_to_bytes(pretty_val):
    # The function returns a value in bytes
    # if the value contains 'B', 'kB', 'MB', 'GB', 'TB'.
    # Otherwise it returns the passed argument.

    val_in_bytes = None

    if 'kB' in pretty_val:
        num_part = int(''.join(d for d in pretty_val if d.isdigit()))
        val_in_bytes = num_part * 1024

    elif 'MB' in pretty_val.upper():
        num_part = int(''.join(d for d in pretty_val if d.isdigit()))
        val_in_bytes = num_part * 1024 * 1024

    elif 'GB' in pretty_val.upper():
        num_part = int(''.join(d for d in pretty_val if d.isdigit()))
        val_in_bytes = num_part * 1024 * 1024 * 1024

    elif 'TB' in pretty_val.upper():
        num_part = int(''.join(d for d in pretty_val if d.isdigit()))
        val_in_bytes = num_part * 1024 * 1024 * 1024 * 1024

    elif 'B' in pretty_val.upper():
        num_part = int(''.join(d for d in pretty_val if d.isdigit()))
        val_in_bytes = num_part

    else:
        return pretty_val

    return val_in_bytes


def param_set(cursor, module, name, value, context):
    try:
        if str(value).lower() == 'default':
            query = "ALTER SYSTEM SET %s = DEFAULT" % name
        else:
            query = "ALTER SYSTEM SET %s = '%s'" % (name, value)
        cursor.execute(query)

        if context != 'postmaster':
            cursor.execute("SELECT pg_reload_conf()")

    except Exception as e:
        module.fail_json(msg="Unable to get %s value due to : %s" % (name, to_native(e)))

    return True


def connect_to_db(module, kw, autocommit=False):
    try:
        db_connection = psycopg2.connect(**kw)
        if autocommit:
            db_connection.set_session(autocommit=True)

    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least version 8.4 to support sslrootcert')
        module.fail_json(msg="unable to connect to database: %s" % to_native(e))
    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e))

    return db_connection

# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        name=dict(type='str', required=True),
        db=dict(type='str', aliases=['login_db']),
        port=dict(type='int', default=5432, aliases=['login_port']),
        ssl_mode=dict(type='str', default='prefer', choices=['allow', 'disable', 'prefer', 'require', 'verify-ca', 'verify-full']),
        ca_cert=dict(type='str', aliases=['ssl_rootcert']),
        value=dict(type='str'),
        reset=dict(type='bool'),
        session_role=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg="the python psycopg2 module is required")

    name = module.params["name"]
    value = module.params["value"]
    reset = module.params["reset"]
    sslrootcert = module.params["ca_cert"]
    session_role = module.params["session_role"]

    # Allow to pass values like 1mb instead of 1MB, etc:
    if value:
        for unit in POSSIBLE_SIZE_UNITS:
            if unit in value:
                value = value.upper()

    if value and reset:
        module.fail_json(msg="%s: value and reset params are mutually exclusive" % name)

    if not value and not reset:
        module.fail_json(msg="%s: at least one of value or reset param must be specified" % name)

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
        "ca_cert": "sslrootcert"
    }
    kw = dict((params_map[k], v) for (k, v) in iteritems(module.params)
              if k in params_map and v != '' and v is not None)

    # Store connection parameters for the final check:
    con_params = deepcopy(kw)

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] is None or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    if psycopg2.__version__ < '2.4.3' and sslrootcert:
        module.fail_json(msg='psycopg2 must be at least 2.4.3 '
                             'in order to user the ca_cert parameter')

    db_connection = connect_to_db(module, kw, autocommit=True)
    cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check server version (needs 9.4 or later):
    cursor.execute("select current_setting('server_version_num')")
    ver = int(cursor.fetchone()[0])
    if ver < PG_REQ_VER:
        module.warn("PostgreSQL is %s version but %s or later is required" % (ver, PG_REQ_VER))
        kw = dict(
            changed=False,
            restart_required=False,
            value_pretty="",
            prev_val_pretty="",
            value={"value": "", "unit": ""},
        )
        kw['name'] = name
        db_connection.close()
        module.exit_json(**kw)

    # Switch role, if specified:
    if session_role:
        try:
            cursor.execute('SET ROLE %s' % session_role)
        except Exception as e:
            module.fail_json(msg="Could not switch role: %s" % to_native(e))

    # Set default returned values:
    restart_required = False
    changed = False
    kw['name'] = name
    kw['restart_required'] = False

    # Get info about param state:
    res = param_get(cursor, module, name)
    current_value = res[0]
    raw_val = res[1]
    unit = res[2]
    boot_val = res[3]
    context = res[4]

    if value == 'True':
        value = 'on'
    elif value == 'False':
        value = 'off'

    kw['prev_val_pretty'] = current_value
    kw['value_pretty'] = deepcopy(kw['prev_val_pretty'])
    kw['context'] = context

    # Do job
    if context == "internal":
        module.fail_json(msg="%s: cannot be changed (internal context). See "
                             "https://www.postgresql.org/docs/current/runtime-config-preset.html" % name)

    if context == "postmaster":
        restart_required = True

    # If check_mode, just compare and exit:
    if module.check_mode:
        if pretty_to_bytes(value) == pretty_to_bytes(current_value):
            kw['changed'] = False

        else:
            kw['value_pretty'] = value
            kw['changed'] = True

        # Anyway returns current raw value in the check_mode:
        kw['value'] = dict(
            value=raw_val,
            unit=unit,
        )
        kw['restart_required'] = restart_required
        module.exit_json(**kw)

    # Set param:
    if value and value != current_value:
        changed = param_set(cursor, module, name, value, context)

        kw['value_pretty'] = value

    # Reset param:
    elif reset:
        if raw_val == boot_val:
            # nothing to change, exit:
            kw['value'] = dict(
                value=raw_val,
                unit=unit,
            )
            module.exit_json(**kw)

        changed = param_set(cursor, module, name, boot_val, context)

    if restart_required:
        module.warn("Restart of PostgreSQL is required for setting %s" % name)

    cursor.close()
    db_connection.close()

    # Reconnect and recheck current value:
    if context in ('sighup', 'superuser-backend', 'backend', 'superuser', 'user'):
        db_connection = connect_to_db(module, con_params, autocommit=True)
        cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

        res = param_get(cursor, module, name)
        # f_ means 'final'
        f_value = res[0]
        f_raw_val = res[1]

        if raw_val == f_raw_val:
            changed = False

        else:
            changed = True

        kw['value_pretty'] = f_value
        kw['value'] = dict(
            value=f_raw_val,
            unit=unit,
        )

        cursor.close()
        db_connection.close()

    kw['changed'] = changed
    kw['restart_required'] = restart_required
    module.exit_json(**kw)


if __name__ == '__main__':
    main()
