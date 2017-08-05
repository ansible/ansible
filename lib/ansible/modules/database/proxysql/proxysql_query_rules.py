#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: proxysql_query_rules
version_added: "2.3"
author: "Ben Mildren (@bmildren)"
short_description: Modifies query rules using the proxysql admin interface.
description:
   - The M(proxysql_query_rules) module modifies query rules using the
     proxysql admin interface.
options:
  rule_id:
    description:
      - The unique id of the rule. Rules are processed in rule_id order.
  active:
    description:
      - A rule with I(active) set to C(False) will be tracked in the database,
        but will be never loaded in the in-memory data structures.
  username:
    description:
      - Filtering criteria matching username.  If I(username) is non-NULL, a
        query will match only if the connection is made with the correct
        username.
  schemaname:
    description:
      - Filtering criteria matching schemaname. If I(schemaname) is non-NULL, a
        query will match only if the connection uses schemaname as its default
        schema.
  flagIN:
    description:
      - Used in combination with I(flagOUT) and I(apply) to create chains of
        rules.
  client_addr:
    description:
      - Match traffic from a specific source.
  proxy_addr:
    description:
      - Match incoming traffic on a specific local IP.
  proxy_port:
    description:
      - Match incoming traffic on a specific local port.
  digest:
    description:
      - Match queries with a specific digest, as returned by
        stats_mysql_query_digest.digest.
  match_digest:
    description:
      - Regular expression that matches the query digest. The dialect of
        regular expressions used is that of re2 - https://github.com/google/re2
  match_pattern:
    description:
      - Regular expression that matches the query text. The dialect of regular
        expressions used is that of re2 - https://github.com/google/re2
  negate_match_pattern:
    description:
      - If I(negate_match_pattern) is set to C(True), only queries not matching
        the query text will be considered as a match. This acts as a NOT
        operator in front of the regular expression matching against
        match_pattern.
  flagOUT:
    description:
      - Used in combination with I(flagIN) and apply to create chains of rules.
        When set, I(flagOUT) signifies the I(flagIN) to be used in the next
        chain of rules.
  replace_pattern:
    description:
      - This is the pattern with which to replace the matched pattern. Note
        that this is optional, and when omitted, the query processor will only
        cache, route, or set other parameters without rewriting.
  destination_hostgroup:
    description:
      - Route matched queries to this hostgroup. This happens unless there is a
        started transaction and the logged in user has
        I(transaction_persistent) set to C(True) (see M(proxysql_mysql_users)).
  cache_ttl:
    description:
      - The number of milliseconds for which to cache the result of the query.
        Note in ProxySQL 1.1 I(cache_ttl) was in seconds.
  timeout:
    description:
      - The maximum timeout in milliseconds with which the matched or rewritten
        query should be executed. If a query run for longer than the specific
        threshold, the query is automatically killed. If timeout is not
        specified, the global variable mysql-default_query_timeout applies.
  retries:
    description:
      - The maximum number of times a query needs to be re-executed in case of
        detected failure during the execution of the query. If retries is not
        specified, the global variable mysql-query_retries_on_failure applies.
  delay:
    description:
      - Number of milliseconds to delay the execution of the query. This is
        essentially a throttling mechanism and QoS, and allows a way to give
        priority to queries over others. This value is added to the
        mysql-default_query_delay global variable that applies to all queries.
  mirror_flagOUT:
    description:
      - Enables query mirroring. If set I(mirror_flagOUT) can be used to
        evaluates the mirrored query against the specified chain of rules.
  mirror_hostgroup:
    description:
      - Enables query mirroring. If set I(mirror_hostgroup) can be used to
        mirror queries to the same or different hostgroup.
  error_msg:
    description:
      - Query will be blocked, and the specified error_msg will be returned to
        the client.
  log:
    description:
      - Query will be logged.
  apply:
    description:
      - Used in combination with I(flagIN) and I(flagOUT) to create chains of
        rules. Setting apply to True signifies the last rule to be applied.
  comment:
    description:
      - Free form text field, usable for a descriptive comment of the query
        rule.
  state:
    description:
      - When C(present) - adds the rule, when C(absent) - removes the rule.
    choices: [ "present", "absent" ]
    default: present
  force_delete:
    description:
      - By default we avoid deleting more than one schedule in a single batch,
        however if you need this behaviour and you're not concerned about the
        schedules deleted, you can set I(force_delete) to C(True).
    default: False
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
# This example adds a rule to redirect queries from a specific user to another
# hostgroup, it saves the mysql query rule config to disk, but avoids loading
# the mysql query config config to runtime (this might be because several
# rules are being added and the user wants to push the config to runtime in a
# single batch using the M(proxysql_manage_config) module). It uses supplied
# credentials to connect to the proxysql admin interface.

- proxysql_backend_servers:
    login_user: admin
    login_password: admin
    username: 'guest_ro'
    destination_hostgroup: 1
    active: 1
    retries: 3
    state: present
    load_to_runtime: False

# This example removes all rules that use the username 'guest_ro', saves the
# mysql query rule config to disk, and dynamically loads the mysql query rule
# config to runtime.  It uses credentials in a supplied config file to connect
# to the proxysql admin interface.

- proxysql_backend_servers:
    config_file: '~/proxysql.cnf'
    username: 'guest_ro'
    state: absent
    force_delete: true
'''

RETURN = '''
stdout:
    description: The mysql user modified or removed from proxysql
    returned: On create/update will return the newly modified rule, in all
              other cases will return a list of rules that match the supplied
              criteria.
    type: dict
    "sample": {
        "changed": true,
        "msg": "Added rule to mysql_query_rules",
        "rules": [
            {
                "active": "0",
                "apply": "0",
                "cache_ttl": null,
                "client_addr": null,
                "comment": null,
                "delay": null,
                "destination_hostgroup": 1,
                "digest": null,
                "error_msg": null,
                "flagIN": "0",
                "flagOUT": null,
                "log": null,
                "match_digest": null,
                "match_pattern": null,
                "mirror_flagOUT": null,
                "mirror_hostgroup": null,
                "negate_match_pattern": "0",
                "proxy_addr": null,
                "proxy_port": null,
                "reconnect": null,
                "replace_pattern": null,
                "retries": null,
                "rule_id": "1",
                "schemaname": null,
                "timeout": null,
                "username": "guest_ro"
            }
        ],
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

    if not MYSQLDB_FOUND:
        module.fail_json(
            msg="the python mysqldb module is required"
        )


def save_config_to_disk(cursor):
    cursor.execute("SAVE MYSQL QUERY RULES TO DISK")
    return True


def load_config_to_runtime(cursor):
    cursor.execute("LOAD MYSQL QUERY RULES TO RUNTIME")
    return True


class ProxyQueryRule(object):

    def __init__(self, module):
        self.state = module.params["state"]
        self.force_delete = module.params["force_delete"]
        self.save_to_disk = module.params["save_to_disk"]
        self.load_to_runtime = module.params["load_to_runtime"]

        config_data_keys = ["rule_id",
                            "active",
                            "username",
                            "schemaname",
                            "flagIN",
                            "client_addr",
                            "proxy_addr",
                            "proxy_port",
                            "digest",
                            "match_digest",
                            "match_pattern",
                            "negate_match_pattern",
                            "flagOUT",
                            "replace_pattern",
                            "destination_hostgroup",
                            "cache_ttl",
                            "timeout",
                            "retries",
                            "delay",
                            "mirror_flagOUT",
                            "mirror_hostgroup",
                            "error_msg",
                            "log",
                            "apply",
                            "comment"]

        self.config_data = dict((k, module.params[k])
                                for k in config_data_keys)

    def check_rule_pk_exists(self, cursor):
        query_string = \
            """SELECT count(*) AS `rule_count`
               FROM mysql_query_rules
               WHERE rule_id = %s"""

        query_data = \
            [self.config_data["rule_id"]]

        cursor.execute(query_string, query_data)
        check_count = cursor.fetchone()
        return (int(check_count['rule_count']) > 0)

    def check_rule_cfg_exists(self, cursor):
        query_string = \
            """SELECT count(*) AS `rule_count`
               FROM mysql_query_rules"""

        cols = 0
        query_data = []

        for col, val in iteritems(self.config_data):
            if val is not None:
                cols += 1
                query_data.append(val)
                if cols == 1:
                    query_string += "\n WHERE " + col + " = %s"
                else:
                    query_string += "\n  AND " + col + " = %s"

        if cols > 0:
            cursor.execute(query_string, query_data)
        else:
            cursor.execute(query_string)
        check_count = cursor.fetchone()
        return int(check_count['rule_count'])

    def get_rule_config(self, cursor, created_rule_id=None):
        query_string = \
            """SELECT *
               FROM mysql_query_rules"""

        if created_rule_id:
            query_data = [created_rule_id, ]
            query_string += "\nWHERE rule_id = %s"

            cursor.execute(query_string, query_data)
            rule = cursor.fetchone()
        else:
            cols = 0
            query_data = []

            for col, val in iteritems(self.config_data):
                if val is not None:
                    cols += 1
                    query_data.append(val)
                    if cols == 1:
                        query_string += "\n WHERE " + col + " = %s"
                    else:
                        query_string += "\n  AND " + col + " = %s"

            if cols > 0:
                cursor.execute(query_string, query_data)
            else:
                cursor.execute(query_string)
            rule = cursor.fetchall()

        return rule

    def create_rule_config(self, cursor):
        query_string = \
            """INSERT INTO mysql_query_rules ("""

        cols = 0
        query_data = []

        for col, val in iteritems(self.config_data):
            if val is not None:
                cols += 1
                query_data.append(val)
                query_string += "\n" + col + ","

        query_string = query_string[:-1]

        query_string += \
            (")\n" +
             "VALUES (" +
             "%s ," * cols)

        query_string = query_string[:-2]
        query_string += ")"

        cursor.execute(query_string, query_data)
        new_rule_id = cursor.lastrowid
        return True, new_rule_id

    def update_rule_config(self, cursor):
        query_string = """UPDATE mysql_query_rules"""

        cols = 0
        query_data = []

        for col, val in iteritems(self.config_data):
            if val is not None and col != "rule_id":
                cols += 1
                query_data.append(val)
                if cols == 1:
                    query_string += "\nSET " + col + "= %s,"
                else:
                    query_string += "\n    " + col + " = %s,"

        query_string = query_string[:-1]
        query_string += "\nWHERE rule_id = %s"

        query_data.append(self.config_data["rule_id"])

        cursor.execute(query_string, query_data)
        return True

    def delete_rule_config(self, cursor):
        query_string = \
            """DELETE FROM mysql_query_rules"""

        cols = 0
        query_data = []

        for col, val in iteritems(self.config_data):
            if val is not None:
                cols += 1
                query_data.append(val)
                if cols == 1:
                    query_string += "\n WHERE " + col + " = %s"
                else:
                    query_string += "\n  AND " + col + " = %s"

        if cols > 0:
            cursor.execute(query_string, query_data)
        else:
            cursor.execute(query_string)
        check_count = cursor.rowcount
        return True, int(check_count)

    def manage_config(self, cursor, state):
        if state:
            if self.save_to_disk:
                save_config_to_disk(cursor)
            if self.load_to_runtime:
                load_config_to_runtime(cursor)

    def create_rule(self, check_mode, result, cursor):
        if not check_mode:
            result['changed'], new_rule_id = \
                self.create_rule_config(cursor)
            result['msg'] = "Added rule to mysql_query_rules"
            self.manage_config(cursor,
                               result['changed'])
            result['rules'] = \
                self.get_rule_config(cursor, new_rule_id)
        else:
            result['changed'] = True
            result['msg'] = ("Rule would have been added to" +
                             " mysql_query_rules, however" +
                             " check_mode is enabled.")

    def update_rule(self, check_mode, result, cursor):
        if not check_mode:
            result['changed'] = \
                self.update_rule_config(cursor)
            result['msg'] = "Updated rule in mysql_query_rules"
            self.manage_config(cursor,
                               result['changed'])
            result['rules'] = \
                self.get_rule_config(cursor)
        else:
            result['changed'] = True
            result['msg'] = ("Rule would have been updated in" +
                             " mysql_query_rules, however" +
                             " check_mode is enabled.")

    def delete_rule(self, check_mode, result, cursor):
        if not check_mode:
            result['rules'] = \
                self.get_rule_config(cursor)
            result['changed'], result['rows_affected'] = \
                self.delete_rule_config(cursor)
            result['msg'] = "Deleted rule from mysql_query_rules"
            self.manage_config(cursor,
                               result['changed'])
        else:
            result['changed'] = True
            result['msg'] = ("Rule would have been deleted from" +
                             " mysql_query_rules, however" +
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
            rule_id=dict(type='int'),
            active=dict(type='bool'),
            username=dict(type='str'),
            schemaname=dict(type='str'),
            flagIN=dict(type='int'),
            client_addr=dict(type='str'),
            proxy_addr=dict(type='str'),
            proxy_port=dict(type='int'),
            digest=dict(type='str'),
            match_digest=dict(type='str'),
            match_pattern=dict(type='str'),
            negate_match_pattern=dict(type='bool'),
            flagOUT=dict(type='int'),
            replace_pattern=dict(type='str'),
            destination_hostgroup=dict(type='int'),
            cache_ttl=dict(type='int'),
            timeout=dict(type='int'),
            retries=dict(type='int'),
            delay=dict(type='int'),
            mirror_flagOUT=dict(type='int'),
            mirror_hostgroup=dict(type='int'),
            error_msg=dict(type='str'),
            log=dict(type='bool'),
            apply=dict(type='bool'),
            comment=dict(type='str'),
            state=dict(default='present', choices=['present',
                                                   'absent']),
            force_delete=dict(default=False, type='bool'),
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

    proxysql_query_rule = ProxyQueryRule(module)
    result = {}

    result['state'] = proxysql_query_rule.state

    if proxysql_query_rule.state == "present":
        try:
            if not proxysql_query_rule.check_rule_cfg_exists(cursor):
                if proxysql_query_rule.config_data["rule_id"] and \
                   proxysql_query_rule.check_rule_pk_exists(cursor):
                    proxysql_query_rule.update_rule(module.check_mode,
                                                    result,
                                                    cursor)
                else:
                    proxysql_query_rule.create_rule(module.check_mode,
                                                    result,
                                                    cursor)
            else:
                result['changed'] = False
                result['msg'] = ("The rule already exists in" +
                                 " mysql_query_rules and doesn't need to be" +
                                 " updated.")
                result['rules'] = \
                    proxysql_query_rule.get_rule_config(cursor)

        except MySQLdb.Error as e:
            module.fail_json(
                msg="unable to modify rule.. %s" % to_native(e)
            )

    elif proxysql_query_rule.state == "absent":
        try:
            existing_rules = proxysql_query_rule.check_rule_cfg_exists(cursor)
            if existing_rules > 0:
                if existing_rules == 1 or \
                   proxysql_query_rule.force_delete:
                    proxysql_query_rule.delete_rule(module.check_mode,
                                                    result,
                                                    cursor)
                else:
                    module.fail_json(
                        msg=("Operation would delete multiple rules" +
                             " use force_delete to override this")
                    )
            else:
                result['changed'] = False
                result['msg'] = ("The rule is already absent from the" +
                                 " mysql_query_rules memory configuration")
        except MySQLdb.Error as e:
            module.fail_json(
                msg="unable to remove rule.. %s" % to_native(e)
            )

    module.exit_json(**result)

if __name__ == '__main__':
    main()
