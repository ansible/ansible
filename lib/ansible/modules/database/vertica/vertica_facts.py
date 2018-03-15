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
module: vertica_facts
version_added: '2.0'
short_description: Gathers Vertica database facts.
description:
  - Gathers Vertica database facts.
options:
  cluster:
    description:
      - Name of the cluster running the schema.
    default: localhost
  port:
    description:
      Database port to connect to.
    default: 5433
  db:
    description:
      - Name of the database running the schema.
  login_user:
    description:
      - The username used to authenticate with.
    default: dbadmin
  login_password:
    description:
      - The password used to authenticate with.
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
- name: gathering vertica facts
  vertica_facts: db=db_name
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

# module specific functions


def get_schema_facts(cursor, schema=''):
    facts = {}
    cursor.execute("""
        select schema_name, schema_owner, create_time
        from schemata
        where not is_system_schema and schema_name not in ('public')
        and (? = '' or schema_name ilike ?)
    """, schema, schema)
    while True:
        rows = cursor.fetchmany(100)
        if not rows:
            break
        for row in rows:
            facts[row.schema_name.lower()] = {
                'name': row.schema_name,
                'owner': row.schema_owner,
                'create_time': str(row.create_time),
                'usage_roles': [],
                'create_roles': []}
    cursor.execute("""
        select g.object_name as schema_name, r.name as role_name,
        lower(g.privileges_description) privileges_description
        from roles r join grants g
        on g.grantee = r.name and g.object_type='SCHEMA'
        and g.privileges_description like '%USAGE%'
        and g.grantee not in ('public', 'dbadmin')
        and (? = '' or g.object_name ilike ?)
    """, schema, schema)
    while True:
        rows = cursor.fetchmany(100)
        if not rows:
            break
        for row in rows:
            schema_key = row.schema_name.lower()
            if 'create' in row.privileges_description:
                facts[schema_key]['create_roles'].append(row.role_name)
            else:
                facts[schema_key]['usage_roles'].append(row.role_name)
    return facts


def get_user_facts(cursor, user=''):
    facts = {}
    cursor.execute("""
        select u.user_name, u.is_locked, u.lock_time,
        p.password, p.acctexpired as is_expired,
        u.profile_name, u.resource_pool,
        u.all_roles, u.default_roles
        from users u join password_auditor p on p.user_id = u.user_id
        where not u.is_super_user
        and (? = '' or u.user_name ilike ?)
     """, user, user)
    while True:
        rows = cursor.fetchmany(100)
        if not rows:
            break
        for row in rows:
            user_key = row.user_name.lower()
            facts[user_key] = {
                'name': row.user_name,
                'locked': str(row.is_locked),
                'password': row.password,
                'expired': str(row.is_expired),
                'profile': row.profile_name,
                'resource_pool': row.resource_pool,
                'roles': [],
                'default_roles': []}
            if row.is_locked:
                facts[user_key]['locked_time'] = str(row.lock_time)
            if row.all_roles:
                facts[user_key]['roles'] = row.all_roles.replace(' ', '').split(',')
            if row.default_roles:
                facts[user_key]['default_roles'] = row.default_roles.replace(' ', '').split(',')
    return facts


def get_role_facts(cursor, role=''):
    facts = {}
    cursor.execute("""
        select r.name, r.assigned_roles
        from roles r
        where (? = '' or r.name ilike ?)
    """, role, role)
    while True:
        rows = cursor.fetchmany(100)
        if not rows:
            break
        for row in rows:
            role_key = row.name.lower()
            facts[role_key] = {
                'name': row.name,
                'assigned_roles': []}
            if row.assigned_roles:
                facts[role_key]['assigned_roles'] = row.assigned_roles.replace(' ', '').split(',')
    return facts


def get_configuration_facts(cursor, parameter=''):
    facts = {}
    cursor.execute("""
        select c.parameter_name, c.current_value, c.default_value
        from configuration_parameters c
        where c.node_name = 'ALL'
        and (? = '' or c.parameter_name ilike ?)
    """, parameter, parameter)
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


def get_node_facts(cursor, schema=''):
    facts = {}
    cursor.execute("""
        select node_name, node_address, export_address, node_state, node_type,
            catalog_path
        from nodes
    """)
    while True:
        rows = cursor.fetchmany(100)
        if not rows:
            break
        for row in rows:
            facts[row.node_address] = {
                'node_name': row.node_name,
                'export_address': row.export_address,
                'node_state': row.node_state,
                'node_type': row.node_type,
                'catalog_path': row.catalog_path}
    return facts

# module logic


def main():

    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(default='localhost'),
            port=dict(default='5433'),
            db=dict(default=None),
            login_user=dict(default='dbadmin'),
            login_password=dict(default=None, no_log=True),
        ), supports_check_mode=True)

    if not pyodbc_found:
        module.fail_json(msg="The python pyodbc module is required.")

    db = ''
    if module.params['db']:
        db = module.params['db']

    try:
        dsn = (
            "Driver=Vertica;"
            "Server=%s;"
            "Port=%s;"
            "Database=%s;"
            "User=%s;"
            "Password=%s;"
            "ConnectionLoadBalance=%s"
        ) % (module.params['cluster'], module.params['port'], db,
             module.params['login_user'], module.params['login_password'], 'true')
        db_conn = pyodbc.connect(dsn, autocommit=True)
        cursor = db_conn.cursor()
    except Exception as e:
        module.fail_json(msg="Unable to connect to database: %s." % to_native(e), exception=traceback.format_exc())

    try:
        schema_facts = get_schema_facts(cursor)
        user_facts = get_user_facts(cursor)
        role_facts = get_role_facts(cursor)
        configuration_facts = get_configuration_facts(cursor)
        node_facts = get_node_facts(cursor)
        module.exit_json(changed=False,
                         ansible_facts={'vertica_schemas': schema_facts,
                                        'vertica_users': user_facts,
                                        'vertica_roles': role_facts,
                                        'vertica_configuration': configuration_facts,
                                        'vertica_nodes': node_facts})
    except NotSupportedError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except SystemExit:
        # avoid catching this on python 2.4
        raise
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
