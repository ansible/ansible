#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Tobias Birkefeld (@tcraxs) <t@craxs.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
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
- Allows to create, drop or change the definition of a sequence generator
  U(https://www.postgresql.org/docs/current/sql-createsequence.html).
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
    - I(state=absent) is mutually exclusive with I(data_type), I(increment),
      I(minvalue), I(maxvalue), I(start), I(cache), I(cycle), I(rename_to) ,
      I(newschema) and I(owner).
    default: present
    choices: [ absent, present ]
    type: str
  data_type:
    description:
    - Specifies the data type of the sequence. Valid types are bigint, integer,
      and smallint. bigint is the default. The data type determines the default
      minimum and maximum values of the sequence. For more info see the
      documention
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
  maxvalue:
    description:
    - Maxvalue determines the maximum value for the sequence. The default for
      an ascending sequence is the maximum
      value of the data type. The default for a descending sequence is -1.
    type: int
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
    - If false (NO CYCLE) is specified, any calls to nextval after the sequence
      has reached its maximum value will return an error. False (NO CYCLE) is
      the default.
    type: bool
  cascade:
    description:
    - Automatically drop objects that depend on the sequence, and in turn all
      objects that depend on those objects.
    - Only used when I(state=absent).
    type: bool
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
    - The schema in the new I(sequence) will be created.
    type: str
  newschema:
    description:
    - The new schema for the I(sequence).
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
  port:
    description:
    - Database port to connect.
    default: 5432
    type: int
    aliases:
    - login_port
  login_user:
    description:
    - User (role) used to authenticate with PostgreSQL.
    default: postgres
    type: str
  login_password:
    description:
    - Password used to authenticate with PostgreSQL.
    type: str
  login_host:
    description:
    - Host running PostgreSQL.
    type: str
  login_unix_socket:
    description:
    - Path to a Unix domain socket for local connections.
    type: str
  ssl_mode:
    description:
    - Determines whether or with what priority a secure SSL TCP/IP connection
      will be negotiated with the server.
    - See U(https://www.postgresql.org/docs/current/static/libpq-ssl.html) for
      more information on the modes.
    - Default of C(prefer) matches libpq default.
    default: prefer
    choices: [ allow, disable, prefer, require, verify-ca, verify-full ]
    type: str
  ca_cert:
    description:
    - Specifies the name of a file containing SSL certificate authority (CA)
      certificate(s).
    - If the file exists, the server's certificate will be
      verified to be signed by one of these authorities.
    type: str
    aliases: [ ssl_rootcert ]
notes:
- If you do not pass db parameter, sequence will be created in the database
  named postgres.
- The default authentication assumes that you are either logging in as or
  sudo'ing to the postgres account on the host.
- To avoid "Peer authentication failed for user postgres" error,
  use postgres user as a I(become_user).
- This module uses psycopg2, a Python PostgreSQL database adapter. You must
  ensure that psycopg2 is installed on the host before using this module.
- If the remote host is the PostgreSQL server (which is the default case), then
  PostgreSQL must also be installed on the remote host. For Ubuntu-based
  systems, install the postgresql, libpq-dev, and python-psycopg2 packages
  on the remote host before using this module.
requirements: [ psycopg2 ]
author:
- Tobias Birkefeld (@tcraxs)
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
    description: Shows the current owner of the sequence.
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
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.database import SQLParseError, pg_quote_identifier
from ansible.module_utils.postgres import postgres_common_argument_spec
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems


def connect_to_db(module, kw, autocommit=False):
    try:
        db_connection = psycopg2.connect(**kw)
        if autocommit:
            if psycopg2.__version__ >= '2.4.2':
                db_connection.set_session(autocommit=True)
            else:
                db_connection.set_isolation_level(
                    psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least '
                                 'version 8.4 to support sslrootcert')

        module.fail_json(msg="unable to connect to database: %s" % to_native(e))

    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e))

    return db_connection


class Sequence(object):
    def __init__(self, name, module, cursor, schema):
        if not schema:
            schema = 'public'
        self.name = name
        self.module = module
        self.cursor = cursor
        self.owner = ''
        self.sequence_schema = schema
        self.data_type = ''
        self.numeric_precision = ''
        self.numeric_precision_radix = ''
        self.numeric_scale = ''
        self.start_value = ''
        self.minimum_value = ''
        self.maximum_value = ''
        self.increment = ''
        self.cycle_option = ''
        self.new_name = ''
        self.new_schema = ''

        self.exists = False
        self.executed_queries = []
        # Collect info
        self.get_info()

    def get_info(self):
        """Getter to refresh and get sequence info"""
        query = ("SELECT * FROM information_schema.sequences "
                 "WHERE sequence_name = '%s' "
                 "AND sequence_schema = '%s'" % (self.name, self.sequence_schema))

        res = self.__exec_sql(query, add_to_executed=False)

        if not res:
            self.exists = False
            return False

        if res[0][0]:
            self.exists = True
            self.sequence_schema = res[0][1]
            self.name = res[0][2]
            self.data_type = res[0][3]
            self.numeric_precision = res[0][4]
            self.numeric_precision_radix = res[0][5]
            self.numeric_scale = res[0][6]
            self.start_value = res[0][7]
            self.minimum_value = res[0][8]
            self.maximum_value = res[0][9]
            self.increment = res[0][10]
            self.cycle_option = res[0][11]

        # get owner info
        query = ("SELECT c.relname,a.rolname,n.nspname "
                 "FROM pg_class as c "
                 "JOIN pg_authid as a on (c.relowner = a.oid) "
                 "JOIN pg_namespace as n on (c.relnamespace = n.oid) "
                 "WHERE c.relkind = 'S' and "
                 "c.relname = '%s' and "
                 "n.nspname = '%s'" % (self.name, self.sequence_schema))

        res = self.__exec_sql(query, add_to_executed=False)

        if not res:
            self.exists = False
            return False

        if res[0][0]:
            self.owner = res[0][1]

    def create(self, data_type=None, increment=None, minimum_value=None,
               maximum_value=None, start=None, cache=None, cycle_option=False,
               schema=None):
        """Create function for sequence"""
        query = "CREATE SEQUENCE"

        if schema:
            query += " %s.%s" % (pg_quote_identifier(schema, 'schema'),
                                 pg_quote_identifier(self.name, 'sequence'))
        else:
            query += " %s" % pg_quote_identifier(self.name, 'sequence')

        if data_type:
            query += " AS %s" % data_type

        if increment:
            query += " INCREMENT BY %s" % increment

        if minimum_value:
            query += " MINVALUE %s" % minimum_value

        if maximum_value:
            query += " MAXVALUE %s" % maximum_value

        if start:
            query += " START WITH %s" % start

        if cache:
            query += " CACHE %s" % cache

        if cycle_option:
            query += " CYCLE"

        return self.__exec_sql(query, ddl=True)

    def drop(self, cascade=False, schema=None):
        query = "DROP SEQUENCE"
        if schema:
            query += " %s.%s" % (pg_quote_identifier(schema, 'schema'),
                                 pg_quote_identifier(self.name, 'sequence'))
        else:
            query += " %s" % pg_quote_identifier(self.name, 'sequence')

        if cascade:
            query += " CASCADE"

        return self.__exec_sql(query, ddl=True)

    def rename(self, rename_to, schema=None):
        query = "ALTER SEQUENCE"
        if schema:
            query += " %s.%s" % (pg_quote_identifier(schema, 'schema'),
                                 pg_quote_identifier(self.name, 'sequence'))
        else:
            query += " %s" % pg_quote_identifier(self.name, 'sequence')

        query += " RENAME TO %s" % pg_quote_identifier(rename_to, 'sequence')

        return self.__exec_sql(query, ddl=True)

    def set_owner(self, new_owner, schema=None):
        query = "ALTER SEQUENCE"
        if schema:
            query += " %s.%s" % (pg_quote_identifier(schema, 'schema'),
                                 pg_quote_identifier(self.name, 'sequence'))
        else:
            query += " %s" % pg_quote_identifier(self.name, 'sequence')

        query += " OWNER TO %s" % pg_quote_identifier(new_owner, 'role')

        return self.__exec_sql(query, ddl=True)

    def set_schema(self, newschema, schema=None):
        query = "ALTER SEQUENCE"
        if schema:
            query += " %s.%s" % (pg_quote_identifier(schema, 'schema'),
                                 pg_quote_identifier(self.name, 'sequence'))
        else:
            query += " %s" % pg_quote_identifier(self.name, 'sequence')

        query += " SET SCHEMA %s" % pg_quote_identifier(newschema, 'schema')

        return self.__exec_sql(query, ddl=True)

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
        sequence=dict(type='str', required=True, aliases=['name']),
        state=dict(type='str', default="present", choices=["absent", "present"]),
        data_type=dict(type='str', choices=['bigint', 'integer', 'smallint']),
        increment=dict(type='int'),
        minvalue=dict(type='int'),
        maxvalue=dict(type='int'),
        start=dict(type='int'),
        cache=dict(type='int'),
        cycle=dict(type='bool'),
        schema=dict(type='str'),
        cascade=dict(type='bool'),

        rename_to=dict(type='str'),
        owner=dict(type='str'),
        newschema=dict(type='str'),

        db=dict(type='str', default='', aliases=['login_db', 'database']),
        session_role=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=(('positional_args', 'named_args'),),
        supports_check_mode=True,
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg=missing_required_lib("psycopg2"))

    sequence = module.params["sequence"]
    state = module.params["state"]
    data_type = module.params["data_type"]
    increment = module.params["increment"]
    minvalue = module.params["minvalue"]
    maxvalue = module.params["maxvalue"]
    start = module.params["start"]
    cache = module.params["cache"]
    cycle = module.params["cycle"]
    cascade = module.params["cascade"]
    rename_to = module.params["rename_to"]
    schema = module.params["schema"]
    owner = module.params["owner"]
    newschema = module.params["newschema"]
    sslrootcert = module.params["ca_cert"]
    session_role = module.params["session_role"]

    # Check mutual exclusive parameters:
    if state == 'absent' and (data_type or increment or minvalue or maxvalue or
                              start or cache or cycle or
                              rename_to or newschema or owner):
        module.fail_json(msg="'%s': state=absent is mutually exclusive with: "
                             "data_type, increment, minvalue, maxvalue, "
                             "start, cache, cycle, "
                             "rename_to, newschema or owner" % sequence)

    if rename_to and (data_type or increment or minvalue or maxvalue or start
                      or cache or cycle or cascade or newschema or owner):
        module.fail_json(msg="'%s': rename_to is mutually exclusive with: "
                             "data_type, increment, minvalue, maxvalue, "
                             "start, cache, cycle, cascade, "
                             "newschema or owner" % sequence)

    if cascade and (data_type or increment or minvalue or maxvalue or start or
                    cache or cycle or rename_to or
                    newschema or owner):
        module.fail_json(msg="'%s': cascade is mutually exclusive with: "
                             "data_type, increment, minvalue, "
                             "maxvalue, start, cache, cycle, "
                             "rename_to, newschema "
                             "or owner" % sequence)

    # To use defaults values, keyword arguments must be absent, so
    # check which values are empty and don't include in the **kw
    # dictionary
    params_map = {
        "login_host": "host",
        "login_user": "user",
        "login_password": "password",
        "port": "port",
        "db": "database",
        "ssl_mode": "sslmode",
        "ca_cert": "sslrootcert"
    }
    kw = dict((params_map[k], v) for (k, v) in iteritems(module.params)
              if k in params_map and v != "" and v is not None)

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] is None or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    if psycopg2.__version__ < '2.4.3' and sslrootcert:
        module.fail_json(msg='psycopg2 must be at least 2.4.3 '
                             'in order to user the ca_cert parameter')

    db_connection = connect_to_db(module, kw, autocommit=True)
    cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Switch role, if specified:
    if session_role:
        try:
            cursor.execute('SET ROLE %s' % session_role)
        except Exception as e:
            module.fail_json(msg="Could not switch role: '%s'" % to_native(e))

    # Change autocommit to False if check_mode:
    if module.check_mode:
        if psycopg2.__version__ >= '2.4.2':
            db_connection.set_session(autocommit=False)
        else:
            db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)

    ##############
    # Do main job:
    sequence_obj = Sequence(sequence, module, cursor, schema)

    # Set defaults:
    autocommit = False
    changed = False

    # Create new sequence
    if not sequence_obj.exists and state == 'present':
        if rename_to:
            module.fail_json(msg="Sequence '%s' does not exist, nothing to rename" % sequence)
        if newschema:
            module.fail_json(msg="Sequence '%s' does not exist, change of schema not possible" % sequence)

        changed = sequence_obj.create(data_type=data_type, increment=increment,
                                      minimum_value=minvalue,
                                      maximum_value=maxvalue, start=start,
                                      cache=cache, cycle_option=cycle,
                                      schema=schema)

    # Drop non-existing sequence
    elif not sequence_obj.exists and state == 'absent':
        # Nothing to do
        module.fail_json(msg="Tries to drop nonexistent sequence '%s'" % sequence)

    # Drop existing sequence
    elif sequence_obj.exists and state == 'absent':
        changed = sequence_obj.drop(cascade=cascade, schema=schema)

    # Rename sequence
    if sequence_obj.exists and rename_to:
        if sequence_obj.name != rename_to:
            changed = sequence_obj.rename(rename_to, schema=schema)
            if changed:
                sequence_obj.new_name = rename_to

    # Refresh information
    if state == 'present':
        sequence_obj.get_info()

    # Change owner, schema and settings
    if state == 'present' and sequence_obj.exists:
        # change owner
        if owner:
            if sequence_obj.owner != owner:
                changed = sequence_obj.set_owner(owner, schema=schema)

        # Set schema
        if newschema:
            if sequence_obj.sequence_schema != newschema:
                changed = sequence_obj.set_schema(newschema, schema=schema)
                if changed:
                    sequence_obj.new_schema = newschema

    # Rollback if it's possible and check_mode:
    if not autocommit:
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
        sequence=sequence_obj.name,
        queries=sequence_obj.executed_queries,
        schema=sequence_obj.sequence_schema,
        data_type=sequence_obj.data_type,
        increment=sequence_obj.increment,
        minvalue=sequence_obj.minimum_value,
        maxvalue=sequence_obj.maximum_value,
        start=sequence_obj.start_value,
        cycle=sequence_obj.cycle_option,
        owner=sequence_obj.owner,
    )

    if state == 'present':
        kw['state'] = 'present'

        if sequence_obj.new_name:
            kw['newname'] = sequence_obj.new_name

        if sequence_obj.new_schema:
            kw['newschema'] = sequence_obj.new_schema

    elif state == 'absent':
        kw['state'] = 'absent'

    module.exit_json(**kw)


if __name__ == '__main__':
    main()
