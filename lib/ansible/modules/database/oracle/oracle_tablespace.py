#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: oracle_tablespace
short_description: Manage Oracle tablespaces and datafiles
description:
- Create and delete Oracle tablespaces.
- Add and modify datafiles.
- All datafiles will be handled equal.
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
  init_size:
    description:
    - Initial size of a datafile if it will be created.
    required: false
    default: 1M
  next_size:
    description:
    - Size of the next extend of each datafile if autoextend is enabled.
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
    - Password to be used to authenticate
    required: False
    default: manager
  oracle_sid:
    description:
    - Oracle SID to use for connection
    required: False
    default: None
  oracle_service:
    description:
    - Oracle Service name to use for connection
    required: False
    default: None
notes:
- Requires cx_Oracle
author: "Thomas Krahn (@nosmoht)"
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

try:
    import cx_Oracle

    oracleclient_found = True
except ImportError:
    oracleclient_found = False


def map_mode(mode):
    if mode == 'SYSDBA':
        return cx_Oracle.SYSDBA
    elif mode == 'SYSOPER':
        return cx_Oracle.SYSOPER
    else:
        return None


def create_connection(module, user, password, host, port, sid=None, service=None, mode=None):
    if sid:
        dsn = cx_Oracle.makedsn(host=host, port=port, sid=sid)
    else:
        dsn = cx_Oracle.makedsn(host=host, port=port, service_name=service)

    try:
        if mode:
            conn = cx_Oracle.connect(
                user=user, password=password, dsn=dsn, mode=map_mode(mode))
        else:
            conn = cx_Oracle.connect(user=user, password=password, dsn=dsn)
        return conn
    except cx_Oracle.DatabaseError as e:
        module.fail_json(msg='{dsn}: {err}'.format(dsn=dsn, err=str(e)))


def execute_sql(module, con, sql):
    cur = con.cursor()
    try:
        cur.execute(sql)
    except cx_Oracle.DatabaseError as e:
        module.fail_json(msg='{sql}: {err}'.format(sql=sql, err=e))
    cur.close()


def fetch_all(module, cur, sql, name):
    try:
        cur.prepare(sql)
        cur.execute(None, dict(name=name))
        rows = cur.fetchall()
    except cx_Oracle.DatabaseError as e:
        module.fail_json(msg='{sql}: {err}'.format(sql=sql, err=str(e)))
    return rows


def get_datafiles(module, conn, ts):
    sql = 'SELECT file_id, file_name, bytes, maxbytes, increment_by FROM dba_data_files WHERE tablespace_name = :name'
    cur = conn.cursor()
    try:
        cur.prepare(sql)
        cur.execute(None, dict(name=ts))
        data = cur.fetchall()
    except cx_Oracle.DatabaseError as e:
        module.fail_json(msg='{sql}: {err}'.format(sql=sql, err=str(e)))

    cur.close()
    datafiles = list()
    for row in data:
        datafiles.append(
            dict(file_id=row[0], name=row[1], bytes=row[2], maxbytes=row[3], increment_by=row[4]))
    return datafiles


def get_tablespace(module, conn, name):
    sql = 'SELECT ts#, name, bigfile FROM v$tablespace WHERE name = :name'
    cur = conn.cursor()
    try:
        cur.prepare(sql)
        cur.execute(None, dict(name=name))
        row = cur.fetchone()
    except cx_Oracle.DatabaseError as e:
        module.fail_json(msg='{sql}: {err}'.format(sql=sql, err=str(e)))
    cur.close()

    if not row:
        return None
    ts = dict(ts_nr=row[0], name=row[1], bigfile=row[2])
    ts['datafiles'] = get_datafiles(module=module, conn=conn, ts=name)

    return ts


def get_create_tablespace_sql(name, blocksize, num_datafiles, init_size, autoextend, next_size, max_size):
    sql = 'CREATE TABLESPACE {name} DATAFILE'.format(name=name)
    for i in xrange(num_datafiles):
        if i > 0:
            sql = '{sql},'.format(sql=sql)
        sql = '{sql} SIZE {size}'.format(sql=sql, size=init_size)
        if autoextend:
            sql = '{sql} AUTOEXTEND ON NEXT {next_size} MAXSIZE {max_size}'.format(sql=sql, next_size=next_size,
                                                                                   max_size=max_size)
        else:
            sql = '{sql} AUTOEXTEND OFF'.format(sql=sql)

    if blocksize:
        sql = '{sql} BLOCKSIZE {blocksize}'.format(
            sql=sql, blocksize=blocksize)
    return sql


def get_drop_tablespace_sql(name):
    sql = 'DROP TABLESPACE {name} INCLUDING CONTENTS AND DATAFILES'.format(
        name=name)
    return sql


def get_alter_datafile_sql(file_id, autoextend, next_size, max_size):
    sql = 'ALTER DATABASE DATAFILE {file_id}'.format(file_id=file_id)
    if not autoextend:
        sql = '{sql} AUTOEXTEND OFF'.format(sql=sql)
    else:
        sql = '{sql} AUTOEXTEND ON NEXT {next_size} MAXSIZE {max_size}'.format(sql=sql, next_size=next_size,
                                                                               max_size=max_size)
    return sql


def get_resize_datafile_sql(file_id, size):
    return 'ALTER DATABASE DATAFILE {file_id} RESIZE {size}'.format(file_id=file_id, size=size)


def size_to_bytes(size, blocksize):
    # Return amount of bytes represented by size
    # Example: size_to_bytes("16M") = 16777216
    # Note: UNLIMITED is NOT 4194304 * blocksize, but 4194302 * blocksize
    if size.upper() == 'UNLIMITED':
        return ((4 * 1024 * 1024) - 2) * blocksize
    m = re.match("([0-9]+)\s*([kKmMgG])?", size)
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


def ensure(module, conn):
    name = module.params['name'].upper()
    blocksize = module.params['blocksize']
    num_datafiles = module.params['num_datafiles']
    init_size = module.params['init_size']
    autoextend = module.params['autoextend']
    next_size = module.params['next_size']
    max_size = module.params['max_size']
    state = module.params['state']
    sql = list()

    tbs = get_tablespace(module=module, conn=conn, name=name)

    if state == 'present':
        if not tbs:
            sql.append(get_create_tablespace_sql(name=name, blocksize=blocksize, num_datafiles=num_datafiles,
                                                 init_size=init_size, autoextend=autoextend, next_size=next_size,
                                                 max_size=max_size))
        else:
            for df in tbs.get('datafiles', None):
                block_size = size_to_bytes(blocksize, None)
                byte=size_to_bytes(init_size, block_size)
                maxbytes = size_to_bytes(max_size, block_size)
                increment_by = size_to_bytes(next_size, block_size) / block_size
                if df.get('maxbytes', None) != maxbytes or df.get('increment_by') != increment_by:
                    sql.append(get_alter_datafile_sql(file_id=df.get('file_id'), autoextend=autoextend, next_size=next_size,
                                                      max_size=max_size))
                if (not autoextend and df.get('bytes') > byte):
                    sql.append(get_resize_datafile_sql(
                        file_id=df.get('file_id'), size=maxbytes))
    elif state == 'absent':
        if tbs:
            sql.append(get_drop_tablespace_sql(name=name))

    if len(sql) > 0:
        if module.check_mode:
            module.exit_json(changed=True, tablespace=tbs, sql=sql)
        for stmt in sql:
            execute_sql(module=module, con=conn, sql=stmt)
        return True, get_tablespace(module=module, conn=conn, name=name), sql
    return False, tbs, sql


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            blocksize=dict(type='str', required=False, default='8k'),
            num_datafiles=dict(type='int', required=False, default=1),
            autoextend=dict(type='bool', required=False, default=False),
            init_size=dict(type='str', required=False, default='1M'),
            next_size=dict(type='str', required=False, default='0'),
            max_size=dict(type='str', required=False, default='0'),
            state=dict(type='str', default='present',
                       choices=['present', 'absent']),
            oracle_host=dict(type='str', default='127.0.0.1'),
            oracle_port=dict(type='str', default='1521'),
            oracle_user=dict(type='str', default='SYSTEM'),
            oracle_mode=dict(type='str', required=None, default=None, choices=[
                'SYSDBA', 'SYSOPER']),
            oracle_pass=dict(type='str', default=None, no_log=True),
            oracle_sid=dict(type='str', default=None),
            oracle_service=dict(type='str', default=None),
        ),
        required_one_of=[['oracle_sid', 'oracle_service']],
        mutually_exclusive=[['oracle_sid', 'oracle_service']],
        supports_check_mode=True,
    )

    if not oracleclient_found:
        module.fail_json(
            msg='cx_Oracle not found. Needs to be installed. See http://cx-oracle.sourceforge.net/')

    oracle_host = module.params['oracle_host']
    oracle_port = module.params['oracle_port']
    oracle_user = module.params['oracle_user']
    oracle_mode = module.params['oracle_mode']
    oracle_pass = module.params['oracle_pass'] or os.environ['ORACLE_PASS']
    oracle_sid = module.params['oracle_sid']
    oracle_service = module.params['oracle_service']

    conn = create_connection(module=module,
                             user=oracle_user, password=oracle_pass, mode=oracle_mode,
                             host=oracle_host, port=oracle_port,
                             sid=oracle_sid, service=oracle_service)

    try:
        changed, tablespace, sql = ensure(module, conn)
        module.exit_json(changed=changed, tablespace=tablespace, sql=sql)
    except Exception as e:
        module.fail_json(msg=e.message)


# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
