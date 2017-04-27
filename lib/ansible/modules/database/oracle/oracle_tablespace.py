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
module: oracle_tablespace
short_description: Manage Oracle tablespaces and datafiles
description:
- Create, alter or delete Oracle tablespaces.
- Add and modify datafiles.
- All datafiles of a tablespace will be handled equal!
- For example, if I(init_size) is set the module will ensure the same value for all data files of a tablespace.
options:
  name:
    description:
    - Tablespace name
    required: true
  num_datafiles:
    description:
    - Amount of datafiles to ensure within the tablespace.
    - If current amount is lower than specified new datafiles will be added until I(num_datafiles) are reached.
    - Datafiles will not be removed if more do exist.
    required: false
    default: 1
  autoextend:
    description:
    - Boolean to define if autoextend of datafiles is enabled or disabled.
    required: false
    default: false
    type: bool
  init_size:
    description:
    - Initial size of a datafile if it will be created.
    - Values must by specified as bytes or have one of ['K','M','G','T','P','E'] as suffix.
    required: false
    default: 1M
  next_size:
    description:
    - Size of the next extend of each datafile if autoextend is enabled.
    - Values must by specified as bytes or have one of ['K','M','G','T','P','E'] as suffix.
    required: false
    default: 0
  max_size:
    description:
    - Max size of each datafile if autoextend is enabled.
    - Values must by specified as bytes or have one of ['K','M','G','T','P','E'] as suffix.
    required: false
    default: 0
  state:
    description:
    - Tablespace state
    required: False
    default: present
    choices: ["present", "absent"]
version_added: "2.4"
author: "Thomas Krahn (@nosmoht)"
extends_documentation_fragment:
- oracle
'''

EXAMPLES = '''
# Ensure tablespace USERS exist, can grow up to 2G in 16M steps.
# Tablespace will be created if it does not exist.
- name: Ensure tablespace users is present
  oracle_tablespace:
    name: USERS
    state: present
    init_size: 100M
    autoextend: true
    next_size: 16M
    max_size: 2G
    oracle_host: db.example.com
    oracle_user: system
    oracle_pass: manager
    oracle_sid: ORCL

# Ensure tablespace TEST does not exist.
- name: Ensure tablespace users is present
  oracle_tablespace:
    name: TEST
    state: absent
    oracle_host: db.example.com
    oracle_user: system
    oracle_pass: manager
    oracle_sid: ORCL
'''

RETURN = '''
tablespace:
  description: Dictionary describing the tablespace as it currently exists within the database
  returned: always
  type: dict
sql:
  description: List of SQL statements executed to ensure the desired state
  returned: always
  type: list
  sample: ['CREATE TABLESPACE data SIZE 1M AUTOEXTEND ON NEXT 1M MAXSIZE UNLIMITED']
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oracle import OracleClient, HAS_ORACLE_LIB, oracle_argument_spec
import re


class OracleSystemParameterClient(OracleClient):
    def __init__(self, module):
        super(OracleSystemParameterClient, self).__init__(module)

    def get_datafiles(self, ts):
        sql = 'SELECT file_id, file_name, bytes, maxbytes, increment_by FROM dba_data_files WHERE tablespace_name = :name'
        data = self.fetch_all(sql, {'name': ts})
        datafiles = []
        for row in data:
            datafiles.append(
                {'file_id': row[0], 'name': row[1], 'bytes': row[2], 'maxbytes': row[3], 'increment_by': row[4]})
        return datafiles

    def get_tablespace(self, name):
        sql = 'SELECT ts#, name, bigfile FROM v$tablespace WHERE name = :name'
        row = self.fetch_one(sql, {'name': name})

        if not row:
            return None
        ts = {'ts_nr': row[0], 'name': row[1], 'bigfile': row[2]}
        ts['datafiles'] = self.get_datafiles(ts=name)

        return ts

    def get_create_tablespace_sql(self, name, blocksize, num_datafiles, init_size, autoextend, next_size, max_size):
        sql = 'CREATE TABLESPACE %s DATAFILE' % (name)
        for i in range(num_datafiles):
            if i > 0:
                sql = '%s,' % (sql)
            sql = '%s SIZE %s' % (sql, init_size)
            if autoextend:
                sql = '%s AUTOEXTEND ON NEXT %s MAXSIZE %s' % (sql, next_size, max_size)
            else:
                sql = '%s AUTOEXTEND OFF' % (sql)

        if blocksize:
            sql = '%s BLOCKSIZE %s' % (sql, blocksize)
        return sql

    def get_drop_tablespace_sql(self, name):
        sql = 'DROP TABLESPACE %s INCLUDING CONTENTS AND DATAFILES' % (name)
        return sql

    def get_alter_datafile_sql(self, file_id, autoextend, next_size, max_size):
        sql = 'ALTER DATABASE DATAFILE %s' % (file_id)
        if not autoextend:
            sql = '%s AUTOEXTEND OFF' % (sql)
        else:
            sql = '%s AUTOEXTEND ON NEXT %s MAXSIZE %s' % (sql, next_size, max_size)
        return sql

    def get_resize_datafile_sql(self, file_id, size):
        return 'ALTER DATABASE DATAFILE %s RESIZE %s' % (file_id, size)

    def size_to_bytes(self, size, blocksize):
        # Return amount of bytes represented by size
        # Example: size_to_bytes("16M") = 16777216
        # Note: UNLIMITED is NOT 4194304 * blocksize, but 4194302 * blocksize
        if size.upper() == 'UNLIMITED':
            return ((4 * 1024 * 1024) - 2) * blocksize
        m = re.match("([0-9]+)\s*([kKmMgGtTpPeE])?", size)
        if not m:
            return None
        num = int(m.group(1))
        if not m.group(2):
            return num
        unit = m.group(2).upper()
        for f in ("K", "M", "G", "T", "P", "E"):
            num *= 1024
            if f == unit:
                return num
        return None


def ensure(module, client):
    name = module.params['name'].upper()
    blocksize = module.params['blocksize']
    num_datafiles = module.params['num_datafiles']
    init_size = module.params['init_size']
    autoextend = module.params['autoextend']
    next_size = module.params['next_size']
    max_size = module.params['max_size']
    state = module.params['state']
    sql = []

    tbs = client.get_tablespace(name=name)

    if state == 'present':
        if not tbs:
            sql.append(client.get_create_tablespace_sql(name=name, blocksize=blocksize, num_datafiles=num_datafiles,
                                                        init_size=init_size, autoextend=autoextend, next_size=next_size,
                                                        max_size=max_size))
        else:
            for df in tbs.get('datafiles', None):
                block_size = client.size_to_bytes(blocksize, None)
                byte = client.size_to_bytes(init_size, block_size)
                maxbytes = client.size_to_bytes(max_size, block_size)
                increment_by = client.size_to_bytes(next_size, block_size) / block_size
                if df.get('maxbytes', None) != maxbytes or df.get('increment_by') != increment_by:
                    sql.append(
                        client.get_alter_datafile_sql(file_id=df.get('file_id'), autoextend=autoextend,
                                                      next_size=next_size,
                                                      max_size=max_size))
                if (not autoextend and df.get('bytes') > byte):
                    sql.append(client.get_resize_datafile_sql(file_id=df.get('file_id'), size=maxbytes))
    elif state == 'absent':
        if tbs:
            sql.append(client.get_drop_tablespace_sql(name=name))

    if len(sql) > 0:
        if module.check_mode:
            module.exit_json(changed=True, tablespace=tbs, sql=sql)
        for stmt in sql:
            client.execute_sql(sql=stmt)
        return True, client.get_tablespace(name=name), sql
    return False, tbs, sql


def main():
    argument_spec = oracle_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str', required=True),
            blocksize=dict(type='str', required=False, default='8k'),
            num_datafiles=dict(type='int', required=False, default=1),
            autoextend=dict(type='bool', required=False, default=False),
            init_size=dict(type='str', required=False, default='1M'),
            next_size=dict(type='str', required=False, default='0'),
            max_size=dict(type='str', required=False, default='0'),
            state=dict(type='str', default='present', choices=['present', 'absent']),
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

    changed, tablespace, sql = ensure(module, client)
    module.exit_json(changed=changed, tablespace=tablespace, sql=sql)


if __name__ == '__main__':
    main()
