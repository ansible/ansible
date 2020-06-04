#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Nate Fleming <nate.fleming@moserit.com>
# Sponsored by Moser Consulting Inc http://www.moserit.com
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: snowflake_wh
short_description: Add or remove Snowflake warehouses
description:
   - Add or remove Snowflake warehouses
options:
  names:
    description:
      - A comma separated list of warehouses to create
    required: true
    aliases: ['wh','warehouse','warehouses','name']
    type: str
  connection:
    description:
      - Provide parameters to the snowflake connection
    required: false
    type: dict
  auto_suspend:
    description:
      - The time in minutes before the warehouse suspends
    required: false
    type: int
  auto_resume:
    description:
      - Auto suspend this warehouse
    required: false
    type: bool
  initially_suspended:
    description:
      - The warehouse should initially be suspended
    required: false
    type: bool
  min_cluster:
    description:
      - The minimum cluster size
    required: false
    type: int
  max_cluster:
    description:
      - The maximum cluster size
    required: false
    type: int
  scaling_policy:
    description:
      - The scaling policy
    required: false
    type: str
    choices: ['STANDARD','ECONOMY']
  size:
    description:
      - The size of the warehouse
    required: false
    aliases: ['warehouse_size','wh_size']
    type: str
    choices:
        - XSMALL
        - X-SMALL
        - SMALL
        - MEDIUM
        - LARGE
        - XLARGE
        - X-LARGE
        - XXLARGE
        - X2LARGE
        - 2X-LARGE
        - XXXLARGE
        - X3LARGE
        - 3X-LARGE
        - X4LARGE
        - 4X-LARGE
  comment:
    description:
      - A comment to include on the database
    required: false
    type: str
  state:
    description:
      - The database state
    default: present
    choices: ["present", "absent"]
    type: str
notes:
   - Requires the snowflake Python package on the host. For Ubuntu, this
     is as easy as pip install snowflake-connector-python (See M(pip).)
requirements:
   - python >= 2.7
   - snowflake
   - snowflake-connector-python
seealso:
    - name: Snowflake Connection Parameters
      description: Comprehensive list of available Snowflake connection parameters
      link: https://docs.snowflake.com/en/user-guide/python-connector-api.html
author: Nate Fleming (@natefleming)
version_added: 1.0
'''

EXAMPLES = r'''
- name: Create a few warehouses (FOO, BAR, BAZ) at once with the same configuration
  snowflake_wh:
    warehouses: FOO, BAR, BAZ
    state: present
    auto_suspend: TRUE
    min_cluster_count: 1
    max_cluster_count: 10

- name: Create a single warehouse using the ACCOUNTADMIN role
  snowflake_wh:
    connection:
      role: ACCOUNTADMIN
    warehouse: ZOO
    state: present

- name: Delete some warehouses at once
  snowflake_wh:
    names: FOO, BAR
    state: absent

- name: Delete a single warehouse using the ACCOUNTADMIN role
  snowflake_wh:
    connection:
      role: ACCOUNTADMIN
    name:  BAZ
    state: absent
'''

import os
import pipes
import subprocess
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.snowflake import snowflake_connect
from ansible.module_utils.snowflake import snowflake_found
from ansible.module_utils.snowflake import snowflake_missing_lib_exception
from ansible.module_utils.snowflake import snowflake_missing_lib_msg
from ansible.module_utils.snowflake import quoted_identifier


VALID_WH_SIZES = [
    'XSMALL',
    'X-SMALL',
    'SMALL',
    'MEDIUM',
    'LARGE',
    'XLARGE',
    'X-LARGE',
    'XXLARGE',
    'X2LARGE',
    '2X-LARGE',
    'XXXLARGE',
    'X3LARGE',
    '3X-LARGE',
    'X4LARGE',
    '4X-LARGE'
]

VALID_SCALING_POLICIES = [
    'STANDARD',
    'ECONOMY'
]


def quoted_identifier(target):
    return "'{0}'".format(target)


def wh_exists(cursor, wh):
    query = 'SHOW WAREHOUSES LIKE {0}'.format(quoted_identifier(wh))
    cursor.execute(query)
    exists = cursor.rowcount > 0
    return exists


def wh_delete(cursor, wh):
    changed = False
    sfqid = None
    query = None
    if wh_exists(cursor, wh):
        query = 'DROP WAREHOUSE {0}'.format(wh)
        cursor.execute(query)
        sfqid = cursor.sfqid
        changed = True
    return {'sql': query, 'warehouse': wh, 'changed': changed, 'sfqid': sfqid}


def wh_create(cursor, wh, wh_size, initially_suspended, auto_suspend, auto_resume, min_cluster_count, max_cluster_count, scaling_policy, comment):
    changed = False
    sfqid = None
    query = None
    with_options = wh_size or initially_suspended or auto_suspend or min_cluster_count or max_cluster_count or scaling_policy or comment
    if not wh_exists(cursor, wh):
        query = ['CREATE WAREHOUSE {0}'.format(wh)]
        query = query + ['WITH'] if with_options else query
        query = query + ["WAREHOUSE_SIZE='{0}'".format(wh_size)] if wh_size else query
        query = query + ["INITIALLY_SUSPENDED={0}".format(initially_suspended)] if initially_suspended else query
        query = query + ["AUTO_SUSPEND={0}".format(auto_suspend)] if auto_suspend else query
        query = query + ["AUTO_RESUME={0}".format(auto_resume)] if auto_resume else query
        query = query + ["MIN_CLUSTER_COUNT={0}".format(min_cluster_count)] if min_cluster_count else query
        query = query + ["MAX_CLUSTER_COUNT={0}".format(max_cluster_count)] if max_cluster_count else query
        query = query + ["SCALING_POLICY={0}".format(scaling_policy)] if scaling_policy else query
        query = query + ["COMMENT='{0}'".format(comment)] if comment else query
        query = ' '.join(query)
        cursor.execute(query)
        sfqid = cursor.sfqid
        changed = True
    return {'sql': query, 'warehouse': wh, 'changed': changed, 'sfqid': sfqid}


def create_connection(params):

    DEFAULT_CONNECTION = {
        "account": DEFAULT_ACCOUNT,
        "user": DEFAULT_USER,
        "password": DEFAULT_PWD,
        "role": DEFAULT_ROLE,
        "warehouse": DEFAULT_WAREHOUSE,
        "schema": DEFAULT_SCHEMA
    }

    options = DEFAULT_CONNECTION
    options.update(params)
    options = {key: value for (key, value) in options.items() if value}

    connection = snowflake.connector.connect(**options)

    return connection


def main():

    module = AnsibleModule(
        argument_spec=dict(
            connection=dict(default={}, type=dict),
            names=dict(required=True, aliases=['wh', 'warehouse', 'warehouses', 'name']),
            state=dict(default="present", choices=["absent", "present"]),
            size=dict(default=None, aliases=['warehouse_size', 'wh_size'], choices=VALID_WH_SIZES),
            auto_suspend=dict(default=None, type=int),
            auto_resume=dict(default=None, type=bool),
            min_cluster_count=dict(default=None, type=int),
            max_cluster_count=dict(default=None, type=int),
            scaling_policy=dict(default=None, choices=VALID_SCALING_POLICIES),
            initially_suspended=dict(default=None, type=bool),
            comment=dict(default='')
        ),
        supports_check_mode=True
    )

    if not snowflake_found:
        module.fail_json(msg=snowflake_missing_lib_msg, exception=snowflake_missing_lib_exception)

    names = [n.strip() for n in module.params['names'].split(',')]
    state = module.params['state']
    wh_size = module.params['size']
    initially_suspended = module.params['initially_suspended']
    auto_suspend = module.params['auto_suspend']
    auto_resume = module.params['auto_resume']
    min_cluster_count = module.params['min_cluster_count']
    max_cluster_count = module.params['max_cluster_count']
    scaling_policy = module.params['scaling_policy']
    comment = module.params['comment']

    try:
        connection = snowflake_connect(module.params['connection'])
        cursor = connection.cursor()
    except Exception as e:
        module.fail_json(msg="Unable to connect to database, check user and password are correct or has the credentials. Exception message: %s" % (e))

    changed = False
    results = []
    if state == "present":
        if module.check_mode:
            changed = any([not wh_exists(cursor, name) for name in names])
        else:
            try:
                results = [wh_create(
                    cursor,
                    name,
                    wh_size,
                    initially_suspended,
                    auto_suspend,
                    auto_resume,
                    min_cluster_count,
                    max_cluster_count,
                    scaling_policy,
                    comment
                ) for name in names]
            except Exception as e:
                module.fail_json(msg="Error creating warehouse: %s" % to_native(e), exception=traceback.format_exc())
    elif state == "absent":
        if module.check_mode:
            changed = any([wh_exists(cursor, name) for name in names])
        else:
            try:
                results = [wh_delete(cursor, name) for name in names]
            except Exception as e:
                module.fail_json(msg="Error deleting warehouse: %s" % to_native(e), exception=traceback.format_exc())

    changed = any([result['changed'] for result in results]) if results else changed
    module.exit_json(changed=changed, state=state, results=results)


if __name__ == '__main__':
    main()
