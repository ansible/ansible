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
module: vertica_role
version_added: '2.0'
short_description: Adds or removes Vertica database roles and assigns roles to them.
description:
  - Adds or removes Vertica database role and, optionally, assign other roles.
options:
  name:
    description:
      - Name of the role to add or remove.
    required: true
  assigned_roles:
    description:
      - Comma separated list of roles to assign to the role.
    aliases: ['assigned_role']
  state:
    description:
      - Whether to create C(present), drop C(absent) or lock C(locked) a role.
    choices: ['present', 'absent']
    default: present
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
- name: creating a new vertica role
  vertica_role: name=role_name db=db_name state=present

- name: creating a new vertica role with other role assigned
  vertica_role: name=role_name assigned_role=other_role_name state=present
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


def update_roles(role_facts, cursor, role,
                 existing, required):
    for assigned_role in set(existing) - set(required):
        cursor.execute("revoke {0} from {1}".format(assigned_role, role))
    for assigned_role in set(required) - set(existing):
        cursor.execute("grant {0} to {1}".format(assigned_role, role))


def check(role_facts, role, assigned_roles):
    role_key = role.lower()
    if role_key not in role_facts:
        return False
    if assigned_roles and sorted(assigned_roles) != sorted(role_facts[role_key]['assigned_roles']):
        return False
    return True


def present(role_facts, cursor, role, assigned_roles):
    role_key = role.lower()
    if role_key not in role_facts:
        cursor.execute("create role {0}".format(role))
        update_roles(role_facts, cursor, role, [], assigned_roles)
        role_facts.update(get_role_facts(cursor, role))
        return True
    else:
        changed = False
        if assigned_roles and (sorted(assigned_roles) != sorted(role_facts[role_key]['assigned_roles'])):
            update_roles(role_facts, cursor, role,
                         role_facts[role_key]['assigned_roles'], assigned_roles)
            changed = True
        if changed:
            role_facts.update(get_role_facts(cursor, role))
        return changed


def absent(role_facts, cursor, role, assigned_roles):
    role_key = role.lower()
    if role_key in role_facts:
        update_roles(role_facts, cursor, role,
                     role_facts[role_key]['assigned_roles'], [])
        cursor.execute("drop role {0} cascade".format(role_facts[role_key]['name']))
        del role_facts[role_key]
        return True
    else:
        return False

# module logic


def main():

    module = AnsibleModule(
        argument_spec=dict(
            role=dict(required=True, aliases=['name']),
            assigned_roles=dict(default=None, aliases=['assigned_role']),
            state=dict(default='present', choices=['absent', 'present']),
            db=dict(default=None),
            cluster=dict(default='localhost'),
            port=dict(default='5433'),
            login_user=dict(default='dbadmin'),
            login_password=dict(default=None, no_log=True),
        ), supports_check_mode=True)

    if not pyodbc_found:
        module.fail_json(msg=missing_required_lib('pyodbc'), exception=PYODBC_IMP_ERR)

    role = module.params['role']
    assigned_roles = []
    if module.params['assigned_roles']:
        assigned_roles = module.params['assigned_roles'].split(',')
        assigned_roles = filter(None, assigned_roles)
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
        role_facts = get_role_facts(cursor)
        if module.check_mode:
            changed = not check(role_facts, role, assigned_roles)
        elif state == 'absent':
            try:
                changed = absent(role_facts, cursor, role, assigned_roles)
            except pyodbc.Error as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())
        elif state == 'present':
            try:
                changed = present(role_facts, cursor, role, assigned_roles)
            except pyodbc.Error as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except NotSupportedError as e:
        module.fail_json(msg=to_native(e), ansible_facts={'vertica_roles': role_facts})
    except CannotDropError as e:
        module.fail_json(msg=to_native(e), ansible_facts={'vertica_roles': role_facts})
    except SystemExit:
        # avoid catching this on python 2.4
        raise
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=changed, role=role, ansible_facts={'vertica_roles': role_facts})


if __name__ == '__main__':
    main()
