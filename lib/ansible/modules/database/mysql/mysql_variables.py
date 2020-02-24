#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Balazs Pocze <banyek@gawker.com>
# Certain parts are taken from Mark Theunissen's mysqldb module
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: mysql_variables

short_description: Manage MySQL global variables
description:
- Query / Set MySQL variables.
version_added: '1.3'
author:
- Balazs Pocze (@banyek)
options:
  variable:
    description:
    - Variable name to operate
    type: str
    required: yes
  value:
    description:
    - If set, then sets variable value to this
    type: str
  mode:
    description:
    - C(global) assigns C(value) to a global system variable which will be changed at runtime
      but won't persist across server restarts.
    - C(persist) assigns C(value) to a global system variable and persists it to
      the mysqld-auto.cnf option file in the data directory
      (the variable will survive service restarts).
    - C(persist_only) persists C(value) to the mysqld-auto.cnf option file in the data directory
      but without setting the global variable runtime value
      (the value will be changed after the next service restart).
    - Supported by MySQL 8.0 or later.
    - For more information see U(https://dev.mysql.com/doc/refman/8.0/en/set-variable.html).
    type: str
    choices: ['global', 'persist', 'persist_only']
    default: global
    version_added: '2.10'

seealso:
- module: mysql_info
- name: MySQL SET command reference
  description: Complete reference of the MySQL SET command documentation.
  link: https://dev.mysql.com/doc/refman/8.0/en/set-statement.html

extends_documentation_fragment:
- mysql
'''

EXAMPLES = r'''
- name: Check for sync_binlog setting
  mysql_variables:
    variable: sync_binlog

- name: Set read_only variable to 1 persistently
  mysql_variables:
    variable: read_only
    value: 1
    mode: persist
'''

RETURN = r'''
queries:
  description: List of executed queries which modified DB's state.
  returned: if executed
  type: list
  sample: ["SET GLOBAL `read_only` = 1"]
  version_added: '2.10'
'''

import os
import warnings
from re import match

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import SQLParseError, mysql_quote_identifier
from ansible.module_utils.mysql import mysql_connect, mysql_driver, mysql_driver_fail_msg
from ansible.module_utils._text import to_native

executed_queries = []


def check_mysqld_auto(module, cursor, mysqlvar):
    """Check variable's value in mysqld-auto.cnf."""
    query = ("SELECT VARIABLE_VALUE "
             "FROM performance_schema.persisted_variables "
             "WHERE VARIABLE_NAME = %s")
    try:
        cursor.execute(query, (mysqlvar,))
        res = cursor.fetchone()
    except Exception as e:
        if "Table 'performance_schema.persisted_variables' doesn't exist" in str(e):
            module.fail_json(msg='Server version must be 8.0 or greater.')

    if res:
        return res[0]
    else:
        return None


def typedvalue(value):
    """
    Convert value to number whenever possible, return same value
    otherwise.

    >>> typedvalue('3')
    3
    >>> typedvalue('3.0')
    3.0
    >>> typedvalue('foobar')
    'foobar'

    """
    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


def getvariable(cursor, mysqlvar):
    cursor.execute("SHOW VARIABLES WHERE Variable_name = %s", (mysqlvar,))
    mysqlvar_val = cursor.fetchall()
    if len(mysqlvar_val) == 1:
        return mysqlvar_val[0][1]
    else:
        return None


def setvariable(cursor, mysqlvar, value, mode='global'):
    """ Set a global mysql variable to a given value

    The DB driver will handle quoting of the given value based on its
    type, thus numeric strings like '3.0' or '8' are illegal, they
    should be passed as numeric literals.

    """
    if mode == 'persist':
        query = "SET PERSIST %s = " % mysql_quote_identifier(mysqlvar, 'vars')
    elif mode == 'global':
        query = "SET GLOBAL %s = " % mysql_quote_identifier(mysqlvar, 'vars')
    elif mode == 'persist_only':
        query = "SET PERSIST_ONLY %s = " % mysql_quote_identifier(mysqlvar, 'vars')

    try:
        cursor.execute(query + "%s", (value,))
        executed_queries.append(query + "%s" % value)
        cursor.fetchall()
        result = True
    except Exception as e:
        result = to_native(e)

    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(type='str'),
            login_password=dict(type='str', no_log=True),
            login_host=dict(type='str', default='localhost'),
            login_port=dict(type='int', default=3306),
            login_unix_socket=dict(type='str'),
            variable=dict(type='str'),
            value=dict(type='str'),
            client_cert=dict(type='path', aliases=['ssl_cert']),
            client_key=dict(type='path', aliases=['ssl_key']),
            ca_cert=dict(type='path', aliases=['ssl_ca']),
            connect_timeout=dict(type='int', default=30),
            config_file=dict(type='path', default='~/.my.cnf'),
            mode=dict(type='str', choices=['global', 'persist', 'persist_only'], default='global'),
        ),
    )
    user = module.params["login_user"]
    password = module.params["login_password"]
    connect_timeout = module.params['connect_timeout']
    ssl_cert = module.params["client_cert"]
    ssl_key = module.params["client_key"]
    ssl_ca = module.params["ca_cert"]
    config_file = module.params['config_file']
    db = 'mysql'

    mysqlvar = module.params["variable"]
    value = module.params["value"]
    mode = module.params["mode"]

    if mysqlvar is None:
        module.fail_json(msg="Cannot run without variable to operate with")
    if match('^[0-9a-z_.]+$', mysqlvar) is None:
        module.fail_json(msg="invalid variable name \"%s\"" % mysqlvar)
    if mysql_driver is None:
        module.fail_json(msg=mysql_driver_fail_msg)
    else:
        warnings.filterwarnings('error', category=mysql_driver.Warning)

    try:
        cursor, db_conn = mysql_connect(module, user, password, config_file, ssl_cert, ssl_key, ssl_ca, db,
                                        connect_timeout=connect_timeout)
    except Exception as e:
        if os.path.exists(config_file):
            module.fail_json(msg=("unable to connect to database, check login_user and "
                                  "login_password are correct or %s has the credentials. "
                                  "Exception message: %s" % (config_file, to_native(e))))
        else:
            module.fail_json(msg="unable to find %s. Exception message: %s" % (config_file, to_native(e)))

    mysqlvar_val = None
    var_in_mysqld_auto_cnf = None

    mysqlvar_val = getvariable(cursor, mysqlvar)
    if mysqlvar_val is None:
        module.fail_json(msg="Variable not available \"%s\"" % mysqlvar, changed=False)

    if value is None:
        module.exit_json(msg=mysqlvar_val)

    if mode in ('persist', 'persist_only'):
        var_in_mysqld_auto_cnf = check_mysqld_auto(module, cursor, mysqlvar)

        if mode == 'persist_only':
            if var_in_mysqld_auto_cnf is None:
                mysqlvar_val = False
            else:
                mysqlvar_val = var_in_mysqld_auto_cnf

    # Type values before using them
    value_wanted = typedvalue(value)
    value_actual = typedvalue(mysqlvar_val)
    value_in_auto_cnf = None
    if var_in_mysqld_auto_cnf is not None:
        value_in_auto_cnf = typedvalue(var_in_mysqld_auto_cnf)

    if value_wanted == value_actual and mode in ('global', 'persist'):
        if mode == 'persist' and value_wanted == value_in_auto_cnf:
            module.exit_json(msg="Variable is already set to requested value globally"
                                 "and stored into mysqld-auto.cnf file.", changed=False)

        elif mode == 'global':
            module.exit_json(msg="Variable is already set to requested value.", changed=False)

    if mode == 'persist_only' and value_wanted == value_in_auto_cnf:
        module.exit_json(msg="Variable is already stored into mysqld-auto.cnf "
                             "with requested value.", changed=False)

    try:
        result = setvariable(cursor, mysqlvar, value_wanted, mode)
    except SQLParseError as e:
        result = to_native(e)

    if result is True:
        module.exit_json(msg="Variable change succeeded prev_value=%s" % value_actual,
                         changed=True, queries=executed_queries)
    else:
        module.fail_json(msg=result, changed=False)


if __name__ == '__main__':
    main()
