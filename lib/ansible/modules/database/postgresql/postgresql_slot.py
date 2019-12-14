#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, John Scalia (@jscalia), Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: postgresql_slot
short_description: Add or remove replication slots from a PostgreSQL database
description:
- Add or remove physical or logical replication slots from a PostgreSQL database.
version_added: '2.8'

options:
  name:
    description:
    - Name of the replication slot to add or remove.
    type: str
    required: yes
    aliases:
    - slot_name
  slot_type:
    description:
    - Slot type.
    type: str
    default: physical
    choices: [ logical, physical ]
  state:
    description:
    - The slot state.
    - I(state=present) implies the slot must be present in the system.
    - I(state=absent) implies the I(groups) must be revoked from I(target_roles).
    type: str
    default: present
    choices: [ absent, present ]
  immediately_reserve:
    description:
    - Optional parameter that when C(yes) specifies that the LSN for this replication slot be reserved
      immediately, otherwise the default, C(no), specifies that the LSN is reserved on the first connection
      from a streaming replication client.
    - Is available from PostgreSQL version 9.6.
    - Uses only with I(slot_type=physical).
    - Mutually exclusive with I(slot_type=logical).
    type: bool
    default: no
  output_plugin:
    description:
    - All logical slots must indicate which output plugin decoder they're using.
    - This parameter does not apply to physical slots.
    - It will be ignored with I(slot_type=physical).
    type: str
    default: "test_decoding"
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

notes:
- Physical replication slots were introduced to PostgreSQL with version 9.4,
  while logical replication slots were added beginning with version 10.0.

seealso:
- name: PostgreSQL pg_replication_slots view reference
  description: Complete reference of the PostgreSQL pg_replication_slots view.
  link: https://www.postgresql.org/docs/current/view-pg-replication-slots.html
- name: PostgreSQL streaming replication protocol reference
  description: Complete reference of the PostgreSQL streaming replication protocol documentation.
  link: https://www.postgresql.org/docs/current/protocol-replication.html
- name: PostgreSQL logical replication protocol reference
  description: Complete reference of the PostgreSQL logical replication protocol documentation.
  link: https://www.postgresql.org/docs/current/protocol-logical-replication.html

author:
- John Scalia (@jscalia)
- Andrew Klychkov (@Andersson007)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Create physical_one physical slot if doesn't exist
  become_user: postgres
  postgresql_slot:
    slot_name: physical_one
    db: ansible

- name: Remove physical_one slot if exists
  become_user: postgres
  postgresql_slot:
    slot_name: physical_one
    db: ansible
    state: absent

- name: Create logical_one logical slot to the database acme if doesn't exist
  postgresql_slot:
    name: logical_slot_one
    slot_type: logical
    state: present
    output_plugin: custom_decoder_one
    db: "acme"

- name: Remove logical_one slot if exists from the cluster running on another host and non-standard port
  postgresql_slot:
    name: logical_one
    login_host: mydatabase.example.org
    port: 5433
    login_user: ourSuperuser
    login_password: thePassword
    state: absent
'''

RETURN = r'''
name:
  description: Name of the slot
  returned: always
  type: str
  sample: "physical_one"
queries:
  description: List of executed queries.
  returned: always
  type: str
  sample: [ "SELECT pg_create_physical_replication_slot('physical_one', False, False)" ]
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
    postgres_common_argument_spec,
)


# ===========================================
# PostgreSQL module specific support methods.
#

class PgSlot(object):
    def __init__(self, module, cursor, name):
        self.module = module
        self.cursor = cursor
        self.name = name
        self.exists = False
        self.kind = ''
        self.__slot_exists()
        self.changed = False
        self.executed_queries = []

    def create(self, kind='physical', immediately_reserve=False, output_plugin=False, just_check=False):
        if self.exists:
            if self.kind == kind:
                return False
            else:
                self.module.warn("slot with name '%s' already exists "
                                 "but has another type '%s'" % (self.name, self.kind))
                return False

        if just_check:
            return None

        if kind == 'physical':
            # Check server version (needs for immedately_reserverd needs 9.6+):
            if self.cursor.connection.server_version < 96000:
                query = "SELECT pg_create_physical_replication_slot(%(name)s)"

            else:
                query = "SELECT pg_create_physical_replication_slot(%(name)s, %(i_reserve)s)"

            self.changed = exec_sql(self, query,
                                    query_params={'name': self.name, 'i_reserve': immediately_reserve},
                                    ddl=True)

        elif kind == 'logical':
            query = "SELECT pg_create_logical_replication_slot(%(name)s, %(o_plugin)s)"
            self.changed = exec_sql(self, query,
                                    query_params={'name': self.name, 'o_plugin': output_plugin}, ddl=True)

    def drop(self):
        if not self.exists:
            return False

        query = "SELECT pg_drop_replication_slot(%(name)s)"
        self.changed = exec_sql(self, query, query_params={'name': self.name}, ddl=True)

    def __slot_exists(self):
        query = "SELECT slot_type FROM pg_replication_slots WHERE slot_name = %(name)s"
        res = exec_sql(self, query, query_params={'name': self.name}, add_to_executed=False)
        if res:
            self.exists = True
            self.kind = res[0][0]


# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        db=dict(type="str", aliases=["login_db"]),
        name=dict(type="str", aliases=["slot_name"]),
        slot_type=dict(type="str", default="physical", choices=["logical", "physical"]),
        immediately_reserve=dict(type="bool", default=False),
        session_role=dict(type="str"),
        output_plugin=dict(type="str", default="test_decoding"),
        state=dict(type="str", default="present", choices=["absent", "present"]),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params["name"]
    slot_type = module.params["slot_type"]
    immediately_reserve = module.params["immediately_reserve"]
    state = module.params["state"]
    output_plugin = module.params["output_plugin"]

    if immediately_reserve and slot_type == 'logical':
        module.fail_json(msg="Module parameters immediately_reserve and slot_type=logical are mutually exclusive")

    # When slot_type is logical and parameter db is not passed,
    # the default database will be used to create the slot and
    # the user should know about this.
    # When the slot type is physical,
    # it doesn't matter which database will be used
    # because physical slots are global objects.
    if slot_type == 'logical':
        warn_db_default = True
    else:
        warn_db_default = False

    conn_params = get_conn_params(module, module.params, warn_db_default=warn_db_default)
    db_connection = connect_to_db(module, conn_params, autocommit=True)
    cursor = db_connection.cursor(cursor_factory=DictCursor)

    ##################################
    # Create an object and do main job
    pg_slot = PgSlot(module, cursor, name)

    changed = False

    if module.check_mode:
        if state == "present":
            if not pg_slot.exists:
                changed = True

            pg_slot.create(slot_type, immediately_reserve, output_plugin, just_check=True)

        elif state == "absent":
            if pg_slot.exists:
                changed = True
    else:
        if state == "absent":
            pg_slot.drop()

        elif state == "present":
            pg_slot.create(slot_type, immediately_reserve, output_plugin)

        changed = pg_slot.changed

    db_connection.close()
    module.exit_json(changed=changed, name=name, queries=pg_slot.executed_queries)


if __name__ == '__main__':
    main()
