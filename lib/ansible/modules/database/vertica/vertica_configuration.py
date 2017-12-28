#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: vertica_configuration
version_added: '2.0'
short_description: Updates Vertica configuration parameters.
description:
    - Updates Vertica configuration parameters.
options:
  name:
    description:
        - Name of the parameter to update.
    required: true
  value:
    description:
        - Value of the parameter to be set.
    required: true
  db:
    description:
        - Name of the Vertica database.
    required: false
    default: null
  cluster:
    description:
        - Name of the Vertica cluster.
    required: false
    default: localhost
  port:
    description:
        - Vertica cluster port to connect to.
    required: false
    default: 5433
  login_user:
    description:
        - The username used to authenticate with.
    required: false
    default: dbadmin
  login_password:
    description:
        - The password used to authenticate with.
    required: false
    default: null
notes:
  - The default authentication assumes that you are either logging in as or sudo'ing
    to the C(dbadmin) account on the host.
  - This module uses C(pyodbc), a Python ODBC database adapter. You must ensure
    that C(unixODBC) and C(pyodbc) is installed on the host and properly configured.
  - Configuring C(unixODBC) for Vertica requires C(Driver = /opt/vertica/lib64/libverticaodbc.so)
    to be added to the C(Vertica) section of either C(/etc/odbcinst.ini) or C($HOME/.odbcinst.ini)
    and both C(ErrorMessagesPath = /opt/vertica/lib64) and C(DriverManagerEncoding = UTF-16)
    to be added to the C(Driver) section of either C(/etc/vertica.ini) or C($HOME/.vertica.ini).
requirements: [ 'unixODBC', 'pyodbc' ]
author: "Dariusz Owczarek (@dareko)"
"""

EXAMPLES = """
- name: updating load_balance_policy
  vertica_configuration: name=failovertostandbyafter value='8 hours'
"""
import traceback

try:
    import pyodbc
except ImportError:
    pyodbc_found = False
else:
    pyodbc_found = True

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class NotSupportedError(Exception):
    pass


class CannotDropError(Exception):
    pass

# module specific functions


def get_configuration_facts(cursor, parameter_name=''):
    facts = {}
    cursor.execute("""
        select c.parameter_name, c.current_value, c.default_value
        from configuration_parameters c
        where c.node_name = 'ALL'
        and (? = '' or c.parameter_name ilike ?)
    """, parameter_name, parameter_name)
    while True:
        rows = cursor.fetchmany(100)
        if not rows:
            break
        for row in rows:
            facts[row.parameter_name.lower()] = {
                'parameter_name': row.parameter_name,
                'current_value': row.current_value,
                'default_value': row.default_value}
    return facts


def check(configuration_facts, parameter_name, current_value):
    parameter_key = parameter_name.lower()
    if current_value and current_value.lower() != configuration_facts[parameter_key]['current_value'].lower():
        return False
    return True


def present(configuration_facts, cursor, parameter_name, current_value):
    parameter_key = parameter_name.lower()
    changed = False
    if current_value and current_value.lower() != configuration_facts[parameter_key]['current_value'].lower():
        cursor.execute("select set_config_parameter('{0}', '{1}')".format(parameter_name, current_value))
        changed = True
    if changed:
        configuration_facts.update(get_configuration_facts(cursor, parameter_name))
    return changed

# module logic


def main():

    module = AnsibleModule(
        argument_spec=dict(
            parameter=dict(required=True, aliases=['name']),
            value=dict(default=None),
            db=dict(default=None),
            cluster=dict(default='localhost'),
            port=dict(default='5433'),
            login_user=dict(default='dbadmin'),
            login_password=dict(default=None, no_log=True),
        ), supports_check_mode=True)

    if not pyodbc_found:
        module.fail_json(msg="The python pyodbc module is required.")

    parameter_name = module.params['parameter']
    current_value = module.params['value']
    db = ''
    if module.params['db']:
        db = module.params['db']

    changed = False

    try:
        dsn = (
            "Driver=Vertica;"
            "Server={0};"
            "Port={1};"
            "Database={2};"
            "User={3};"
            "Password={4};"
            "ConnectionLoadBalance={5}"
        ).format(module.params['cluster'], module.params['port'], db,
                 module.params['login_user'], module.params['login_password'], 'true')
        db_conn = pyodbc.connect(dsn, autocommit=True)
        cursor = db_conn.cursor()
    except Exception as e:
        module.fail_json(msg="Unable to connect to database: {0}.".format(to_native(e)),
                         exception=traceback.format_exc())

    try:
        configuration_facts = get_configuration_facts(cursor)
        if module.check_mode:
            changed = not check(configuration_facts, parameter_name, current_value)
        else:
            try:
                changed = present(configuration_facts, cursor, parameter_name, current_value)
            except pyodbc.Error as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except NotSupportedError as e:
        module.fail_json(msg=to_native(e), ansible_facts={'vertica_configuration': configuration_facts})
    except CannotDropError as e:
        module.fail_json(msg=to_native(e), ansible_facts={'vertica_configuration': configuration_facts})
    except SystemExit:
        # avoid catching this on python 2.4
        raise
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=changed, parameter=parameter_name, ansible_facts={'vertica_configuration': configuration_facts})


if __name__ == '__main__':
    main()
