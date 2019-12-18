#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = r'''
---
module: mysql_query
short_description: Run MySQL queries
description:
- Runs arbitrary MySQL queries.
- Pay attention, the module does not support check mode!
  All queries will be executed in autocommit mode.
- Can run queries from SQL script files.
version_added: '2.10'
options:
  query:
    description:
    - SQL query to run.
    - Mutually exclusive with I(path_to_script).
    type: str
  positional_args:
    description:
    - List of values to be passed as positional arguments to the query.
    - Mutually exclusive with I(named_args).
    type: list
  named_args:
    description:
    - Dictionary of key-value arguments to pass to the query.
    - Mutually exclusive with I(positional_args).
    type: dict
  path_to_script:
    description:
    - Path to SQL script on the remote host.
    - Returns result of the last query in the script.
    - Mutually exclusive with I(query).
    type: path
  login_db:
    description:
    - Name of database to connect to and run queries against.
    type: str
author:
- Andrew Klychkov (@Andersson007)
extends_documentation_fragment: mysql
'''

EXAMPLES = r'''
- name: Simple select query to acme db
  mysql_query:
    login_db: acme
    query: SELECT * FROM orders

- name: Select query to db acme with positional arguments
  mysql_query:
    login_db: acme
    query: SELECT * FROM acme WHERE id = %s AND story = %s
    positional_args:
    - 1
    - test

- name: Select query to test_db with named_args
  mysql_query:
    login_db: test_db
    query: SELECT * FROM test WHERE id = %(id_val)s AND story = %(story_val)s
    named_args:
      id_val: 1
      story_val: test

- name: Insert query to test_table in db test_db
  mysql_query:
    login_db: test_db
    query: INSERT INTO test_table (id, story) VALUES (2, 'my_long_story')

- name: Run queries from SQL script
  mysql_query:
    login_db: test_db
    path_to_script: /tmp/test.sql
'''

RETURN = r'''
query:
    description: Executed query.
    returned: always
    type: str
    sample: 'SELECT * FROM bar'
query_result:
    description:
    - List of dictionaries in column:value form representing returned rows.
    returned: changed
    type: list
    sample: [{"Column": "Value1"},{"Column": "Value2"}]
rowcount:
    description: Number of affected rows.
    returned: changed
    type: int
    sample: 5
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.mysql import (
    mysql_connect,
    mysql_common_argument_spec,
    mysql_driver,
    mysql_driver_fail_msg,
)
from ansible.module_utils._text import to_native

DML_QUERY_KEYWORDS = ('INSERT', 'UPDATE', 'DELETE')
DDL_QUERY_KEYWORDS = ('CREATE', 'DROP', 'ALTER')


# ===========================================
# Module execution.
#

def main():
    argument_spec = mysql_common_argument_spec()
    argument_spec.update(
        query=dict(type='str'),
        login_db=dict(type='str'),
        positional_args=dict(type='list'),
        named_args=dict(type='dict'),
        path_to_script=dict(type='path'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=(
            ('positional_args', 'named_args'),
            ('query', 'path_to_script'),
        ),
    )

    db = module.params['login_db']
    connect_timeout = module.params['connect_timeout']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    ssl_cert = module.params['client_cert']
    ssl_key = module.params['client_key']
    ssl_ca = module.params['ca_cert']
    config_file = module.params['config_file']
    query = module.params["query"]
    positional_args = module.params["positional_args"]
    named_args = module.params["named_args"]
    path_to_script = module.params["path_to_script"]

    if positional_args and named_args:
        module.fail_json(msg="positional_args and named_args params are mutually exclusive")

    if path_to_script and query:
        module.fail_json(msg="path_to_script is mutually exclusive with query")

    if path_to_script:
        try:
            query = open(path_to_script, 'r').read()
        except Exception as e:
            module.fail_json(msg="Cannot read file '%s' : %s" % (path_to_script, to_native(e)))

    if mysql_driver is None:
        module.fail_json(msg=mysql_driver_fail_msg)

    # Connect to DB:
    try:
        cursor = mysql_connect(module, login_user, login_password,
                               config_file, ssl_cert, ssl_key, ssl_ca, db,
                               connect_timeout=connect_timeout,
                               cursor_class='DictCursor', autocommit=True)
    except Exception as e:
        module.fail_json(msg="unable to connect to database, check login_user and "
                             "login_password are correct or %s has the credentials. "
                             "Exception message: %s" % (config_file, to_native(e)))
    # Prepare args:
    if module.params.get("positional_args"):
        arguments = module.params["positional_args"]
    elif module.params.get("named_args"):
        arguments = module.params["named_args"]
    else:
        arguments = None

    # Set defaults:
    changed = False

    # Execute query:
    try:
        cursor.execute(query, arguments)
    except Exception as e:
        cursor.close()
        module.fail_json(msg="Cannot execute SQL '%s' args [%s]: %s" % (query, arguments, to_native(e)))

    try:
        query_result = [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        module.fail_json(msg="Cannot fetch rows from cursor: %s" % to_native(e))

    # Check DML or DDL keywords in query and set changed accordingly:
    for keyword in DML_QUERY_KEYWORDS:
        if keyword in query.upper() and cursor.rowcount > 0:
            changed = True

    for keyword in DDL_QUERY_KEYWORDS:
        if keyword in query.upper():
            changed = True

    # Create dict with returned values:
    kw = {
        'changed': changed,
        'query': cursor._last_executed,
        'query_result': query_result,
        'rowcount': cursor.rowcount,
    }

    # Exit:
    module.exit_json(**kw)


if __name__ == '__main__':
    main()
