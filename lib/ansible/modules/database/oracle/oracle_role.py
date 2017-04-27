#!/usr/bin/python
#  -*- coding: utf-8 -*-

# Copyright (c) 2017 Thomas Krahn (@Nosmoht)
# All rights reserved.
#
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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: oracle_role
short_description: Manage Oracle roles
description:
- Modify Oracle system parameters
options:
  name:
    description:
    - Role name
    required: true
  roles:
    description:
      - List of roles granted to the role.
      - If an empty list C([]) is specified all granted roles will be revoked.
      - All items will be converted using uppercase.
    required: false
    default: None
  sys_privs:
    description:
      - List of system privileges granted to the role.
      - If an empty list C([]) is specified all granted system privileges will be revoked.
      - All items will be converted using uppercase.
  state:
    description:
    - Parameter state
    required: False
    default: present
    choices: ["present", "absent"]
version_added: "2.4"
author: "Thomas Krahn (@nosmoht)"
extends_documentation_fragment:
- oracle
'''

EXAMPLES = '''
- name: Ensure Oracle role
  oracle_role:
    name: APP_ROLE
    roles:
    - PLUSTRACE
    sys_privs:
    - CONNECT
    oracle_host: db.example.com
    oracle_port: 1523
    oracle_user: system
    oracle_pass: manager
    oracle_sid: ORCL
'''

RETURN = '''
role:
  description: Role and attributes as it currently exists within the database
  returned: always
  type: dict
sql:
  description: List of SQL statements executed to ensure the desired state
  returned: always
  type: list
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oracle import OracleClient, HAS_ORACLE_LIB, oracle_argument_spec


class OracleRoleClient(OracleClient):
    def __init__(self, module):
        super(OracleRoleClient, self).__init__(module)

    def get_role(self, name):
        data = {}

        sql = 'SELECT role, password_required FROM dba_roles WHERE role = :name'
        row = self.fetch_one(sql, {'name': name})
        if not row:
            return None

        data['name'] = row[0]
        data['password_required'] = row[1]

        sql = 'SELECT privilege FROM dba_sys_privs WHERE grantee = :name'
        row = self.fetch_all(sql, {'name': name})
        data['sys_privs'] = [item[0] for item in row]

        sql = 'SELECT granted_role FROM DBA_ROLE_PRIVS WHERE grantee = :name'
        row = self.fetch_all(sql, {'name': name})
        data['roles'] = [item[0] for item in row]

        return data

    def get_create_role_sql(self, name, password_required=None):
        sql = 'CREATE ROLE "%s"' % (name)
        #   if password_required:
        #       sql='{sql}'
        return sql

    def get_drop_role_sql(self, name):
        sql = 'DROP ROLE "%s"' % (name)
        return sql

    def get_privilege_sql(self, action, name, priv):
        if action == 'REVOKE':
            from_to = 'FROM'
        else:
            from_to = 'TO'
        sql = '%s %s %s "%s"' % (action, priv, from_to, name)
        return sql

    def get_grant_privilege_sql(self, name, priv):
        return self.get_privilege_sql(action='GRANT', priv=priv, name=name)

    def get_revoke_privilege_sql(self, name, priv):
        return self.get_privilege_sql(action='REVOKE', priv=priv, name=name)


def ensure(module, client):
    name = module.params['name'].upper()
    if module.params['roles'] is not None:
        roles = [item.upper() for item in module.params['roles']]
    else:
        roles = None

    state = module.params['state']
    if module.params['sys_privs'] is not None:
        sys_privs = [item.upper() for item in module.params['sys_privs']]
    else:
        sys_privs = None

    role = client.get_role(name)

    sql = []

    if state == 'absent':
        if not role:
            sql.append(client.get_drop_role_sql(name=name))
    else:
        if role:
            sql.append(client.get_create_role_sql(name=name))

        # Roles
        if roles is not None:
            if role:
                granted_roles = role.get('roles')
            else:
                granted_roles = []
            roles_to_grant = list(set(roles) - set(granted_roles))
            for item in roles_to_grant:
                sql.append(client.get_grant_privilege_sql(priv=item, name=name))

            roles_to_revoke = list(set(granted_roles) - set(roles))
            for item in roles_to_revoke:
                sql.append(client.get_revoke_privilege_sql(priv=item, name=name))

        # System privileges
        if sys_privs is not None:
            if role:
                granted_sys_privs = role.get('sys_privs')
            else:
                granted_sys_privs = []
            privs_to_grant = list(set(sys_privs) - set(granted_sys_privs))
            for item in privs_to_grant:
                sql.append(client.get_grant_privilege_sql(priv=item, name=name))

            privs_to_revoke = list(set(granted_sys_privs) - set(sys_privs))
            for item in privs_to_revoke:
                sql.append(client.get_revoke_privilege_sql(priv=item, name=name))

    if len(sql) > 0:
        if module.check_mode:
            module.exit_json(changed=True, role=role, sql=sql)
        for stmt in sql:
            client.execute_sql(stmt)
        return True, client.get_role(name), sql

    return False, role, sql


def main():
    argument_spec = oracle_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str', required=True),
            roles=dict(type='list', default=None),
            state=dict(type='str', default='present',
                       choices=['present', 'absent']),
            sys_privs=dict(type='list', default=None),
        ),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[['oracle_sid', 'oracle_service']],
        mutually_exclusive=[['oracle_sid', 'oracle_service']],
        supports_check_mode=True,
    )

    if not HAS_ORACLE_LIB:
        module.fail_json(msg='cx_Oracle not found. Needs to be installed. See http://cx-oracle.sourceforge.net/')

    client = OracleRoleClient(module)
    client.connect(host=module.params['oracle_host'],
                   port=module.params['oracle_port'],
                   user=module.params['oracle_user'],
                   password=module.params['oracle_pass'],
                   mode=module.params['oracle_mode'],
                   sid=module.params['oracle_sid'], service=module.params['oracle_service'])

    changed, role, sql = ensure(module, client)
    module.exit_json(changed=changed, role=role, sql=sql)


if __name__ == '__main__':
    main()
