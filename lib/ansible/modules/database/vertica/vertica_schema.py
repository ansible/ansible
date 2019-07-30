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
module: vertica_schema
version_added: '2.0'
short_description: Adds or removes Vertica database schema and roles.
description:
  - Adds or removes Vertica database schema and, optionally, roles
    with schema access privileges.
  - A schema will not be removed until all the objects have been dropped.
  - In such a situation, if the module tries to remove the schema it
    will fail and only remove roles created for the schema if they have
    no dependencies.
options:
  name:
    description:
      - Name of the schema to add or remove.
    required: true
  usage_roles:
    description:
      - Comma separated list of roles to create and grant usage access to the schema.
    aliases: ['usage_role']
  create_roles:
    description:
      - Comma separated list of roles to create and grant usage and create access to the schema.
    aliases: ['create_role']
  owner:
    description:
      - Name of the user to set as owner of the schema.
  state:
    description:
      - Whether to create C(present), or drop C(absent) a schema.
    default: present
    choices: ['present', 'absent']
  db:
    description:
      - Name of the Vertica database.
  cluster:
    description:
      - Name of the Vertica cluster.
    default: localhost
  port:
    description:
      - Vertica cluster port to connect to.
    default: 5433
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
- name: creating a new vertica schema
  vertica_schema: name=schema_name db=db_name state=present

- name: creating a new schema with specific schema owner
  vertica_schema: name=schema_name owner=dbowner db=db_name state=present

- name: creating a new schema with roles
  vertica_schema:
    name=schema_name
    create_roles=schema_name_all
    usage_roles=schema_name_ro,schema_name_rw
    db=db_name
    state=present
"""
import traceback

PYODBC_IMP_ERR = None
try:
    import pyodbc
except ImportError:
    PYODBC_IMP_ERR = traceback.format_exc()
    pyodbc_found = False
else:
    pyodbc_found = True

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native


class NotSupportedError(Exception):
    pass


class CannotDropError(Exception):
    pass

# module specific functions


def get_schema_facts(cursor, schema=''):
    facts = {}
    cursor.execute("""
        select schema_name, schema_owner, create_time
        from schemata
        where not is_system_schema and schema_name not in ('public', 'TxtIndex')
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
        on g.grantee_id = r.role_id and g.object_type='SCHEMA'
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


def update_roles(schema_facts, cursor, schema,
                 existing, required,
                 create_existing, create_required):
    for role in set(existing + create_existing) - set(required + create_required):
        cursor.execute("drop role {0} cascade".format(role))
    for role in set(create_existing) - set(create_required):
        cursor.execute("revoke create on schema {0} from {1}".format(schema, role))
    for role in set(required + create_required) - set(existing + create_existing):
        cursor.execute("create role {0}".format(role))
        cursor.execute("grant usage on schema {0} to {1}".format(schema, role))
    for role in set(create_required) - set(create_existing):
        cursor.execute("grant create on schema {0} to {1}".format(schema, role))


def check(schema_facts, schema, usage_roles, create_roles, owner):
    schema_key = schema.lower()
    if schema_key not in schema_facts:
        return False
    if owner and owner.lower() == schema_facts[schema_key]['owner'].lower():
        return False
    if sorted(usage_roles) != sorted(schema_facts[schema_key]['usage_roles']):
        return False
    if sorted(create_roles) != sorted(schema_facts[schema_key]['create_roles']):
        return False
    return True


def present(schema_facts, cursor, schema, usage_roles, create_roles, owner):
    schema_key = schema.lower()
    if schema_key not in schema_facts:
        query_fragments = ["create schema {0}".format(schema)]
        if owner:
            query_fragments.append("authorization {0}".format(owner))
        cursor.execute(' '.join(query_fragments))
        update_roles(schema_facts, cursor, schema, [], usage_roles, [], create_roles)
        schema_facts.update(get_schema_facts(cursor, schema))
        return True
    else:
        changed = False
        if owner and owner.lower() != schema_facts[schema_key]['owner'].lower():
            raise NotSupportedError((
                "Changing schema owner is not supported. "
                "Current owner: {0}."
            ).format(schema_facts[schema_key]['owner']))
        if sorted(usage_roles) != sorted(schema_facts[schema_key]['usage_roles']) or \
           sorted(create_roles) != sorted(schema_facts[schema_key]['create_roles']):

            update_roles(schema_facts, cursor, schema,
                         schema_facts[schema_key]['usage_roles'], usage_roles,
                         schema_facts[schema_key]['create_roles'], create_roles)
            changed = True
        if changed:
            schema_facts.update(get_schema_facts(cursor, schema))
        return changed


def absent(schema_facts, cursor, schema, usage_roles, create_roles):
    schema_key = schema.lower()
    if schema_key in schema_facts:
        update_roles(schema_facts, cursor, schema,
                     schema_facts[schema_key]['usage_roles'], [], schema_facts[schema_key]['create_roles'], [])
        try:
            cursor.execute("drop schema {0} restrict".format(schema_facts[schema_key]['name']))
        except pyodbc.Error:
            raise CannotDropError("Dropping schema failed due to dependencies.")
        del schema_facts[schema_key]
        return True
    else:
        return False

# module logic


def main():

    module = AnsibleModule(
        argument_spec=dict(
            schema=dict(required=True, aliases=['name']),
            usage_roles=dict(default=None, aliases=['usage_role']),
            create_roles=dict(default=None, aliases=['create_role']),
            owner=dict(default=None),
            state=dict(default='present', choices=['absent', 'present']),
            db=dict(default=None),
            cluster=dict(default='localhost'),
            port=dict(default='5433'),
            login_user=dict(default='dbadmin'),
            login_password=dict(default=None, no_log=True),
        ), supports_check_mode=True)

    if not pyodbc_found:
        module.fail_json(msg=missing_required_lib('pyodbc'), exception=PYODBC_IMP_ERR)

    schema = module.params['schema']
    usage_roles = []
    if module.params['usage_roles']:
        usage_roles = module.params['usage_roles'].split(',')
        usage_roles = filter(None, usage_roles)
    create_roles = []
    if module.params['create_roles']:
        create_roles = module.params['create_roles'].split(',')
        create_roles = filter(None, create_roles)
    owner = module.params['owner']
    state = module.params['state']
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
        module.fail_json(msg="Unable to connect to database: {0}.".format(to_native(e)))

    try:
        schema_facts = get_schema_facts(cursor)
        if module.check_mode:
            changed = not check(schema_facts, schema, usage_roles, create_roles, owner)
        elif state == 'absent':
            try:
                changed = absent(schema_facts, cursor, schema, usage_roles, create_roles)
            except pyodbc.Error as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())
        elif state == 'present':
            try:
                changed = present(schema_facts, cursor, schema, usage_roles, create_roles, owner)
            except pyodbc.Error as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except NotSupportedError as e:
        module.fail_json(msg=to_native(e), ansible_facts={'vertica_schemas': schema_facts})
    except CannotDropError as e:
        module.fail_json(msg=to_native(e), ansible_facts={'vertica_schemas': schema_facts})
    except SystemExit:
        # avoid catching this on python 2.4
        raise
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=changed, schema=schema, ansible_facts={'vertica_schemas': schema_facts})


if __name__ == '__main__':
    main()
