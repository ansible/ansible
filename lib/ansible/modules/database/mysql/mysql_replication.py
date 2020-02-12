#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Balazs Pocze <banyek@gawker.com>
# Copyright: (c) 2019, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# Certain parts are taken from Mark Theunissen's mysqldb module
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: mysql_replication
short_description: Manage MySQL replication
description:
- Manages MySQL server replication, slave, master status, get and change master host.
version_added: '1.3'
author:
- Balazs Pocze (@banyek)
- Andrew Klychkov (@Andersson007)
options:
  mode:
    description:
    - Module operating mode. Could be
      C(changemaster) (CHANGE MASTER TO),
      C(getmaster) (SHOW MASTER STATUS),
      C(getslave) (SHOW SLAVE STATUS),
      C(startslave) (START SLAVE),
      C(stopslave) (STOP SLAVE),
      C(resetmaster) (RESET MASTER) - supported from Ansible 2.10,
      C(resetslave) (RESET SLAVE),
      C(resetslaveall) (RESET SLAVE ALL).
    type: str
    choices:
    - changemaster
    - getmaster
    - getslave
    - startslave
    - stopslave
    - resetmaster
    - resetslave
    - resetslaveall
    default: getslave
  master_host:
    description:
    - Same as mysql variable.
    type: str
  master_user:
    description:
    - Same as mysql variable.
    type: str
  master_password:
    description:
    - Same as mysql variable.
    type: str
  master_port:
    description:
    - Same as mysql variable.
    type: int
  master_connect_retry:
    description:
    - Same as mysql variable.
    type: int
  master_log_file:
    description:
    - Same as mysql variable.
    type: str
  master_log_pos:
    description:
    - Same as mysql variable.
    type: int
  relay_log_file:
    description:
    - Same as mysql variable.
    type: str
  relay_log_pos:
    description:
    - Same as mysql variable.
    type: int
  master_ssl:
    description:
    - Same as mysql variable.
    type: bool
  master_ssl_ca:
    description:
    - Same as mysql variable.
    type: str
  master_ssl_capath:
    description:
    - Same as mysql variable.
    type: str
  master_ssl_cert:
    description:
    - Same as mysql variable.
    type: str
  master_ssl_key:
    description:
    - Same as mysql variable.
    type: str
  master_ssl_cipher:
    description:
    - Same as mysql variable.
    type: str
  master_auto_position:
    description:
    - Whether the host uses GTID based replication or not.
    type: bool
    version_added: '2.0'
  master_use_gtid:
    description:
    - Configures the slave to use the MariaDB Global Transaction ID.
    - C(disabled) equals MASTER_USE_GTID=no command.
    - To find information about available values see
      U(https://mariadb.com/kb/en/library/change-master-to/#master_use_gtid).
    - Available since MariaDB 10.0.2.
    choices: [current_pos, slave_pos, disabled]
    type: str
    version_added: '2.10'
  master_delay:
    description:
    - Time lag behind the master's state (in seconds).
    - Available from MySQL 5.6.
    - For more information see U(https://dev.mysql.com/doc/refman/8.0/en/replication-delayed.html).
    type: int
    version_added: '2.10'
  connection_name:
    description:
    - Name of the master connection.
    - Supported from MariaDB 10.0.1.
    - Mutually exclusive with I(channel).
    - For more information see U(https://mariadb.com/kb/en/library/multi-source-replication/).
    type: str
    version_added: '2.10'
  channel:
    description:
    - Name of replication channel.
    - Multi-source replication is supported from MySQL 5.7.
    - Mutually exclusive with I(connection_name).
    - For more information see U(https://dev.mysql.com/doc/refman/8.0/en/replication-multi-source.html).
    type: str
    version_added: '2.10'
  fail_on_error:
    description:
    - Fails on error when calling mysql.
    type: bool
    default: False
    version_added: '2.10'

notes:
- If an empty value for the parameter of string type is needed, use an empty string.

extends_documentation_fragment:
- mysql

seealso:
- module: mysql_info
- name: MySQL replication reference
  description: Complete reference of the MySQL replication documentation.
  link: https://dev.mysql.com/doc/refman/8.0/en/replication.html
- name: MariaDB replication reference
  description: Complete reference of the MariaDB replication documentation.
  link: https://mariadb.com/kb/en/library/setting-up-replication/
'''

EXAMPLES = r'''
- name: Stop mysql slave thread
  mysql_replication:
    mode: stopslave

- name: Get master binlog file name and binlog position
  mysql_replication:
    mode: getmaster

- name: Change master to master server 192.0.2.1 and use binary log 'mysql-bin.000009' with position 4578
  mysql_replication:
    mode: changemaster
    master_host: 192.0.2.1
    master_log_file: mysql-bin.000009
    master_log_pos: 4578

- name: Check slave status using port 3308
  mysql_replication:
    mode: getslave
    login_host: ansible.example.com
    login_port: 3308

- name: On MariaDB change master to use GTID current_pos
  mysql_replication:
    mode: changemaster
    master_use_gtid: current_pos

- name: Change master to use replication delay 3600 seconds
  mysql_replication:
    mode: changemaster
    master_host: 192.0.2.1
    master_delay: 3600

- name: Start MariaDB standby with connection name master-1
  mysql_replication:
    mode: startslave
    connection_name: master-1

- name: Stop replication in channel master-1
  mysql_replication:
    mode: stopslave
    channel: master-1

- name: >
    Run RESET MASTER command which will delete all existing binary log files
    and reset the binary log index file on the master
  mysql_replication:
    mode: resetmaster

- name: Run start slave and fail the task on errors
  mysql_replication:
    mode: startslave
    connection_name: master-1
    fail_on_error: yes

- name: Change master and fail on error (like when slave thread is running)
  mysql_replication:
    mode: changemaster
    fail_on_error: yes

'''

RETURN = r'''
queries:
  description: List of executed queries which modified DB's state.
  returned: always
  type: list
  sample: ["CHANGE MASTER TO MASTER_HOST='master2.example.com',MASTER_PORT=3306"]
  version_added: '2.10'
'''

import os
import warnings

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.mysql import mysql_connect, mysql_driver, mysql_driver_fail_msg
from ansible.module_utils._text import to_native

executed_queries = []


def get_master_status(cursor):
    cursor.execute("SHOW MASTER STATUS")
    masterstatus = cursor.fetchone()
    return masterstatus


def get_slave_status(cursor, connection_name='', channel=''):
    if connection_name:
        query = "SHOW SLAVE '%s' STATUS" % connection_name
    else:
        query = "SHOW SLAVE STATUS"

    if channel:
        query += " FOR CHANNEL '%s'" % channel

    cursor.execute(query)
    slavestatus = cursor.fetchone()
    return slavestatus


def stop_slave(module, cursor, connection_name='', channel='', fail_on_error=False):
    if connection_name:
        query = "STOP SLAVE '%s'" % connection_name
    else:
        query = 'STOP SLAVE'

    if channel:
        query += " FOR CHANNEL '%s'" % channel

    try:
        executed_queries.append(query)
        cursor.execute(query)
        stopped = True
    except mysql_driver.Warning as e:
        stopped = False
    except Exception as e:
        if fail_on_error:
            module.fail_json(msg="STOP SLAVE failed: %s" % to_native(e))
        stopped = False
    return stopped


def reset_slave(module, cursor, connection_name='', channel='', fail_on_error=False):
    if connection_name:
        query = "RESET SLAVE '%s'" % connection_name
    else:
        query = 'RESET SLAVE'

    if channel:
        query += " FOR CHANNEL '%s'" % channel

    try:
        executed_queries.append(query)
        cursor.execute(query)
        reset = True
    except mysql_driver.Warning as e:
        reset = False
    except Exception as e:
        if fail_on_error:
            module.fail_json(msg="RESET SLAVE failed: %s" % to_native(e))
        reset = False
    return reset


def reset_slave_all(module, cursor, connection_name='', channel='', fail_on_error=False):
    if connection_name:
        query = "RESET SLAVE '%s' ALL" % connection_name
    else:
        query = 'RESET SLAVE ALL'

    if channel:
        query += " FOR CHANNEL '%s'" % channel

    try:
        executed_queries.append(query)
        cursor.execute(query)
        reset = True
    except mysql_driver.Warning as e:
        reset = False
    except Exception as e:
        if fail_on_error:
            module.fail_json(msg="RESET SLAVE ALL failed: %s" % to_native(e))
        reset = False
    return reset


def reset_master(module, cursor, fail_on_error=False):
    query = 'RESET MASTER'
    try:
        executed_queries.append(query)
        cursor.execute(query)
        reset = True
    except mysql_driver.Warning as e:
        reset = False
    except Exception as e:
        if fail_on_error:
            module.fail_json(msg="RESET MASTER failed: %s" % to_native(e))
        reset = False
    return reset


def start_slave(module, cursor, connection_name='', channel='', fail_on_error=False):
    if connection_name:
        query = "START SLAVE '%s'" % connection_name
    else:
        query = 'START SLAVE'

    if channel:
        query += " FOR CHANNEL '%s'" % channel

    try:
        executed_queries.append(query)
        cursor.execute(query)
        started = True
    except mysql_driver.Warning as e:
        started = False
    except Exception as e:
        if fail_on_error:
            module.fail_json(msg="START SLAVE failed: %s" % to_native(e))
        started = False
    return started


def changemaster(cursor, chm, connection_name='', channel=''):
    if connection_name:
        query = "CHANGE MASTER '%s' TO %s" % (connection_name, ','.join(chm))
    else:
        query = 'CHANGE MASTER TO %s' % ','.join(chm)

    if channel:
        query += " FOR CHANNEL '%s'" % channel

    executed_queries.append(query)
    cursor.execute(query)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(type='str'),
            login_password=dict(type='str', no_log=True),
            login_host=dict(type='str', default='localhost'),
            login_port=dict(type='int', default=3306),
            login_unix_socket=dict(type='str'),
            mode=dict(type='str', default='getslave', choices=[
                'getmaster', 'getslave', 'changemaster', 'stopslave',
                'startslave', 'resetmaster', 'resetslave', 'resetslaveall']),
            master_auto_position=dict(type='bool', default=False),
            master_host=dict(type='str'),
            master_user=dict(type='str'),
            master_password=dict(type='str', no_log=True),
            master_port=dict(type='int'),
            master_connect_retry=dict(type='int'),
            master_log_file=dict(type='str'),
            master_log_pos=dict(type='int'),
            relay_log_file=dict(type='str'),
            relay_log_pos=dict(type='int'),
            master_ssl=dict(type='bool', default=False),
            master_ssl_ca=dict(type='str'),
            master_ssl_capath=dict(type='str'),
            master_ssl_cert=dict(type='str'),
            master_ssl_key=dict(type='str'),
            master_ssl_cipher=dict(type='str'),
            connect_timeout=dict(type='int', default=30),
            config_file=dict(type='path', default='~/.my.cnf'),
            client_cert=dict(type='path', aliases=['ssl_cert']),
            client_key=dict(type='path', aliases=['ssl_key']),
            ca_cert=dict(type='path', aliases=['ssl_ca']),
            master_use_gtid=dict(type='str', choices=['current_pos', 'slave_pos', 'disabled']),
            master_delay=dict(type='int'),
            connection_name=dict(type='str'),
            channel=dict(type='str'),
            fail_on_error=dict(type='bool', default=False),
        ),
        mutually_exclusive=[
            ['connection_name', 'channel']
        ],
    )
    mode = module.params["mode"]
    master_host = module.params["master_host"]
    master_user = module.params["master_user"]
    master_password = module.params["master_password"]
    master_port = module.params["master_port"]
    master_connect_retry = module.params["master_connect_retry"]
    master_log_file = module.params["master_log_file"]
    master_log_pos = module.params["master_log_pos"]
    relay_log_file = module.params["relay_log_file"]
    relay_log_pos = module.params["relay_log_pos"]
    master_ssl = module.params["master_ssl"]
    master_ssl_ca = module.params["master_ssl_ca"]
    master_ssl_capath = module.params["master_ssl_capath"]
    master_ssl_cert = module.params["master_ssl_cert"]
    master_ssl_key = module.params["master_ssl_key"]
    master_ssl_cipher = module.params["master_ssl_cipher"]
    master_auto_position = module.params["master_auto_position"]
    ssl_cert = module.params["client_cert"]
    ssl_key = module.params["client_key"]
    ssl_ca = module.params["ca_cert"]
    connect_timeout = module.params['connect_timeout']
    config_file = module.params['config_file']
    master_delay = module.params['master_delay']
    if module.params.get("master_use_gtid") == 'disabled':
        master_use_gtid = 'no'
    else:
        master_use_gtid = module.params["master_use_gtid"]
    connection_name = module.params["connection_name"]
    channel = module.params['channel']
    fail_on_error = module.params['fail_on_error']

    if mysql_driver is None:
        module.fail_json(msg=mysql_driver_fail_msg)
    else:
        warnings.filterwarnings('error', category=mysql_driver.Warning)

    login_password = module.params["login_password"]
    login_user = module.params["login_user"]

    try:
        cursor, db_conn = mysql_connect(module, login_user, login_password, config_file,
                                        ssl_cert, ssl_key, ssl_ca, None, cursor_class='DictCursor',
                                        connect_timeout=connect_timeout)
    except Exception as e:
        if os.path.exists(config_file):
            module.fail_json(msg="unable to connect to database, check login_user and login_password are correct or %s has the credentials. "
                                 "Exception message: %s" % (config_file, to_native(e)))
        else:
            module.fail_json(msg="unable to find %s. Exception message: %s" % (config_file, to_native(e)))

    if mode in "getmaster":
        status = get_master_status(cursor)
        if not isinstance(status, dict):
            status = dict(Is_Master=False, msg="Server is not configured as mysql master")
        else:
            status['Is_Master'] = True
        module.exit_json(queries=executed_queries, **status)

    elif mode in "getslave":
        status = get_slave_status(cursor, connection_name, channel)
        if not isinstance(status, dict):
            status = dict(Is_Slave=False, msg="Server is not configured as mysql slave")
        else:
            status['Is_Slave'] = True
        module.exit_json(queries=executed_queries, **status)

    elif mode in "changemaster":
        chm = []
        result = {}
        if master_host is not None:
            chm.append("MASTER_HOST='%s'" % master_host)
        if master_user is not None:
            chm.append("MASTER_USER='%s'" % master_user)
        if master_password is not None:
            chm.append("MASTER_PASSWORD='%s'" % master_password)
        if master_port is not None:
            chm.append("MASTER_PORT=%s" % master_port)
        if master_connect_retry is not None:
            chm.append("MASTER_CONNECT_RETRY=%s" % master_connect_retry)
        if master_log_file is not None:
            chm.append("MASTER_LOG_FILE='%s'" % master_log_file)
        if master_log_pos is not None:
            chm.append("MASTER_LOG_POS=%s" % master_log_pos)
        if master_delay is not None:
            chm.append("MASTER_DELAY=%s" % master_delay)
        if relay_log_file is not None:
            chm.append("RELAY_LOG_FILE='%s'" % relay_log_file)
        if relay_log_pos is not None:
            chm.append("RELAY_LOG_POS=%s" % relay_log_pos)
        if master_ssl:
            chm.append("MASTER_SSL=1")
        if master_ssl_ca is not None:
            chm.append("MASTER_SSL_CA='%s'" % master_ssl_ca)
        if master_ssl_capath is not None:
            chm.append("MASTER_SSL_CAPATH='%s'" % master_ssl_capath)
        if master_ssl_cert is not None:
            chm.append("MASTER_SSL_CERT='%s'" % master_ssl_cert)
        if master_ssl_key is not None:
            chm.append("MASTER_SSL_KEY='%s'" % master_ssl_key)
        if master_ssl_cipher is not None:
            chm.append("MASTER_SSL_CIPHER='%s'" % master_ssl_cipher)
        if master_auto_position:
            chm.append("MASTER_AUTO_POSITION=1")
        if master_use_gtid is not None:
            chm.append("MASTER_USE_GTID=%s" % master_use_gtid)
        try:
            changemaster(cursor, chm, connection_name, channel)
        except mysql_driver.Warning as e:
            result['warning'] = to_native(e)
        except Exception as e:
            module.fail_json(msg='%s. Query == CHANGE MASTER TO %s' % (to_native(e), chm))
        result['changed'] = True
        module.exit_json(queries=executed_queries, **result)
    elif mode in "startslave":
        started = start_slave(module, cursor, connection_name, channel, fail_on_error)
        if started is True:
            module.exit_json(msg="Slave started ", changed=True, queries=executed_queries)
        else:
            module.exit_json(msg="Slave already started (Or cannot be started)", changed=False, queries=executed_queries)
    elif mode in "stopslave":
        stopped = stop_slave(module, cursor, connection_name, channel, fail_on_error)
        if stopped is True:
            module.exit_json(msg="Slave stopped", changed=True, queries=executed_queries)
        else:
            module.exit_json(msg="Slave already stopped", changed=False, queries=executed_queries)
    elif mode in "resetmaster":
        reset = reset_master(module, cursor, fail_on_error)
        if reset is True:
            module.exit_json(msg="Master reset", changed=True, queries=executed_queries)
        else:
            module.exit_json(msg="Master already reset", changed=False, queries=executed_queries)
    elif mode in "resetslave":
        reset = reset_slave(module, cursor, connection_name, channel, fail_on_error)
        if reset is True:
            module.exit_json(msg="Slave reset", changed=True, queries=executed_queries)
        else:
            module.exit_json(msg="Slave already reset", changed=False, queries=executed_queries)
    elif mode in "resetslaveall":
        reset = reset_slave_all(module, cursor, connection_name, channel, fail_on_error)
        if reset is True:
            module.exit_json(msg="Slave reset", changed=True, queries=executed_queries)
        else:
            module.exit_json(msg="Slave already reset", changed=False, queries=executed_queries)

    warnings.simplefilter("ignore")


if __name__ == '__main__':
    main()
