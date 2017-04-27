#!/usr/bin/python
# -*- coding: utf-8 -*-

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
module: oracle_system_parameter
short_description: Manage Oracle instance parameters.
description:
- Set, update or reset Oracle instance (ASM, RDBMS) parameters.
- The scope of change can be specified with I(scope).
- The returned value I(restart_required) indicates if a parameter changed requires an instance restart to take effect.
- The I(oracle_user) used to connect to the instance must have ALTER SYSTEM permissions.
options:
  name:
    description:
    - Parameter name
    required: true
  value:
    description:
    - Parameter value
    required: false
  scope:
    description:
    - Parameter scope
    default: both
    choices: ["both", "memory", "spfile"]
  state:
    description:
    - Parameter state
    required: False
    default: present
    choices: ["present", "absent"]
  oracle_host:
    description:
    - Hostname or IP address of Oracle DB
    required: False
    default: 127.0.0.1
  oracle_port:
    description:
    - Listener Port
    required: False
    default: 1521
  oracle_user:
    description:
    - Account to connect as
    required: False
    default: SYSTEM
  oracle_pass:
    description:
    - Password to be used to authenticate.
    - Can be omitted if environment variable C(ORACLE_PASS) is set.
    required: False
    default: None
  oracle_mode:
    description:
    - Connection mode.
    - Omit for normal connection.
    required: False
    default: None
    choices: ['SYSASM', 'SYSDBA', 'SYSOPER']
  oracle_sid:
    description:
    - Oracle SID to connect to
    required: False
    default: None
  oracle_service:
    description:
    - Oracle Net Service name to connect to
    required: False
    default: None
requirements:
- cx_Oracle
version_added: "2.4"
author: "Thomas Krahn (@nosmoht)"
'''

EXAMPLES = '''
- name: Ensure Oracle system parameter
  oracle_system_privilege:
    name: db_create_file_dest
    value: +DATA
    oracle_host: db.example.com
    oracle_port: 1523
    oracle_user: system
    oracle_pass: manager
    oracle_sid: ORCL
'''

RETURN = '''
system_parameter:
  description: Parameter as it currently exists within the instance
  returned: always
  type: dict
  samle:
    "system_parameter": {
      "display_value": "2G",
      "name": "sga_target",
      "value": "2147483648"
    }
sql:
  description: List of SQL statements executed to ensure the desired state
  returned: always
  type: list
  sample: ['ALTER SYSTEM SET "sga_mag_size" = 4G']
restart_required:
  description:
  - Boolean that determines if an instance restart is required to enable the parameter value.
  - Only true if a parameter I(scope) is C(spfile) and it's value was changed.
  returned: always
  type: bool
  sample: true
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oracle import OracleClient, HAS_ORACLE_LIB, oracle_argument_spec


class OracleSystemParameterClient(OracleClient):
    def __init__(self, module):
        super(OracleSystemParameterClient, self).__init__(module)

    def get_system_parameter(self, name, scope):
        if scope == 'spfile':
            source = 'v$spparameter'
        else:
            source = 'v$system_parameter'

        sql = 'select sp.name, sp.value, sp.display_value from %s sp where sp.name = :name' % (source)
        row = self.fetch_one(sql, {'name': name})
        if row:
            return {'name': row[0], 'value': row[1], 'display_value': row[2]}
        return None

    def get_alter_system_sql(self, name, scope, value=None, reset=False):
        if reset:
            sql = 'ALTER SYSTEM RESET "%s" SCOPE=%s' % (name, scope)
        else:
            sql = 'ALTER SYSTEM SET "%s" = \'%s\' SCOPE=%s' % (name, value, scope)
        return sql


def ensure(module, client):
    name = module.params['name'].lower()
    value = module.params['value']
    scope = module.params['scope']
    state = module.params['state']

    param = client.get_system_parameter(name, scope)

    sql = []
    if param:
        if state == 'absent' and param.get('value', None):
            sql.append(client.get_alter_system_sql(name=name, scope=scope, reset=True))
        if value not in [param.get('value'), param.get('display_value')]:
            sql.append(client.get_alter_system_sql(name=name, value=value, scope=scope, reset=False))

    restart_required = False
    if len(sql) > 0:
        if module.check_mode:
            module.exit_json(changed=True, system_parameter=param, sql=sql)
        for stmt in sql:
            client.execute_sql(stmt)
            if scope == 'spfile':
                restart_required = True
        return True, client.get_system_parameter(name=name, scope=scope), sql, restart_required
    return False, param, sql, restart_required


def main():
    argument_spec = oracle_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str', required=True),
            value=dict(type='str', required=False),
            scope=dict(type='str', default='both', choices=['both', 'memory', 'spfile']),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            oracle_mode=dict(type='str', required=None, default=None, choices=['SYSDBA', 'SYSASM', 'SYSOPER']),
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

    client = OracleSystemParameterClient(module)
    client.connect(host=module.params['oracle_host'],
                   port=module.params['oracle_port'],
                   user=module.params['oracle_user'],
                   password=module.params['oracle_pass'],
                   mode=module.params['oracle_mode'],
                   sid=module.params['oracle_sid'], service=module.params['oracle_service'])

    changed, system_parameter, sql, restart_required = ensure(module, client)
    module.exit_json(changed=changed, system_parameter=system_parameter, sql=sql, restart_required=restart_required)


if __name__ == '__main__':
    main()
