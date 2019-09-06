#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Balazs Pocze <banyek@gawker.com>
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
    - Manages MySQL server replication, slave, master status get and change master host.
version_added: "1.3"
author:
- Balazs Pocze (@banyek)
options:
    mode:
        description:
            - module operating mode. Could be getslave (SHOW SLAVE STATUS), getmaster (SHOW MASTER STATUS), changemaster (CHANGE MASTER TO), startslave
              (START SLAVE), stopslave (STOP SLAVE), resetslave (RESET SLAVE), resetslaveall (RESET SLAVE ALL)
        type: str
        choices:
            - getslave
            - getmaster
            - changemaster
            - stopslave
            - startslave
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
        version_added: "2.0"
extends_documentation_fragment:
- mysql
'''

EXAMPLES = r'''
# Stop mysql slave thread
- mysql_replication:
    mode: stopslave

# Get master binlog file name and binlog position
- mysql_replication:
    mode: getmaster

# Change master to master server 192.0.2.1 and use binary log 'mysql-bin.000009' with position 4578
- mysql_replication:
    mode: changemaster
    master_host: 192.0.2.1
    master_log_file: mysql-bin.000009
    master_log_pos: 4578

# Check slave status using port 3308
- mysql_replication:
    mode: getslave
    login_host: ansible.example.com
    login_port: 3308
'''

import os
import warnings

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.mysql import mysql_connect, mysql_driver, mysql_driver_fail_msg
from ansible.module_utils._text import to_native


def get_master_status(cursor):
    cursor.execute("SHOW MASTER STATUS")
    masterstatus = cursor.fetchone()
    return masterstatus


def get_slave_status(cursor):
    cursor.execute("SHOW SLAVE STATUS")
    slavestatus = cursor.fetchone()
    return slavestatus


def stop_slave(cursor):
    try:
        cursor.execute("STOP SLAVE")
        stopped = True
    except Exception:
        stopped = False
    return stopped


def reset_slave(cursor):
    try:
        cursor.execute("RESET SLAVE")
        reset = True
    except Exception:
        reset = False
    return reset


def reset_slave_all(cursor):
    try:
        cursor.execute("RESET SLAVE ALL")
        reset = True
    except Exception:
        reset = False
    return reset


def start_slave(cursor):
    try:
        cursor.execute("START SLAVE")
        started = True
    except Exception:
        started = False
    return started


def changemaster(cursor, chm, chm_params):
    sql_param = ",".join(chm)
    query = 'CHANGE MASTER TO %s' % sql_param
    cursor.execute(query, chm_params)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(type='str'),
            login_password=dict(type='str', no_log=True),
            login_host=dict(type='str', default='localhost'),
            login_port=dict(type='int', default=3306),
            login_unix_socket=dict(type='str'),
            mode=dict(type='str', default='getslave', choices=[
                'getmaster', 'getslave', 'changemaster', 'stopslave', 'startslave', 'resetslave', 'resetslaveall']),
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
        )
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

    if mysql_driver is None:
        module.fail_json(msg=mysql_driver_fail_msg)
    else:
        warnings.filterwarnings('error', category=mysql_driver.Warning)

    login_password = module.params["login_password"]
    login_user = module.params["login_user"]

    try:
        cursor = mysql_connect(module, login_user, login_password, config_file,
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
        module.exit_json(**status)

    elif mode in "getslave":
        status = get_slave_status(cursor)
        if not isinstance(status, dict):
            status = dict(Is_Slave=False, msg="Server is not configured as mysql slave")
        else:
            status['Is_Slave'] = True
        module.exit_json(**status)

    elif mode in "changemaster":
        chm = []
        chm_params = {}
        result = {}
        if master_host:
            chm.append("MASTER_HOST=%(master_host)s")
            chm_params['master_host'] = master_host
        if master_user:
            chm.append("MASTER_USER=%(master_user)s")
            chm_params['master_user'] = master_user
        if master_password:
            chm.append("MASTER_PASSWORD=%(master_password)s")
            chm_params['master_password'] = master_password
        if master_port is not None:
            chm.append("MASTER_PORT=%(master_port)s")
            chm_params['master_port'] = master_port
        if master_connect_retry is not None:
            chm.append("MASTER_CONNECT_RETRY=%(master_connect_retry)s")
            chm_params['master_connect_retry'] = master_connect_retry
        if master_log_file:
            chm.append("MASTER_LOG_FILE=%(master_log_file)s")
            chm_params['master_log_file'] = master_log_file
        if master_log_pos is not None:
            chm.append("MASTER_LOG_POS=%(master_log_pos)s")
            chm_params['master_log_pos'] = master_log_pos
        if relay_log_file:
            chm.append("RELAY_LOG_FILE=%(relay_log_file)s")
            chm_params['relay_log_file'] = relay_log_file
        if relay_log_pos is not None:
            chm.append("RELAY_LOG_POS=%(relay_log_pos)s")
            chm_params['relay_log_pos'] = relay_log_pos
        if master_ssl:
            chm.append("MASTER_SSL=1")
        if master_ssl_ca:
            chm.append("MASTER_SSL_CA=%(master_ssl_ca)s")
            chm_params['master_ssl_ca'] = master_ssl_ca
        if master_ssl_capath:
            chm.append("MASTER_SSL_CAPATH=%(master_ssl_capath)s")
            chm_params['master_ssl_capath'] = master_ssl_capath
        if master_ssl_cert:
            chm.append("MASTER_SSL_CERT=%(master_ssl_cert)s")
            chm_params['master_ssl_cert'] = master_ssl_cert
        if master_ssl_key:
            chm.append("MASTER_SSL_KEY=%(master_ssl_key)s")
            chm_params['master_ssl_key'] = master_ssl_key
        if master_ssl_cipher:
            chm.append("MASTER_SSL_CIPHER=%(master_ssl_cipher)s")
            chm_params['master_ssl_cipher'] = master_ssl_cipher
        if master_auto_position:
            chm.append("MASTER_AUTO_POSITION = 1")
        try:
            changemaster(cursor, chm, chm_params)
        except mysql_driver.Warning as e:
            result['warning'] = to_native(e)
        except Exception as e:
            module.fail_json(msg='%s. Query == CHANGE MASTER TO %s' % (to_native(e), chm))
        result['changed'] = True
        module.exit_json(**result)
    elif mode in "startslave":
        started = start_slave(cursor)
        if started is True:
            module.exit_json(msg="Slave started ", changed=True)
        else:
            module.exit_json(msg="Slave already started (Or cannot be started)", changed=False)
    elif mode in "stopslave":
        stopped = stop_slave(cursor)
        if stopped is True:
            module.exit_json(msg="Slave stopped", changed=True)
        else:
            module.exit_json(msg="Slave already stopped", changed=False)
    elif mode in "resetslave":
        reset = reset_slave(cursor)
        if reset is True:
            module.exit_json(msg="Slave reset", changed=True)
        else:
            module.exit_json(msg="Slave already reset", changed=False)
    elif mode in "resetslaveall":
        reset = reset_slave_all(cursor)
        if reset is True:
            module.exit_json(msg="Slave reset", changed=True)
        else:
            module.exit_json(msg="Slave already reset", changed=False)

    warnings.simplefilter("ignore")


if __name__ == '__main__':
    main()
