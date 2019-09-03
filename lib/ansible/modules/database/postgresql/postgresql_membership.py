#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
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
module: postgresql_membership
short_description: Add or remove PostgreSQL roles from groups
description:
- Adds or removes PostgreSQL roles from groups (other roles).
- Users are roles with login privilege.
- Groups are PostgreSQL roles usually without LOGIN privelege.
- "Common use case:"
- 1) add a new group (groups) by M(postgresql_user) module with I(role_attr_flags=NOLOGIN)
- 2) grant them desired privileges by M(postgresql_privs) module
- 3) add desired PostgreSQL users to the new group (groups) by this module
version_added: '2.8'
options:
  groups:
    description:
    - The list of groups (roles) that need to be granted to or revoked from I(target_roles).
    required: yes
    type: list
    aliases:
    - group
    - source_role
    - source_roles
  target_roles:
    description:
    - The list of target roles (groups will be granted to them).
    required: yes
    type: list
    aliases:
    - target_role
    - users
    - user
  fail_on_role:
    description:
      - If C(yes), fail when group or target_role doesn't exist. If C(no), just warn and continue.
    default: yes
    type: bool
  state:
    description:
    - Membership state.
    - I(state=present) implies the I(groups)must be granted to I(target_roles).
    - I(state=absent) implies the I(groups) must be revoked from I(target_roles).
    type: str
    default: present
    choices: [ absent, present ]
  db:
    description:
    - Name of database to connect to.
    type: str
    aliases:
    - login_db
  session_role:
    description:
    - Switch to session_role after connecting.
      The specified session_role must be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though
      the session_role were the one that had logged in originally.
    type: str
seealso:
- module: postgresql_user
- module: postgresql_privs
- module: postgresql_owner
- name: PostgreSQL role membership reference
  description: Complete reference of the PostgreSQL role membership documentation.
  link: https://www.postgresql.org/docs/current/role-membership.html
- name: PostgreSQL role attributes reference
  description: Complete reference of the PostgreSQL role attributes documentation.
  link: https://www.postgresql.org/docs/current/role-attributes.html
author:
- Andrew Klychkov (@Andersson007)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Grant role read_only to alice and bob
  postgresql_membership:
    group: read_only
    target_roles:
    - alice
    - bob
    state: present

# you can also use target_roles: alice,bob,etc to pass the role list

- name: Revoke role read_only and exec_func from bob. Ignore if roles don't exist
  postgresql_membership:
    groups:
    - read_only
    - exec_func
    target_role: bob
    fail_on_role: no
    state: absent
'''

RETURN = r'''
queries:
    description: List of executed queries.
    returned: always
    type: str
    sample: [ "GRANT \"user_ro\" TO \"alice\"" ]
granted:
    description: Dict of granted groups and roles.
    returned: if I(state=present)
    type: dict
    sample: { "ro_group": [ "alice", "bob" ] }
revoked:
    description: Dict of revoked groups and roles.
    returned: if I(state=absent)
    type: dict
    sample: { "ro_group": [ "alice", "bob" ] }
state:
    description: Membership state that tried to be set.
    returned: always
    type: str
    sample: "present"
'''

try:
    from psycopg2.extras import DictCursor
except ImportError:
    # psycopg2 is checked by connect_to_db()
    # from ansible.module_utils.postgres
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.postgres import (
    connect_to_db,
    exec_sql,
    get_conn_params,
    PgMembership,
    postgres_common_argument_spec,
)


# ===========================================
# Module execution.
#

def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        groups=dict(type='list', aliases=['group', 'source_role', 'source_roles']),
        target_roles=dict(type='list', aliases=['target_role', 'user', 'users']),
        fail_on_role=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        db=dict(type='str', aliases=['login_db']),
        session_role=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    groups = module.params['groups']
    target_roles = module.params['target_roles']
    fail_on_role = module.params['fail_on_role']
    state = module.params['state']

    conn_params = get_conn_params(module, module.params, warn_db_default=False)
    db_connection = connect_to_db(module, conn_params, autocommit=False)
    cursor = db_connection.cursor(cursor_factory=DictCursor)

    ##############
    # Create the object and do main job:

    pg_membership = PgMembership(module, cursor, groups, target_roles, fail_on_role)

    if state == 'present':
        pg_membership.grant()

    elif state == 'absent':
        pg_membership.revoke()

    # Rollback if it's possible and check_mode:
    if module.check_mode:
        db_connection.rollback()
    else:
        db_connection.commit()

    cursor.close()
    db_connection.close()

    # Make return values:
    return_dict = dict(
        changed=pg_membership.changed,
        state=state,
        groups=pg_membership.groups,
        target_roles=pg_membership.target_roles,
        queries=pg_membership.executed_queries,
    )

    if state == 'present':
        return_dict['granted'] = pg_membership.granted
    elif state == 'absent':
        return_dict['revoked'] = pg_membership.revoked

    module.exit_json(**return_dict)


if __name__ == '__main__':
    main()
