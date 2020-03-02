#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: proxysql_replication_hostgroups
version_added: "2.3"
author: "Ben Mildren (@bmildren)"
short_description: Manages replication hostgroups using the proxysql admin
                   interface.
description:
   - Each row in mysql_replication_hostgroups represent a pair of
     writer_hostgroup and reader_hostgroup. ProxySQL will monitor the value of
     read_only for all the servers in specified hostgroups, and based on the
     value of read_only will assign the server to the writer or reader
     hostgroups.
options:
  writer_hostgroup:
    description:
      - Id of the writer hostgroup.
    required: True
  reader_hostgroup:
    description:
      - Id of the reader hostgroup.
    required: True
  comment:
    description:
      - Text field that can be used for any purposes defined by the user.
  state:
    description:
      - When C(present) - adds the replication hostgroup, when C(absent) -
        removes the replication hostgroup.
    choices: [ "present", "absent" ]
    default: present
extends_documentation_fragment:
  - proxysql.managing_config
  - proxysql.connectivity
'''

EXAMPLES = '''
---
# This example adds a replication hostgroup, it saves the mysql server config
# to disk, but avoids loading the mysql server config to runtime (this might be
# because several replication hostgroup are being added and the user wants to
# push the config to runtime in a single batch using the
# M(proxysql_manage_config) module).  It uses supplied credentials to connect
# to the proxysql admin interface.

- proxysql_replication_hostgroups:
    login_user: 'admin'
    login_password: 'admin'
    writer_hostgroup: 1
    reader_hostgroup: 2
    state: present
    load_to_runtime: False

# This example removes a replication hostgroup, saves the mysql server config
# to disk, and dynamically loads the mysql server config to runtime.  It uses
# credentials in a supplied config file to connect to the proxysql admin
# interface.

- proxysql_replication_hostgroups:
    config_file: '~/proxysql.cnf'
    writer_hostgroup: 3
    reader_hostgroup: 4
    state: absent
'''

RETURN = '''
stdout:
    description: The replication hostgroup modified or removed from proxysql
    returned: On create/update will return the newly modified group, on delete
              it will return the deleted record.
    type: dict
    "sample": {
        "changed": true,
        "msg": "Added server to mysql_hosts",
        "repl_group": {
            "comment": "",
            "reader_hostgroup": "1",
            "writer_hostgroup": "2"
        },
        "state": "present"
    }
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.mysql import mysql_connect, mysql_driver, mysql_driver_fail_msg
from ansible.module_utils._text import to_native

# ===========================================
# proxysql module specific support methods.
#


def perform_checks(module):
    if module.params["login_port"] < 0 \
       or module.params["login_port"] > 65535:
        module.fail_json(
            msg="login_port must be a valid unix port number (0-65535)"
        )

    if not module.params["writer_hostgroup"] >= 0:
        module.fail_json(
            msg="writer_hostgroup must be a integer greater than or equal to 0"
        )

    if not module.params["reader_hostgroup"] == \
            module.params["writer_hostgroup"]:
        if not module.params["reader_hostgroup"] > 0:
            module.fail_json(
                msg=("writer_hostgroup must be a integer greater than" +
                     " or equal to 0")
            )
    else:
        module.fail_json(
            msg="reader_hostgroup cannot equal writer_hostgroup"
        )

    if mysql_driver is None:
        module.fail_json(msg=mysql_driver_fail_msg)


def save_config_to_disk(cursor):
    cursor.execute("SAVE MYSQL SERVERS TO DISK")
    return True


def load_config_to_runtime(cursor):
    cursor.execute("LOAD MYSQL SERVERS TO RUNTIME")
    return True


class ProxySQLReplicationHostgroup(object):

    def __init__(self, module):
        self.state = module.params["state"]
        self.save_to_disk = module.params["save_to_disk"]
        self.load_to_runtime = module.params["load_to_runtime"]
        self.writer_hostgroup = module.params["writer_hostgroup"]
        self.reader_hostgroup = module.params["reader_hostgroup"]
        self.comment = module.params["comment"]

    def check_repl_group_config(self, cursor, keys):
        query_string = \
            """SELECT count(*) AS `repl_groups`
               FROM mysql_replication_hostgroups
               WHERE writer_hostgroup = %s
                 AND reader_hostgroup = %s"""

        query_data = \
            [self.writer_hostgroup,
             self.reader_hostgroup]

        if self.comment and not keys:
            query_string += "\n  AND comment = %s"
            query_data.append(self.comment)

        cursor.execute(query_string, query_data)
        check_count = cursor.fetchone()
        return (int(check_count['repl_groups']) > 0)

    def get_repl_group_config(self, cursor):
        query_string = \
            """SELECT *
               FROM mysql_replication_hostgroups
               WHERE writer_hostgroup = %s
                 AND reader_hostgroup = %s"""

        query_data = \
            [self.writer_hostgroup,
             self.reader_hostgroup]

        cursor.execute(query_string, query_data)
        repl_group = cursor.fetchone()
        return repl_group

    def create_repl_group_config(self, cursor):
        query_string = \
            """INSERT INTO mysql_replication_hostgroups (
               writer_hostgroup,
               reader_hostgroup,
               comment)
               VALUES (%s, %s, %s)"""

        query_data = \
            [self.writer_hostgroup,
             self.reader_hostgroup,
             self.comment or '']

        cursor.execute(query_string, query_data)
        return True

    def update_repl_group_config(self, cursor):
        query_string = \
            """UPDATE mysql_replication_hostgroups
               SET comment = %s
               WHERE writer_hostgroup = %s
                 AND reader_hostgroup = %s"""

        query_data = \
            [self.comment,
             self.writer_hostgroup,
             self.reader_hostgroup]

        cursor.execute(query_string, query_data)
        return True

    def delete_repl_group_config(self, cursor):
        query_string = \
            """DELETE FROM mysql_replication_hostgroups
               WHERE writer_hostgroup = %s
                 AND reader_hostgroup = %s"""

        query_data = \
            [self.writer_hostgroup,
             self.reader_hostgroup]

        cursor.execute(query_string, query_data)
        return True

    def manage_config(self, cursor, state):
        if state:
            if self.save_to_disk:
                save_config_to_disk(cursor)
            if self.load_to_runtime:
                load_config_to_runtime(cursor)

    def create_repl_group(self, check_mode, result, cursor):
        if not check_mode:
            result['changed'] = \
                self.create_repl_group_config(cursor)
            result['msg'] = "Added server to mysql_hosts"
            result['repl_group'] = \
                self.get_repl_group_config(cursor)
            self.manage_config(cursor,
                               result['changed'])
        else:
            result['changed'] = True
            result['msg'] = ("Repl group would have been added to" +
                             " mysql_replication_hostgroups, however" +
                             " check_mode is enabled.")

    def update_repl_group(self, check_mode, result, cursor):
        if not check_mode:
            result['changed'] = \
                self.update_repl_group_config(cursor)
            result['msg'] = "Updated server in mysql_hosts"
            result['repl_group'] = \
                self.get_repl_group_config(cursor)
            self.manage_config(cursor,
                               result['changed'])
        else:
            result['changed'] = True
            result['msg'] = ("Repl group would have been updated in" +
                             " mysql_replication_hostgroups, however" +
                             " check_mode is enabled.")

    def delete_repl_group(self, check_mode, result, cursor):
        if not check_mode:
            result['repl_group'] = \
                self.get_repl_group_config(cursor)
            result['changed'] = \
                self.delete_repl_group_config(cursor)
            result['msg'] = "Deleted server from mysql_hosts"
            self.manage_config(cursor,
                               result['changed'])
        else:
            result['changed'] = True
            result['msg'] = ("Repl group would have been deleted from" +
                             " mysql_replication_hostgroups, however" +
                             " check_mode is enabled.")

# ===========================================
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default=None, type='str'),
            login_password=dict(default=None, no_log=True, type='str'),
            login_host=dict(default="127.0.0.1"),
            login_unix_socket=dict(default=None),
            login_port=dict(default=6032, type='int'),
            config_file=dict(default="", type='path'),
            writer_hostgroup=dict(required=True, type='int'),
            reader_hostgroup=dict(required=True, type='int'),
            comment=dict(type='str'),
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
                               cursor_class='DictCursor')
    except mysql_driver.Error as e:
        module.fail_json(
            msg="unable to connect to ProxySQL Admin Module.. %s" % to_native(e)
        )

    proxysql_repl_group = ProxySQLReplicationHostgroup(module)
    result = {}

    result['state'] = proxysql_repl_group.state

    if proxysql_repl_group.state == "present":
        try:
            if not proxysql_repl_group.check_repl_group_config(cursor,
                                                               keys=True):
                proxysql_repl_group.create_repl_group(module.check_mode,
                                                      result,
                                                      cursor)
            else:
                if not proxysql_repl_group.check_repl_group_config(cursor,
                                                                   keys=False):
                    proxysql_repl_group.update_repl_group(module.check_mode,
                                                          result,
                                                          cursor)
                else:
                    result['changed'] = False
                    result['msg'] = ("The repl group already exists in" +
                                     " mysql_replication_hostgroups and" +
                                     " doesn't need to be updated.")
                    result['repl_group'] = \
                        proxysql_repl_group.get_repl_group_config(cursor)

        except mysql_driver.Error as e:
            module.fail_json(
                msg="unable to modify replication hostgroup.. %s" % to_native(e)
            )

    elif proxysql_repl_group.state == "absent":
        try:
            if proxysql_repl_group.check_repl_group_config(cursor,
                                                           keys=True):
                proxysql_repl_group.delete_repl_group(module.check_mode,
                                                      result,
                                                      cursor)
            else:
                result['changed'] = False
                result['msg'] = ("The repl group is already absent from the" +
                                 " mysql_replication_hostgroups memory" +
                                 " configuration")

        except mysql_driver.Error as e:
            module.fail_json(
                msg="unable to delete replication hostgroup.. %s" % to_native(e)
            )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
