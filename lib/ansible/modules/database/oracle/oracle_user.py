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
module: oracle_user
short_description: Manage Oracle user accounts
description:
- Create, update, delete, lock or unlock Oracle database accounts.
- Grant and revoke system privileges and roles.
- Grant and revoke table privileges.
- Set tablespace quotas.
- The I(oracle_user) account used to connect to target database needs to have permissions to select from DBA views and execute the required SQL.
- All SQL statements that will/would be executed can be reviewed from the returned C(sql).
options:
  name:
    description:
    - Account name
    required: true
  default_tablespace:
    description:
    - Default tablespace name
    required: false
  password:
    description:
    - Password hash as in SYS.USER$.PASSWORD
    - The I(oracle_user) that connects to the instance must have permissions to read from SYS.USER$.
  password_mismatch:
    description:
    - Boolean to define if a mismatch of current and specified password is allowed.
    - If I(true), the password will not be changed if different.
    - If I(false), password will be changed.
    required: false
    default: false
    type: bool
  quotas:
    description:
    - List of dictionaries each describing a tablespace quota. See example.
    required: false
  roles:
    description:
    - List of roles granted to the user.
    - If an empty list I([]) is passed all roles will be revoked.
    - Roles granted to the user but not passed to the module will be revoked.
    - If parameter is omitted or I(None) roles will not be changed.
    - All passed items will be uppercased.
    required: false
    default: None
  sys_privs:
    description:
    - List of system privileges granted to the user.
    - If an empty list I([]) is passed all system privileges will be revoked.
    - If parameter is omitted or I(None) system privileges will not be changed.
    - System privileges granted to the user but not passed to the module will be revoked.
    - All items will be converted using uppercase.
    required: false
  state:
    description:
    - If I(present), I(locked) or I(unlocked) and the user does not exist it will be created.
    - If I(absent) and the user exists it will be locked, afterwards all session will be disconnected immediate and finally the user gets dropped.
    required: False
    default: present
    choices: ["present", "absent", "locked", "unlocked"]
  tab_privs:
    description:
    - List of dictionary each describing table privileges. See examples.
    - If parameter is omitted or I(None) table privileges will not be changed.
    - Table privileges that are granted but not passed to the module will be revoked.
    required: False
  temporary_tablespace:
    description:
    - Temporary tablespace name
    required: false
version_added: "2.4"
author: "Thomas Krahn (@nosmoht)"
extends_documentation_fragment:
- oracle
'''

EXAMPLES = '''
- name: Ensure Oracle user accounts
  oracle_user:
    name: pinky
    default_tablespace: DATA
    temporary_tablespace: TEMP
    password: 975C9ABC52D157E5
    quotas:
    - tablespace: DATA
      quota: UNLIMITED
    roles:
    - DBA
    sys_privs:
    - CONNECT
    - UNLIMITED TABLESPACE
    tab_privs:
    - owner: SYS
      table_name: USER$
      privileges:
      - SELECT
    oracle_host: oracle.example.com
    oracle_user: SYSTEM
    oracle_pass: manager
    oracle_sid: ORCL

- name: Ensure user brain is locked
  oracle_user:
    name: brain
    state: locked
    oracle_host: oracle.example.com
    oracle_user: SYSTEM
    oracle_pass: manager
    oracle_sid: ORCL

- name: Ensure user elvira is absent
  oracle_user:
    name: elvira
    state: absent
    oracle_host: oracle.example.com
    oracle_user: SYSTEM
    oracle_pass: manager
    oracle_sid: ORCL
'''

RETURN = '''
user:
  description: Dictionary that describes the current user account.
  returned: always
  type: dict
  sample:
    "user": {
      "account_status": "OPEN",
      "default_tablespace": "DATA",
      "name": "MYADMIN",
      "password": null,
      "quotas": [],
      "roles": [
        "DBA"
      ],
      "sys_privs": [
        "UNLIMITED TABLESPACE"
      ],
      "tab_privs": [],
      "temporary_tablespace": "TEMP"
    }
sql:
  description: List of SQL statements executed to ensure the desired state
  returned: always
  type: list
  sample: ["CREATE USER myadmin IDENTIFIED BY VALUES '1234567890'", "GRANT DBA TO myadmin"]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oracle import OracleClient, HAS_ORACLE_LIB, oracle_argument_spec
import re


class OracleAccountClient(OracleClient):
    def __init__(self, module):
        super(OracleAccountClient, self).__init__(module)

    def get_user(self, name, fetch_password=False):
        sql = 'SELECT default_tablespace, temporary_tablespace, account_status FROM dba_users WHERE username = :name'
        row = self.fetch_one(sql, {'name': name})
        if not row:
            return None

        data = {}
        data['name'] = name
        data['default_tablespace'] = row[0]
        data['temporary_tablespace'] = row[1]
        data['account_status'] = row[2]

        if fetch_password:
            sql = 'SELECT password FROM sys.user$ WHERE name = :name'
            row = self.fetch_one(sql, {'name': name})
            password = row[0]
        else:
            password = None
        data['password'] = password

        # Roles granted
        sql = 'SELECT granted_role FROM dba_role_privs WHERE grantee = :name'
        rows = self.fetch_all(sql, {'name': name})
        data['roles'] = [item[0] for item in rows]

        # System privileges granted
        sql = 'SELECT privilege FROM dba_sys_privs WHERE grantee = :name'
        rows = self.fetch_all(sql, {'name': name})
        data['sys_privs'] = [item[0] for item in rows]

        # Tablespace quotas
        sql = 'SELECT tablespace_name, max_bytes FROM dba_ts_quotas WHERE username = :name'
        rows = self.fetch_all(sql, {'name': name})
        data['quotas'] = [{'tablespace': item[0], 'max_bytes': item[1]} for item in rows]

        # Table privileges granted
        sql = '''\
            SELECT owner, table_name, LISTAGG(privilege, \',\') WITHIN GROUP (ORDER BY privilege) \
            FROM dba_tab_privs \
            WHERE grantee = :name \
            GROUP BY owner, table_name
        '''
        rows = self.fetch_all(sql, {'name': name})
        data['tab_privs'] = [{'owner': row[0], 'table_name': row[1], 'privileges': row[2].split(',')} for row in rows]

        return data

    def get_create_user_sql(self, name, userpass, default_tablespace=None, temporary_tablespace=None,
                            account_status=None):
        sql = "CREATE USER %s IDENTIFIED BY VALUES '%s'" % (name, userpass)
        if default_tablespace:
            sql = '%s DEFAULT TABLESPACE %s' % (sql, default_tablespace)
        if temporary_tablespace:
            sql = '%s TEMPORARY TABLESPACE %s' % (sql, temporary_tablespace)
        if account_status:
            sql = '%s ACCOUNT %s' % (sql, account_status)
        return sql

    def get_drop_user_sql(self, name):
        sql = 'DROP USER "%s" CASCADE' % (name)
        return sql

    def get_alter_user_sql(self, name, userpass=None, default_tablespace=None, temporary_tablespace=None,
                           account_status=None):
        sql = 'ALTER USER %s' % (name)
        if userpass:
            sql = "%s IDENTIFIED BY VALUES '%s'" % (sql, userpass)
            if default_tablespace:
                sql = '%s DEFAULT TABLESPACE %s' % (sql, default_tablespace)
            if temporary_tablespace:
                sql = '%s TEMPORARY TABLESPACE %s' % (sql, temporary_tablespace)
            if account_status:
                sql = '%s ACCOUNT %s' % (sql, account_status)
            return sql

    def get_grant_privilege_sql(self, user, priv, admin=False):
        sql = 'GRANT %s TO %s' % (priv, user)
        if admin:
            sql = '%s WITH ADMIN OPTION' % (sql)
        return sql

    def get_revoke_privilege_sql(self, user, priv):
        sql = 'REVOKE %s FROM %s' % (priv, user)
        return sql

    def map_state(self, state):
        if state in ['present', 'unlocked']:
            return 'UNLOCK'
        return 'LOCK'

    def map_account_state(self, account_status):
        if account_status == 'OPEN':
            return ['present', 'unlocked']
        return 'locked'

    def get_disconnect_sessions_sql(self, name, rac=False):
        if rac:
            source = 'gv$session'
            s = "''' || s.sid || ',' || s.serial# || '''',@' || s.inst_id || "
        else:
            source = 'v$session'
            s = "''' || s.sid || ',' || s.serial# || '''"

        sql = """
        declare
          cursor c is select sid, serial# from %s where username = '%s';
        begin
          for s in c loop
            execute immediate 'alter system disconnect session %s immediate';
          end loop;
        end;
        """
        return sql % (source, name, s)

    def get_alter_user_quota_sql(self, tablespace, username, quota):
        return 'ALTER USER "%s" QUOTA %s ON %s' % (username, quota, tablespace)

    def get_factor(self, unit):
        units = ['K', 'M', 'G', 'T']
        factor = 1024
        for u in units:
            if u == unit:
                break
            factor = factor * 1024
        return factor

    def get_max_bytes(self, quota):
        if quota is None:
            return None
        quota = quota.strip().upper()
        if quota == 'UNLIMITED':
            return -1
        match = re.match(r"([0-9]+)([A-Z]+)", quota, re.I)
        if match:
            items = match.groups()
            bytes = int(items[0])
            unit = items[1]
            return bytes * self.get_factor(unit)
        return quota

    def get_quota_list(self, target, actual):
        data = []
        for target_quota in target:
            quota = {}
            quota['tablespace'] = target_quota.get('tablespace')
            quota['target'] = target_quota.get('quota')
            for current_quota in actual:
                found = current_quota.get('tablespace') == target_quota.get('tablespace')
                if found:
                    quota['actual'] = current_quota.get('quota')
                    break
            data.append(quota)
        return data

    def merge_table_privs(self, target, merge, name):
        for item in merge:
            found = False
            owner = item.get('owner')
            table_name = item.get('table_name')
            privileges = item.get('privileges')
            for index, t in enumerate(target):
                found = owner == t.get('owner') and table_name == t.get('table_name')
                if found:
                    target[index][name] = privileges
                    break
            if not found:
                target.append({'owner': owner, 'table_name': table_name, name: privileges})
        return target

    def tab_privs_diff(self, target, actual):
        data = []
        data = self.merge_table_privs(data, target, 'target')
        data = self.merge_table_privs(data, actual, 'actual')

        for index, item in enumerate(data):
            data[index]['revoke'] = list(set(item.get('actual', [])) - set(item.get('target', [])))
            data[index]['grant'] = list(set(item.get('target', [])) - set(item.get('actual', [])))
        return data


def ensure(module, client):
    sql = []

    name = module.params['name'].upper()
    if module.params['default_tablespace']:
        default_tablespace = module.params['default_tablespace'].upper()
    else:
        default_tablespace = None
    password = module.params['password']
    password_mismatch = module.params['password_mismatch']

    quotas = module.params['quotas']

    if module.params['roles'] is not None:
        roles = [item.upper() for item in module.params['roles']]
    else:
        roles = None

    state = module.params['state']

    if module.params['temporary_tablespace']:
        temporary_tablespace = module.params['temporary_tablespace'].upper()
    else:
        temporary_tablespace = None

    if module.params['sys_privs']:
        sys_privs = [item.upper() for item in module.params['sys_privs']]
    else:
        sys_privs = None

    if module.params['tab_privs'] is not None:
        # module.fail_json(msg=module.params['tab_privs'])
        tab_privs = [{'owner': item.get('owner').strip().upper(),
                      'table_name': item.get('table_name').strip().upper(),
                      'privileges': [priv.upper() for priv in item.get('privileges')]}
                     for item in module.params['tab_privs']]
    else:
        tab_privs = None

    if password:
        fetch_password = True
    else:
        fetch_password = False
    user = client.get_user(name, fetch_password)

    # User doesn't exist
    if not user:
        # CREATE USER
        if state != 'absent':
            sql.append(client.get_create_user_sql(name=name,
                                                  userpass=password,
                                                  default_tablespace=default_tablespace,
                                                  temporary_tablespace=temporary_tablespace,
                                                  account_status=client.map_state(state)))
            # Sys privs
            if sys_privs is not None:
                for sys_priv in sys_privs:
                    sql.append(client.get_grant_privilege_sql(user=name, priv=sys_priv))
            # Roles
            if roles is not None:
                for role in roles:
                    sql.append(client.get_grant_privilege_sql(user=name, priv=role))
            # Quotas
            if quotas is not None:
                for quota in quotas:
                    sql.append(client.get_alter_user_quota_sql(tablespace=quota.get('tablespace'), username=name,
                                                               quota=quota.get('quota')))
            # Table privileges
            if tab_privs is not None:
                for tab_priv in tab_privs:
                    for priv in tab_priv.get('privileges', []):
                        priv_stmt = '%s ON "%s"."%s"' % (priv, tab_priv.get('owner'), tab_priv.get('table_name'))
                        sql.append(client.get_grant_privilege_sql(user=name, priv=priv_stmt))
    else:
        # DROP USER
        if state == 'absent':
            if user:
                sql.append(client.get_alter_user_sql(name=name, account_status=client.map_state('locked')))
                sql.append(client.get_disconnect_sessions_sql(name=name, rac=client.is_rac()))
                sql.append(client.get_drop_user_sql(name=name))
        else:
            if state not in client.map_account_state(user.get('account_status')):
                sql.append(client.get_alter_user_sql(
                    name=name, account_status=client.map_state(state)))
            if password and (user.get('password') != password and not password_mismatch):
                sql.append(client.get_alter_user_sql(name=name, userpass=password))
            if default_tablespace and user.get('default_tablespace') != default_tablespace:
                sql.append(client.get_alter_user_sql(
                    name=name, default_tablespace=default_tablespace))
            if temporary_tablespace and user.get('temporary_tablespace') != temporary_tablespace:
                sql.append(client.get_alter_user_sql(
                    name=name, temporary_tablespace=temporary_tablespace))

            if roles is not None:
                if user:
                    granted_roles = user.get('roles')
                else:
                    granted_roles = []

                priv_to_grant = list(set(roles) - set(granted_roles))
                for priv in priv_to_grant:
                    sql.append(client.get_grant_privilege_sql(user=name, priv=priv))

                priv_to_revoke = list(set(granted_roles) - set(roles))
                for priv in priv_to_revoke:
                    sql.append(client.get_revoke_privilege_sql(user=name, priv=priv))

            # System privileges
            if sys_privs is not None:
                if user:
                    granted_sys_privs = user.get('sys_privs')
                else:
                    granted_sys_privs = []
                privs_to_grant = list(set(sys_privs) - set(granted_sys_privs))
                for priv in privs_to_grant:
                    sql.append(client.get_grant_privilege_sql(user=name, priv=priv))
                priv_to_revoke = list(set(granted_sys_privs) - set(sys_privs))
                for priv in priv_to_revoke:
                    sql.append(client.get_revoke_privilege_sql(user=name, priv=priv))

            # Quotas
            if quotas is not None:
                quotas_list = client.get_quota_list(target=quotas, actual=user.get('quotas'))
                for quota in quotas_list:
                    if quota.get('target') != quota.get('actual'):
                        sql.append(
                            client.get_alter_user_quota_sql(tablespace=quota.get('tablespace'), username=name,
                                                            quota=quota.get('target')))

            # Table privileges
            if tab_privs is not None:
                privs_diff = client.tab_privs_diff(target=tab_privs, actual=user.get('tab_privs'))
                for diff in privs_diff:
                    if diff.get('revoke') is not None:
                        for revoke in diff.get('revoke'):
                            priv_stmt = '%s ON "%s"."%s"' % (revoke, diff.get('owner'), diff.get('table_name'))
                            sql.append(client.get_revoke_privilege_sql(user=name, priv=priv_stmt))
                    if diff.get('grant') is not None:
                        for grant in diff.get('grant'):
                            priv_stmt = '%s ON "%s"."%s"' % (grant, diff.get('owner'), diff.get('table_name'))
                            sql.append(client.get_grant_privilege_sql(user=name, priv=priv_stmt))

    if len(sql) != 0:
        if module.check_mode:
            module.exit_json(changed=True, sql=sql, user=user)
        for stmt in sql:
            client.execute_sql(stmt)
        return True, client.get_user(name), sql
    return False, user, sql


def main():
    argument_spec = oracle_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str', required=True),
            password=dict(type='str', required=False, no_log=True),
            password_mismatch=dict(type='bool', default=False),
            default_tablespace=dict(type='str', required=False),
            temporary_tablespace=dict(type='str', required=False),
            quotas=dict(type='list', required=False),
            roles=dict(type='list', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent', 'locked', 'unlocked']),
            sys_privs=dict(type='list', required=False),
            tab_privs=dict(type='list', required=False),
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

    client = OracleAccountClient(module)
    client.connect(host=module.params['oracle_host'],
                   port=module.params['oracle_port'],
                   user=module.params['oracle_user'],
                   password=module.params['oracle_pass'],
                   mode=module.params['oracle_mode'],
                   sid=module.params['oracle_sid'], service=module.params['oracle_service'])

    changed, user, sql = ensure(module, client)
    module.exit_json(changed=changed, user=user, sql=sql)


if __name__ == '__main__':
    main()
