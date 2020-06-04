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
module: snowflake_role
short_description: Add or remove Snowflake databases from a remote host.
description:
   - Add or remove Snowflake databases from a remote host.
options:
  name:
    description:
      - A comma separated list of roles to add or remove
    required: true
    aliases: ['role', 'roles', 'names']
    type: str
  comment:
    description:
      - A comment to include with this role
    required: false
    type: str
  inherited_roles:
    description:
      - A comma separated list of existing roles which will be granted to new roles
    required: false
    aliases: ['inherited_role']
    type: str
  connection:
    description:
      - Provide parameters to the snowflake connection
    required: false
    type: dict
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
version_added: '1.0'
'''

EXAMPLES = r'''
- name: Create a role FOO
  snowflake_role:
    connection:
      role: SECURITYADMIN
    name: FOO
    state: present
- name: Delete a role (FOO)
  snowflake_role:
    connection:
      role: SECURITYADMIN
    name: FOO
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


def role_exists(cursor, role):
    query = 'SHOW ROLES LIKE {0}'.format(quoted_identifier(role))
    cursor.execute(query)
    exists = cursor.rowcount > 0
    return exists


def role_delete(cursor, role):
    changed = False
    sfqid = None
    query = None
    if role_exists(cursor, role):
        query = 'DROP ROLE {0}'.format(role)
        cursor.execute(query)
        sfqid = cursor.sfqid
        changed = True

    return {'sql': query, 'role': role, 'changed': changed, 'sfqid': sfqid}


def role_create(cursor, role, comment, inherited_roles):
    changed = False
    sfqid = None
    query = None
    if not role_exists(cursor, role):
        query = ["CREATE ROLE {0}".format(role)]
        query = query + ["COMMENT='{0}'".format(comment)] if comment else query
        query = ' '.join(query)
        cursor.execute(query)
        sfqid = cursor.sfqid
        changed = True

    for inherited_role in inherited_roles:
        cursor.execute('GRANT ROLE {0} TO ROLE {1}'.format(inherited_role, role))

    return {'sql': query, 'role': role, 'changed': changed, 'sfqid': sfqid}


def main():

    module = AnsibleModule(
        argument_spec=dict(
            connection=dict(default={}, type=dict),
            name=dict(required=True, aliases=['names', 'role', 'roles']),
            state=dict(default="present", choices=["absent", "present"]),
            inherited_roles=dict(default='', aliases=['inherited_role']),
            comment=dict(default="")
        ),
        supports_check_mode=True
    )

    if not snowflake_found:
        module.fail_json(msg=snowflake_missing_lib_msg, exception=snowflake_missing_lib_exception)

    names = [n.strip() for n in module.params['name'].split(',')]
    state = module.params['state']
    comment = module.params['comment']
    inherited_roles = [x.strip() for x in module.params['inherited_roles'].split(',') if x]
    sfqid = None

    try:
        connection = snowflake_connect(module.params['connection'])
        cursor = connection.cursor()
    except Exception as e:
        module.fail_json(msg="Unable to connect to database, check user and password are correct or has the credentials. Exception message: %s" % (e))

    changed = False
    results = None
    if state == "present":
        if module.check_mode:
            changed = any([not role_exists(cursor, n) for n in names])
        else:
            try:
                results = [role_create(cursor, n, comment, inherited_roles) for n in names]
            except Exception as e:
                module.fail_json(msg="Error creating role: %s" % to_native(e), exception=traceback.format_exc())

    elif state == "absent":
        if module.check_mode:
            changed = any([role_exists(cursor, n) for n in names])
        else:
            try:
                results = [role_delete(cursor, n) for n in names]
            except Exception as e:
                module.fail_json(msg="Error deleting role: %s" % to_native(e), exception=traceback.format_exc())

    changed = any([result['changed'] for result in results]) if results else changed
    module.exit_json(changed=changed, state=state, results=results)


if __name__ == '__main__':
    main()
