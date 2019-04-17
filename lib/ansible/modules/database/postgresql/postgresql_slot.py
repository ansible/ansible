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
short_description: Add or remove slots from a PostgreSQL database
description:
- Add or remove physical or logical slots from a PostgreSQL database.
version_added: '2.8'

options:
  name:
    description:
    - Name of the slot to add or remove.
    type: str
    required: yes
    aliases:
    - slot_name
  slot_type:
    description:
    - Slot type.
    - For more information see
      U(https://www.postgresql.org/docs/current/protocol-replication.html) and
      U(https://www.postgresql.org/docs/current/logicaldecoding-explanation.html).
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
    - Optional parameter the when C(yes) specifies that the LSN for this replication slot be reserved
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
- The default authentication assumes that you are either logging in as or
  sudo'ing to the postgres account on the host.
- To avoid "Peer authentication failed for user postgres" error,
  use postgres user as a I(become_user).
- This module uses psycopg2, a Python PostgreSQL database adapter. You must
  ensure that psycopg2 is installed on the host before using this module.
- If the remote host is the PostgreSQL server (which is the default case), then
  PostgreSQL must also be installed on the remote host.
- For Ubuntu-based systems, install the postgresql, libpq-dev, and python-psycopg2 packages

requirements:
- psycopg2

author:
- John Scalia (@jscalia)
- Andew Klychkov (@Andersson007)
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

- name: Create logical_one logical slot to the database acme if doen't exist
  postgresql_slot:
    name: logical_slot_one
    slot_type: logical
    state: present
    output_plugin: custom_decoder_one

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
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.database import SQLParseError
from ansible.module_utils.postgres import postgres_common_argument_spec
from ansible.module_utils._text import to_native


def connect_to_db(module, kw, autocommit=False):
    try:
        db_connection = psycopg2.connect(**kw)
        if autocommit:
            if psycopg2.__version__ >= '2.4.2':
                db_connection.set_session(autocommit=True)
            else:
                db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least '
                                 'version 8.4 to support sslrootcert')

        module.fail_json(msg="unable to connect to database: %s" % to_native(e))

    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e))

    return db_connection


def get_pg_version(cursor):
    cursor.execute("select current_setting('server_version_num')")
    return int(cursor.fetchone()[0])


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
            ver = get_pg_version(self.cursor)
            if ver < 96000:
                query = "SELECT pg_create_physical_replication_slot('%s')" % self.name

            else:
                query = "SELECT pg_create_physical_replication_slot('%s', %s)" % (self.name, immediately_reserve)

        elif kind == 'logical':
            query = "SELECT pg_create_logical_replication_slot('%s', '%s')" % (self.name, output_plugin)

        self.changed = self.__exec_sql(query, ddl=True)

    def drop(self):
        if not self.exists:
            return False

        query = "SELECT pg_drop_replication_slot('%s')" % self.name
        self.changed = self.__exec_sql(query, ddl=True)

    def __slot_exists(self):
        query = "SELECT slot_type FROM pg_replication_slots WHERE slot_name = '%s'" % self.name
        res = self.__exec_sql(query, add_to_executed=False)
        if res:
            self.exists = True
            self.kind = res[0][0]

    def __exec_sql(self, query, ddl=False, add_to_executed=True):
        try:
            self.cursor.execute(query)

            if add_to_executed:
                self.executed_queries.append(query)

            if not ddl:
                res = self.cursor.fetchall()
                return res
            return True
        except SQLParseError as e:
            self.module.fail_json(msg=to_native(e))
        except psycopg2.ProgrammingError as e:
            self.module.fail_json(msg="Cannot execute SQL '%s': %s" % (query, to_native(e)))
        return False


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

    if not HAS_PSYCOPG2:
        module.fail_json(msg=missing_required_lib('psycopg2'))

    db = module.params["db"]
    name = module.params["name"]
    slot_type = module.params["slot_type"]
    immediately_reserve = module.params["immediately_reserve"]
    state = module.params["state"]
    ssl_rootcert = module.params["ca_cert"]
    output_plugin = module.params["output_plugin"]
    session_role = module.params["session_role"]

    if immediately_reserve and slot_type == 'logical':
        module.fail_json(msg="Module parameters immediately_reserve and slot_type=logical are mutually exclusive")

    # To use defaults values, keyword arguments must be absent, so
    # check which values are empty and don't include in the **kw
    # dictionary
    params_map = {
        "db": "database",
        "login_host": "host",
        "login_user": "user",
        "login_password": "password",
        "port": "port",
        "sslmode": "ssl_mode",
        "ca_cert": "ssl_rootcert"
    }
    kw = dict((params_map[k], v) for (k, v) in module.params.items()
              if k in params_map and v != '')

    # if a login_unix_socket is specified, incorporate it here
    is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    if psycopg2.__version__ < '2.4.3' and ssl_rootcert is not None:
        module.fail_json(msg='psycopg2 must be at least 2.4.3 in order to use the ssl_rootcert parameter')

    db_connection = connect_to_db(module, kw, autocommit=True)
    cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Switch role, if specified:
    if session_role:
        try:
            cursor.execute('SET ROLE %s' % session_role)
        except Exception as e:
            module.fail_json(msg="Could not switch role: %s" % to_native(e))

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

    module.exit_json(changed=changed, name=name, queries=pg_slot.executed_queries)


if __name__ == '__main__':
    main()
