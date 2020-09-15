#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Tobias Birkefeld (@tcraxs) <t@craxs.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: postgresql_sequence
short_description: Create, drop, or alter a PostgreSQL sequence
description:
- Allows to create, drop or change the definition of a sequence generator.
version_added: '2.9'
options:
  sequence:
    description:
    - The name of the sequence.
    required: true
    type: str
    aliases:
    - name
  state:
    description:
    - The sequence state.
    - If I(state=absent) other options will be ignored except of I(name) and
      I(schema).
    default: present
    choices: [ absent, present ]
    type: str
  data_type:
    description:
    - Specifies the data type of the sequence. Valid types are bigint, integer,
      and smallint. bigint is the default. The data type determines the default
      minimum and maximum values of the sequence. For more info see the
      documentation
      U(https://www.postgresql.org/docs/current/sql-createsequence.html).
    - Supported from PostgreSQL 10.
    choices: [ bigint, integer, smallint ]
    type: str
  increment:
    description:
    - Increment specifies which value is added to the current sequence value
      to create a new value.
    - A positive value will make an ascending sequence, a negative one a
      descending sequence. The default value is 1.
    type: int
  minvalue:
    description:
    - Minvalue determines the minimum value a sequence can generate. The
      default for an ascending sequence is 1. The default for a descending
      sequence is the minimum value of the data type.
    type: int
    aliases:
      - min
  maxvalue:
    description:
    - Maxvalue determines the maximum value for the sequence. The default for
      an ascending sequence is the maximum
      value of the data type. The default for a descending sequence is -1.
    type: int
    aliases:
      - max
  start:
    description:
    - Start allows the sequence to begin anywhere. The default starting value
      is I(minvalue) for ascending sequences and I(maxvalue) for descending
      ones.
    type: int
  cache:
    description:
    - Cache specifies how many sequence numbers are to be preallocated and
      stored in memory for faster access. The minimum value is 1 (only one
      value can be generated at a time, i.e., no cache), and this is also
      the default.
    type: int
  cycle:
    description:
    - The cycle option allows the sequence to wrap around when the I(maxvalue)
      or I(minvalue) has been reached by an ascending or descending sequence
      respectively. If the limit is reached, the next number generated will be
      the minvalue or maxvalue, respectively.
    - If C(false) (NO CYCLE) is specified, any calls to nextval after the sequence
      has reached its maximum value will return an error. False (NO CYCLE) is
      the default.
    type: bool
    default: no
  cascade:
    description:
    - Automatically drop objects that depend on the sequence, and in turn all
      objects that depend on those objects.
    - Ignored if I(state=present).
    - Only used with I(state=absent).
    type: bool
    default: no
  rename_to:
    description:
    - The new name for the I(sequence).
    - Works only for existing sequences.
    type: str
  owner:
    description:
    - Set the owner for the I(sequence).
    type: str
  schema:
    description:
    - The schema of the I(sequence). This is be used to create and relocate
      a I(sequence) in the given schema.
    default: public
    type: str
  newschema:
    description:
    - The new schema for the I(sequence). Will be used for moving a
      I(sequence) to another I(schema).
    - Works only for existing sequences.
    type: str
  session_role:
    description:
    - Switch to session_role after connecting. The specified I(session_role)
      must be a role that the current I(login_user) is a member of.
    - Permissions checking for SQL commands is carried out as though
      the I(session_role) were the one that had logged in originally.
    type: str
  db:
    description:
    - Name of database to connect to and run queries against.
    type: str
    aliases:
    - database
    - login_db
notes:
- If you do not pass db parameter, sequence will be created in the database
  named postgres.
seealso:
- module: postgresql_table
- module: postgresql_owner
- module: postgresql_privs
- module: postgresql_tablespace
- name: CREATE SEQUENCE reference
  description: Complete reference of the CREATE SEQUENCE command documentation.
  link: https://www.postgresql.org/docs/current/sql-createsequence.html
- name: ALTER SEQUENCE reference
  description: Complete reference of the ALTER SEQUENCE command documentation.
  link: https://www.postgresql.org/docs/current/sql-altersequence.html
- name: DROP SEQUENCE reference
  description: Complete reference of the DROP SEQUENCE command documentation.
  link: https://www.postgresql.org/docs/current/sql-dropsequence.html
author:
- Tobias Birkefeld (@tcraxs)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Create an ascending bigint sequence called foobar in the default
        database
  postgresql_sequence:
    name: foobar

- name: Create an ascending integer sequence called foobar, starting at 101
  postgresql_sequence:
    name: foobar
    data_type: integer
    start: 101

- name: Create an descending sequence called foobar, starting at 101 and
        preallocated 10 sequence numbers in cache
  postgresql_sequence:
    name: foobar
    increment: -1
    cache: 10
    start: 101

- name: Create an ascending sequence called foobar, which cycle between 1 to 10
  postgresql_sequence:
    name: foobar
    cycle: yes
    min: 1
    max: 10

- name: Create an ascending bigint sequence called foobar in the default
        database with owner foobar
  postgresql_sequence:
    name: foobar
    owner: foobar

- name: Rename an existing sequence named foo to bar
  postgresql_sequence:
    name: foo
    rename_to: bar

- name: Change the schema of an existing sequence to foobar
  postgresql_sequence:
    name: foobar
    newschema: foobar

- name: Change the owner of an existing sequence to foobar
  postgresql_sequence:
    name: foobar
    owner: foobar

- name: Drop a sequence called foobar
  postgresql_sequence:
    name: foobar
    state: absent

- name: Drop a sequence called foobar with cascade
  postgresql_sequence:
    name: foobar
    cascade: yes
    state: absent
'''

RETURN = r'''
state:
  description: Sequence state at the end of execution.
  returned: always
  type: str
  sample: 'present'
sequence:
  description: Sequence name.
  returned: always
  type: str
  sample: 'foobar'
queries:
    description: List of queries that was tried to be executed.
    returned: always
    type: str
    sample: [ "CREATE SEQUENCE \"foo\"" ]
schema:
    description: Name of the schema of the sequence
    returned: always
    type: str
    sample: 'foo'
data_type:
    description: Shows the current data type of the sequence.
    returned: always
    type: str
    sample: 'bigint'
increment:
    description: The value of increment of the sequence. A positive value will
                 make an ascending sequence, a negative one a descending
                 sequence.
    returned: always
    type: int
    sample: '-1'
minvalue:
    description: The value of minvalue of the sequence.
    returned: always
    type: int
    sample: '1'
maxvalue:
    description: The value of maxvalue of the sequence.
    returned: always
    type: int
    sample: '9223372036854775807'
start:
    description: The value of start of the sequence.
    returned: always
    type: int
    sample: '12'
cycle:
    description: Shows if the sequence cycle or not.
    returned: always
    type: str
    sample: 'NO'
owner:
    description: Shows the current owner of the sequence
                 after the successful run of the task.
    returned: always
    type: str
    sample: 'postgres'
newname:
    description: Shows the new sequence name after rename.
    returned: on success
    type: str
    sample: 'barfoo'
newschema:
    description: Shows the new schema of the sequence after schema change.
    returned: on success
    type: str
    sample: 'foobar'
'''


try:
    from psycopg2.extras import DictCursor
except ImportError:
    # psycopg2 is checked by connect_to_db()
    # from ansible.module_utils.postgres
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import pg_quote_identifier
from ansible.module_utils.postgres import (
    connect_to_db,
    exec_sql,
    get_conn_params,
    postgres_common_argument_spec,
)


class Sequence(object):
    """Implements behavior of CREATE, ALTER or DROP SEQUENCE PostgreSQL command.

    Arguments:
        module (AnsibleModule) -- object of AnsibleModule class
        cursor (cursor) -- cursor object of psycopg2 library

    Attributes:
        module (AnsibleModule) -- object of AnsibleModule class
        cursor (cursor) -- cursor object of psycopg2 library
        changed (bool) --  something was changed after execution or not
        executed_queries (list) -- executed queries
        name (str) -- name of the sequence
        owner (str) -- name of the owner of the sequence
        schema (str) -- name of the schema (default: public)
        data_type (str) -- data type of the sequence
        start_value (int) -- value of the sequence start
        minvalue (int) -- minimum value of the sequence
        maxvalue (int) -- maximum value of the sequence
        increment (int) -- increment value of the sequence
        cycle (bool) -- sequence can cycle or not
        new_name (str) -- name of the renamed sequence
        new_schema (str) -- name of the new schema
        exists (bool) -- sequence exists or not
    """

    def __init__(self, module, cursor):
        self.module = module
        self.cursor = cursor
        self.executed_queries = []
        self.name = self.module.params['sequence']
        self.owner = ''
        self.schema = self.module.params['schema']
        self.data_type = ''
        self.start_value = ''
        self.minvalue = ''
        self.maxvalue = ''
        self.increment = ''
        self.cycle = ''
        self.new_name = ''
        self.new_schema = ''
        self.exists = False
        # Collect info
        self.get_info()

    def get_info(self):
        """Getter to refresh and get sequence info"""
        query = ("SELECT "
                 "s.sequence_schema AS schemaname, "
                 "s.sequence_name AS sequencename, "
                 "pg_get_userbyid(c.relowner) AS sequenceowner, "
                 "s.data_type::regtype AS data_type, "
                 "s.start_value AS start_value, "
                 "s.minimum_value AS min_value, "
                 "s.maximum_value AS max_value, "
                 "s.increment AS increment_by, "
                 "s.cycle_option AS cycle "
                 "FROM information_schema.sequences s "
                 "JOIN pg_class c ON c.relname = s.sequence_name "
                 "LEFT JOIN pg_namespace n ON n.oid = c.relnamespace "
                 "WHERE NOT pg_is_other_temp_schema(n.oid) "
                 "AND c.relkind = 'S'::\"char\" "
                 "AND sequence_name = %(name)s "
                 "AND sequence_schema = %(schema)s")

        res = exec_sql(self, query,
                       query_params={'name': self.name, 'schema': self.schema},
                       add_to_executed=False)

        if not res:
            self.exists = False
            return False

        if res:
            self.exists = True
            self.schema = res[0]['schemaname']
            self.name = res[0]['sequencename']
            self.owner = res[0]['sequenceowner']
            self.data_type = res[0]['data_type']
            self.start_value = res[0]['start_value']
            self.minvalue = res[0]['min_value']
            self.maxvalue = res[0]['max_value']
            self.increment = res[0]['increment_by']
            self.cycle = res[0]['cycle']

    def create(self):
        """Implements CREATE SEQUENCE command behavior."""
        query = ['CREATE SEQUENCE']
        query.append(self.__add_schema())

        if self.module.params.get('data_type'):
            query.append('AS %s' % self.module.params['data_type'])

        if self.module.params.get('increment'):
            query.append('INCREMENT BY %s' % self.module.params['increment'])

        if self.module.params.get('minvalue'):
            query.append('MINVALUE %s' % self.module.params['minvalue'])

        if self.module.params.get('maxvalue'):
            query.append('MAXVALUE %s' % self.module.params['maxvalue'])

        if self.module.params.get('start'):
            query.append('START WITH %s' % self.module.params['start'])

        if self.module.params.get('cache'):
            query.append('CACHE %s' % self.module.params['cache'])

        if self.module.params.get('cycle'):
            query.append('CYCLE')

        return exec_sql(self, ' '.join(query), ddl=True)

    def drop(self):
        """Implements DROP SEQUENCE command behavior."""
        query = ['DROP SEQUENCE']
        query.append(self.__add_schema())

        if self.module.params.get('cascade'):
            query.append('CASCADE')

        return exec_sql(self, ' '.join(query), ddl=True)

    def rename(self):
        """Implements ALTER SEQUENCE RENAME TO command behavior."""
        query = ['ALTER SEQUENCE']
        query.append(self.__add_schema())
        query.append('RENAME TO %s' % pg_quote_identifier(self.module.params['rename_to'], 'sequence'))

        return exec_sql(self, ' '.join(query), ddl=True)

    def set_owner(self):
        """Implements ALTER SEQUENCE OWNER TO command behavior."""
        query = ['ALTER SEQUENCE']
        query.append(self.__add_schema())
        query.append('OWNER TO %s' % pg_quote_identifier(self.module.params['owner'], 'role'))

        return exec_sql(self, ' '.join(query), ddl=True)

    def set_schema(self):
        """Implements ALTER SEQUENCE SET SCHEMA command behavior."""
        query = ['ALTER SEQUENCE']
        query.append(self.__add_schema())
        query.append('SET SCHEMA %s' % pg_quote_identifier(self.module.params['newschema'], 'schema'))

        return exec_sql(self, ' '.join(query), ddl=True)

    def __add_schema(self):
        return '.'.join([pg_quote_identifier(self.schema, 'schema'),
                        pg_quote_identifier(self.name, 'sequence')])


# ===========================================
# Module execution.
#

def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        sequence=dict(type='str', required=True, aliases=['name']),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        data_type=dict(type='str', choices=['bigint', 'integer', 'smallint']),
        increment=dict(type='int'),
        minvalue=dict(type='int', aliases=['min']),
        maxvalue=dict(type='int', aliases=['max']),
        start=dict(type='int'),
        cache=dict(type='int'),
        cycle=dict(type='bool', default=False),
        schema=dict(type='str', default='public'),
        cascade=dict(type='bool', default=False),
        rename_to=dict(type='str'),
        owner=dict(type='str'),
        newschema=dict(type='str'),
        db=dict(type='str', default='', aliases=['login_db', 'database']),
        session_role=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['rename_to', 'data_type'],
            ['rename_to', 'increment'],
            ['rename_to', 'minvalue'],
            ['rename_to', 'maxvalue'],
            ['rename_to', 'start'],
            ['rename_to', 'cache'],
            ['rename_to', 'cycle'],
            ['rename_to', 'cascade'],
            ['rename_to', 'owner'],
            ['rename_to', 'newschema'],
            ['cascade', 'data_type'],
            ['cascade', 'increment'],
            ['cascade', 'minvalue'],
            ['cascade', 'maxvalue'],
            ['cascade', 'start'],
            ['cascade', 'cache'],
            ['cascade', 'cycle'],
            ['cascade', 'owner'],
            ['cascade', 'newschema'],
        ]
    )

    # Note: we don't need to check mutually exclusive params here, because they are
    # checked automatically by AnsibleModule (mutually_exclusive=[] list above).

    # Change autocommit to False if check_mode:
    autocommit = not module.check_mode
    # Connect to DB and make cursor object:
    conn_params = get_conn_params(module, module.params)
    db_connection = connect_to_db(module, conn_params, autocommit=autocommit)
    cursor = db_connection.cursor(cursor_factory=DictCursor)

    ##############
    # Create the object and do main job:
    data = Sequence(module, cursor)

    # Set defaults:
    changed = False

    # Create new sequence
    if not data.exists and module.params['state'] == 'present':
        if module.params.get('rename_to'):
            module.fail_json(msg="Sequence '%s' does not exist, nothing to rename" % module.params['sequence'])
        if module.params.get('newschema'):
            module.fail_json(msg="Sequence '%s' does not exist, change of schema not possible" % module.params['sequence'])

        changed = data.create()

    # Drop non-existing sequence
    elif not data.exists and module.params['state'] == 'absent':
        # Nothing to do
        changed = False

    # Drop existing sequence
    elif data.exists and module.params['state'] == 'absent':
        changed = data.drop()

    # Rename sequence
    if data.exists and module.params.get('rename_to'):
        if data.name != module.params['rename_to']:
            changed = data.rename()
            if changed:
                data.new_name = module.params['rename_to']

    # Refresh information
    if module.params['state'] == 'present':
        data.get_info()

    # Change owner, schema and settings
    if module.params['state'] == 'present' and data.exists:
        # change owner
        if module.params.get('owner'):
            if data.owner != module.params['owner']:
                changed = data.set_owner()

        # Set schema
        if module.params.get('newschema'):
            if data.schema != module.params['newschema']:
                changed = data.set_schema()
                if changed:
                    data.new_schema = module.params['newschema']

    # Rollback if it's possible and check_mode:
    if module.check_mode:
        db_connection.rollback()
    else:
        db_connection.commit()

    cursor.close()
    db_connection.close()

    # Make return values:
    kw = dict(
        changed=changed,
        state='present',
        sequence=data.name,
        queries=data.executed_queries,
        schema=data.schema,
        data_type=data.data_type,
        increment=data.increment,
        minvalue=data.minvalue,
        maxvalue=data.maxvalue,
        start=data.start_value,
        cycle=data.cycle,
        owner=data.owner,
    )

    if module.params['state'] == 'present':
        if data.new_name:
            kw['newname'] = data.new_name
        if data.new_schema:
            kw['newschema'] = data.new_schema

    elif module.params['state'] == 'absent':
        kw['state'] = 'absent'

    module.exit_json(**kw)


if __name__ == '__main__':
    main()
