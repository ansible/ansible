#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: proxysql_backend_servers
version_added: "2.3"
author: "Ben Mildren (@bmildren)"
short_description: Adds or removes mysql hosts from proxysql admin interface.
description:
   - The M(proxysql_backend_servers) module adds or removes mysql hosts using
     the proxysql admin interface.
options:
  hostgroup_id:
    description:
      - The hostgroup in which this mysqld instance is included. An instance
        can be part of one or more hostgroups.
    default: 0
  hostname:
    description:
      - The ip address at which the mysqld instance can be contacted.
    required: True
  port:
    description:
      - The port at which the mysqld instance can be contacted.
    default: 3306
  status:
    description:
      - ONLINE - Backend server is fully operational.
        OFFLINE_SOFT - When a server is put into C(OFFLINE_SOFT) mode,
                       connections are kept in use until the current
                       transaction is completed. This allows to gracefully
                       detach a backend.
        OFFLINE_HARD - When a server is put into C(OFFLINE_HARD) mode, the
                       existing connections are dropped, while new incoming
                       connections aren't accepted either.

        If omitted the proxysql database default for I(status) is C(ONLINE).
    choices: [ "ONLINE", "OFFLINE_SOFT", "OFFLINE_HARD"]
  weight:
    description:
      - The bigger the weight of a server relative to other weights, the higher
        the probability of the server being chosen from the hostgroup. If
        omitted the proxysql database default for I(weight) is 1.
  compression:
    description:
      - If the value of I(compression) is greater than 0, new connections to
        that server will use compression. If omitted the proxysql database
        default for I(compression) is 0.
  max_connections:
    description:
      - The maximum number of connections ProxySQL will open to this backend
        server. If omitted the proxysql database default for I(max_connections)
        is 1000.
  max_replication_lag:
    description:
      - If greater than 0, ProxySQL will reguarly monitor replication lag. If
        replication lag goes above I(max_replication_lag), proxysql will
        temporarily shun the server until replication catches up. If omitted
        the proxysql database default for I(max_replication_lag) is 0.
  use_ssl:
    description:
      - If I(use_ssl) is set to C(True), connections to this server will be
        made using SSL connections. If omitted the proxysql database default
        for I(use_ssl) is C(False).
  max_latency_ms:
    description:
      - Ping time is monitored regularly. If a host has a ping time greater
        than I(max_latency_ms) it is excluded from the connection pool
        (although the server stays ONLINE). If omitted the proxysql database
        default for I(max_latency_ms) is 0.
  comment:
    description:
      - Text field that can be used for any purposed defined by the user.
        Could be a description of what the host stores, a reminder of when the
        host was added or disabled, or a JSON processed by some checker script.
    default: ''
  state:
    description:
      - When C(present) - adds the host, when C(absent) - removes the host.
    choices: [ "present", "absent" ]
    default: present
  save_to_disk:
    description:
      - Save mysql host config to sqlite db on disk to persist the
        configuration.
    default: True
  load_to_runtime:
    description:
      - Dynamically load mysql host config to runtime memory.
    default: True
  login_user:
    description:
      - The username used to authenticate to ProxySQL admin interface.
    default: None
  login_password:
    description:
      - The password used to authenticate to ProxySQL admin interface.
    default: None
  login_host:
    description:
      - The host used to connect to ProxySQL admin interface.
    default: '127.0.0.1'
  login_port:
    description:
      - The port used to connect to ProxySQL admin interface.
    default: 6032
  config_file:
    description:
      - Specify a config file from which login_user and login_password are to
        be read.
    default: ''
'''

EXAMPLES = '''
---
# This example adds a server, it saves the mysql server config to disk, but
# avoids loading the mysql server config to runtime (this might be because
# several servers are being added and the user wants to push the config to
# runtime in a single batch using the M(proxysql_manage_config) module).  It
# uses supplied credentials to connect to the proxysql admin interface.

- proxysql_backend_servers:
    login_user: 'admin'
    login_password: 'admin'
    hostname: 'mysql01'
    state: present
    load_to_runtime: False

# This example removes a server, saves the mysql server config to disk, and
# dynamically loads the mysql server config to runtime.  It uses credentials
# in a supplied config file to connect to the proxysql admin interface.

- proxysql_backend_servers:
    config_file: '~/proxysql.cnf'
    hostname: 'mysql02'
    state: absent
'''

RETURN = '''
stdout:
    description: The mysql host modified or removed from proxysql
    returned: On create/update will return the newly modified host, on delete
              it will return the deleted record.
    type: dict
    "sample": {
        "changed": true,
        "hostname": "192.168.52.1",
        "msg": "Added server to mysql_hosts",
        "server": {
            "comment": "",
            "compression": "0",
            "hostgroup_id": "1",
            "hostname": "192.168.52.1",
            "max_connections": "1000",
            "max_latency_ms": "0",
            "max_replication_lag": "0",
            "port": "3306",
            "status": "ONLINE",
            "use_ssl": "0",
            "weight": "1"
        },
        "state": "present"
    }
'''

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.mysql import mysql_connect
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native

try:
    import MySQLdb
    import MySQLdb.cursors
except ImportError:
    MYSQLDB_FOUND = False
else:
    MYSQLDB_FOUND = True

# ===========================================
# proxysql module specific support methods.
#


def perform_checks(module):
    if module.params["login_port"] < 0 \
       or module.params["login_port"] > 65535:
        module.fail_json(
            msg="login_port must be a valid unix port number (0-65535)"
        )

    if module.params["port"] < 0 \
       or module.params["port"] > 65535:
        module.fail_json(
            msg="port must be a valid unix port number (0-65535)"
        )

    if module.params["compression"]:
        if module.params["compression"] < 0 \
           or module.params["compression"] > 102400:
            module.fail_json(
                msg="compression must be set between 0 and 102400"
            )

    if module.params["max_replication_lag"]:
        if module.params["max_replication_lag"] < 0 \
           or module.params["max_replication_lag"] > 126144000:
            module.fail_json(
                msg="max_replication_lag must be set between 0 and 102400"
            )

    if not MYSQLDB_FOUND:
        module.fail_json(
            msg="the python mysqldb module is required"
        )


def save_config_to_disk(cursor):
    cursor.execute("SAVE MYSQL SERVERS TO DISK")
    return True


def load_config_to_runtime(cursor):
    cursor.execute("LOAD MYSQL SERVERS TO RUNTIME")
    return True


class ProxySQLServer(object):

    def __init__(self, module):
        self.state = module.params["state"]
        self.save_to_disk = module.params["save_to_disk"]
        self.load_to_runtime = module.params["load_to_runtime"]

        self.hostgroup_id = module.params["hostgroup_id"]
        self.hostname = module.params["hostname"]
        self.port = module.params["port"]

        config_data_keys = ["status",
                            "weight",
                            "compression",
                            "max_connections",
                            "max_replication_lag",
                            "use_ssl",
                            "max_latency_ms",
                            "comment"]

        self.config_data = dict((k, module.params[k])
                                for k in config_data_keys)

    def check_server_config_exists(self, cursor):
        query_string = \
            """SELECT count(*) AS `host_count`
               FROM mysql_servers
               WHERE hostgroup_id = %s
                 AND hostname = %s
                 AND port = %s"""

        query_data = \
            [self.hostgroup_id,
             self.hostname,
             self.port]

        cursor.execute(query_string, query_data)
        check_count = cursor.fetchone()
        return (int(check_count['host_count']) > 0)

    def check_server_config(self, cursor):
        query_string = \
            """SELECT count(*) AS `host_count`
               FROM mysql_servers
               WHERE hostgroup_id = %s
                 AND hostname = %s
                 AND port = %s"""

        query_data = \
            [self.hostgroup_id,
             self.hostname,
             self.port]

        for col, val in iteritems(self.config_data):
            if val is not None:
                query_data.append(val)
                query_string += "\n  AND " + col + " = %s"

        cursor.execute(query_string, query_data)
        check_count = cursor.fetchone()
        return (int(check_count['host_count']) > 0)

    def get_server_config(self, cursor):
        query_string = \
            """SELECT *
               FROM mysql_servers
               WHERE hostgroup_id = %s
                 AND hostname = %s
                 AND port = %s"""

        query_data = \
            [self.hostgroup_id,
             self.hostname,
             self.port]

        cursor.execute(query_string, query_data)
        server = cursor.fetchone()
        return server

    def create_server_config(self, cursor):
        query_string = \
            """INSERT INTO mysql_servers (
               hostgroup_id,
               hostname,
               port"""

        cols = 3
        query_data = \
            [self.hostgroup_id,
             self.hostname,
             self.port]

        for col, val in iteritems(self.config_data):
            if val is not None:
                cols += 1
                query_data.append(val)
                query_string += ",\n" + col

        query_string += \
            (")\n" +
             "VALUES (" +
             "%s ," * cols)

        query_string = query_string[:-2]
        query_string += ")"

        cursor.execute(query_string, query_data)
        return True

    def update_server_config(self, cursor):
        query_string = """UPDATE mysql_servers"""

        cols = 0
        query_data = []

        for col, val in iteritems(self.config_data):
            if val is not None:
                cols += 1
                query_data.append(val)
                if cols == 1:
                    query_string += "\nSET " + col + "= %s,"
                else:
                    query_string += "\n    " + col + " = %s,"

        query_string = query_string[:-1]
        query_string += ("\nWHERE hostgroup_id = %s\n  AND hostname = %s" +
                         "\n  AND port = %s")

        query_data.append(self.hostgroup_id)
        query_data.append(self.hostname)
        query_data.append(self.port)

        cursor.execute(query_string, query_data)
        return True

    def delete_server_config(self, cursor):
        query_string = \
            """DELETE FROM mysql_servers
               WHERE hostgroup_id = %s
                 AND hostname = %s
                 AND port = %s"""

        query_data = \
            [self.hostgroup_id,
             self.hostname,
             self.port]

        cursor.execute(query_string, query_data)
        return True

    def manage_config(self, cursor, state):
        if state:
            if self.save_to_disk:
                save_config_to_disk(cursor)
            if self.load_to_runtime:
                load_config_to_runtime(cursor)

    def create_server(self, check_mode, result, cursor):
        if not check_mode:
            result['changed'] = \
                self.create_server_config(cursor)
            result['msg'] = "Added server to mysql_hosts"
            result['server'] = \
                self.get_server_config(cursor)
            self.manage_config(cursor,
                               result['changed'])
        else:
            result['changed'] = True
            result['msg'] = ("Server would have been added to" +
                             " mysql_hosts, however check_mode" +
                             " is enabled.")

    def update_server(self, check_mode, result, cursor):
        if not check_mode:
            result['changed'] = \
                self.update_server_config(cursor)
            result['msg'] = "Updated server in mysql_hosts"
            result['server'] = \
                self.get_server_config(cursor)
            self.manage_config(cursor,
                               result['changed'])
        else:
            result['changed'] = True
            result['msg'] = ("Server would have been updated in" +
                             " mysql_hosts, however check_mode" +
                             " is enabled.")

    def delete_server(self, check_mode, result, cursor):
        if not check_mode:
            result['server'] = \
                self.get_server_config(cursor)
            result['changed'] = \
                self.delete_server_config(cursor)
            result['msg'] = "Deleted server from mysql_hosts"
            self.manage_config(cursor,
                               result['changed'])
        else:
            result['changed'] = True
            result['msg'] = ("Server would have been deleted from" +
                             " mysql_hosts, however check_mode is" +
                             " enabled.")

# ===========================================
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default=None, type='str'),
            login_password=dict(default=None, no_log=True, type='str'),
            login_host=dict(default='127.0.0.1'),
            login_unix_socket=dict(default=None),
            login_port=dict(default=6032, type='int'),
            config_file=dict(default='', type='path'),
            hostgroup_id=dict(default=0, type='int'),
            hostname=dict(required=True, type='str'),
            port=dict(default=3306, type='int'),
            status=dict(choices=['ONLINE',
                                 'OFFLINE_SOFT',
                                 'OFFLINE_HARD']),
            weight=dict(type='int'),
            compression=dict(type='int'),
            max_connections=dict(type='int'),
            max_replication_lag=dict(type='int'),
            use_ssl=dict(type='bool'),
            max_latency_ms=dict(type='int'),
            comment=dict(default='', type='str'),
            state=dict(default='present', choices=['present',
                                                   'absent']),
            save_to_disk=dict(default=True, type='bool'),
            load_to_runtime=dict(default=True, type='bool')
        ),
        supports_check_mode=True
    )

    perform_checks(module)

    login_user = module.params["login_user"]
    login_password = module.params["login_password"]
    config_file = module.params["config_file"]

    cursor = None
    try:
        cursor = mysql_connect(module,
                               login_user,
                               login_password,
                               config_file,
                               cursor_class=MySQLdb.cursors.DictCursor)
    except MySQLdb.Error as e:
        module.fail_json(
            msg="unable to connect to ProxySQL Admin Module.. %s" % to_native(e)
        )

    proxysql_server = ProxySQLServer(module)
    result = {}

    result['state'] = proxysql_server.state
    if proxysql_server.hostname:
        result['hostname'] = proxysql_server.hostname

    if proxysql_server.state == "present":
        try:
            if not proxysql_server.check_server_config(cursor):
                if not proxysql_server.check_server_config_exists(cursor):
                    proxysql_server.create_server(module.check_mode,
                                                  result,
                                                  cursor)
                else:
                    proxysql_server.update_server(module.check_mode,
                                                  result,
                                                  cursor)
            else:
                result['changed'] = False
                result['msg'] = ("The server already exists in mysql_hosts" +
                                 " and doesn't need to be updated.")
                result['server'] = \
                    proxysql_server.get_server_config(cursor)
        except MySQLdb.Error as e:
            module.fail_json(
                msg="unable to modify server.. %s" % to_native(e)
            )

    elif proxysql_server.state == "absent":
        try:
            if proxysql_server.check_server_config_exists(cursor):
                proxysql_server.delete_server(module.check_mode,
                                              result,
                                              cursor)
            else:
                result['changed'] = False
                result['msg'] = ("The server is already absent from the" +
                                 " mysql_hosts memory configuration")
        except MySQLdb.Error as e:
            module.fail_json(
                msg="unable to remove server.. %s" % to_native(e)
            )

    module.exit_json(**result)

if __name__ == '__main__':
    main()
