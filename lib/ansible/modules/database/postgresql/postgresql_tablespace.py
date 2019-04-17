#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Flavien Chantelot (@Dorn-)
# Copyright: (c) 2018, Antoine Levy-Lambert (@antoinell)
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
module: postgresql_tablespace
short_description: Add or remove PostgreSQL tablespaces from remote hosts
description:
- Adds or removes PostgreSQL tablespaces from remote hosts
  U(https://www.postgresql.org/docs/current/sql-createtablespace.html),
  U(https://www.postgresql.org/docs/current/manage-ag-tablespaces.html).
version_added: '2.8'
options:
  tablespace:
    description:
    - Name of the tablespace to add or remove.
    required: true
    type: str
    aliases:
    - name
  location:
    description:
    - Path to the tablespace directory in the file system.
    - Ensure that the location exists and has right privileges.
    type: path
    aliases:
    - path
  state:
    description:
    - Tablespace state.
    - I(state=present) implies the tablespace must be created if it doesn't exist.
    - I(state=absent) implies the tablespace must be removed if present.
      I(state=absent) is mutually exclusive with I(location), I(owner), i(set).
    - See the Notes section for information about check mode restrictions.
    type: str
    default: present
    choices: [ absent, present ]
  owner:
    description:
    - Name of the role to set as an owner of the tablespace.
    - If this option is not specified, the tablespace owner is a role that creates the tablespace.
    type: str
  set:
    description:
    - Dict of tablespace options to set. Supported from PostgreSQL 9.0.
    - For more information see U(https://www.postgresql.org/docs/current/sql-createtablespace.html).
    - When reset is passed as an option's value, if the option was set previously, it will be removed
      U(https://www.postgresql.org/docs/current/sql-altertablespace.html).
    type: dict
  rename_to:
    description:
    - New name of the tablespace.
    - The new name cannot begin with pg_, as such names are reserved for system tablespaces.
  session_role:
    description:
    - Switch to session_role after connecting. The specified session_role must
      be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though
      the session_role were the one that had logged in originally.
    type: str
  db:
    description:
    - Name of database to connect to and run queries against.
    type: str
    aliases:
    - login_db
notes:
- I(state=absent) and I(state=present) (the second one if the tablespace doesn't exist) do not
  support check mode because the corresponding PostgreSQL DROP and CREATE TABLESPACE commands
  can not be run inside the transaction block.
- The default authentication assumes that you are either logging in as or
  sudo'ing to the postgres account on the host.
- To avoid "Peer authentication failed for user postgres" error,
  use postgres user as a I(become_user).
- This module uses psycopg2, a Python PostgreSQL database adapter. You must
  ensure that psycopg2 is installed on the host before using this module.
- If the remote host is the PostgreSQL server (which is the default case), then
  PostgreSQL must also be installed on the remote host.
- For Ubuntu-based systems, install the postgresql, libpq-dev, and python-psycopg2 packages
  on the remote host before using this module.
requirements: [ psycopg2 ]
author:
- Flavien Chantelot (@Dorn-)
- Antoine Levy-Lambert (@antoinell)
- Andrew Klychkov (@Andersson007)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Create a new tablespace called acme and set bob as an its owner
  postgresql_tablespace:
    name: acme
    owner: bob
    location: /data/foo

- name: Create a new tablespace called bar with tablespace options
  postgresql_tablespace:
    name: bar
    set:
      random_page_cost: 1
      seq_page_cost: 1

- name: Reset random_page_cost option
  postgresql_tablespace:
    name: bar
    set:
      random_page_cost: reset

- name: Rename the tablespace from bar to pcie_ssd
  postgresql_tablespace:
    name: bar
    rename_to: pcie_ssd

- name: Drop tablespace called bloat
  postgresql_tablespace:
    name: bloat
    state: absent
'''

RETURN = r'''
queries:
    description: List of queries that was tried to be executed.
    returned: always
    type: str
    sample: [ "CREATE TABLESPACE bar LOCATION '/incredible/ssd'" ]
tablespace:
    description: Tablespace name.
    returned: always
    type: str
    sample: 'ssd'
owner:
    description: Tablespace owner.
    returned: always
    type: str
    sample: 'Bob'
options:
    description: Tablespace options.
    returned: always
    type: dict
    sample: { 'random_page_cost': 1, 'seq_page_cost': 1 }
location:
    description: Path to the tablespace in the file system.
    returned: always
    type: str
    sample: '/incredible/fast/ssd'
newname:
    description: New tablespace name
    returned: if existent
    type: str
    sample: new_ssd
state:
    description: Tablespace state at the end of execution.
    returned: always
    type: str
    sample: 'present'
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
                db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least '
                                 'version 8.4 to support sslrootcert')

        module.fail_json(msg="unable to connect to database: %s" % to_native(e))

    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e))

    return db_connection


class PgTablespace(object):
    def __init__(self, module, cursor, name):
        self.module = module
        self.cursor = cursor
        self.name = name
        self.exists = False
        self.owner = ''
        self.settings = {}
        self.location = ''
        self.executed_queries = []
        self.new_name = ''
        self.opt_not_supported = False
        # Collect info:
        self.get_info()

    def get_info(self):
        # Check that spcoptions exists:
        opt = self.__exec_sql("SELECT 1 FROM information_schema.columns "
                              "WHERE table_name = 'pg_tablespace' "
                              "AND column_name = 'spcoptions'", add_to_executed=False)

        # For 9.1 version and earlier:
        location = self.__exec_sql("SELECT 1 FROM information_schema.columns "
                                   "WHERE table_name = 'pg_tablespace' "
                                   "AND column_name = 'spclocation'", add_to_executed=False)
        if location:
            location = 'spclocation'
        else:
            location = 'pg_tablespace_location(t.oid)'

        if not opt:
            self.opt_not_supported = True
            query = ("SELECT r.rolname, (SELECT Null), %s "
                     "FROM pg_catalog.pg_tablespace AS t "
                     "JOIN pg_catalog.pg_roles AS r "
                     "ON t.spcowner = r.oid "
                     "WHERE t.spcname = '%s'" % (location, self.name))
        else:
            query = ("SELECT r.rolname, t.spcoptions, %s "
                     "FROM pg_catalog.pg_tablespace AS t "
                     "JOIN pg_catalog.pg_roles AS r "
                     "ON t.spcowner = r.oid "
                     "WHERE t.spcname = '%s'" % (location, self.name))

        res = self.__exec_sql(query, add_to_executed=False)

        if not res:
            self.exists = False
            return False

        if res[0][0]:
            self.exists = True
            self.owner = res[0][0]

            if res[0][1]:
                # Options exist:
                for i in res[0][1]:
                    i = i.split('=')
                    self.settings[i[0]] = i[1]

            if res[0][2]:
                # Location exists:
                self.location = res[0][2]

    def create(self, location):
        query = ("CREATE TABLESPACE %s LOCATION '%s'" % (pg_quote_identifier(self.name, 'database'), location))
        return self.__exec_sql(query, ddl=True)

    def drop(self):
        return self.__exec_sql("DROP TABLESPACE %s" % pg_quote_identifier(self.name, 'database'), ddl=True)

    def set_owner(self, new_owner):
        if new_owner == self.owner:
            return False

        query = "ALTER TABLESPACE %s OWNER TO %s" % (pg_quote_identifier(self.name, 'database'), new_owner)
        return self.__exec_sql(query, ddl=True)

    def rename(self, newname):
        query = "ALTER TABLESPACE %s RENAME TO %s" % (pg_quote_identifier(self.name, 'database'), newname)
        self.new_name = newname
        return self.__exec_sql(query, ddl=True)

    def set_settings(self, new_settings):
        # settings must be a dict {'key': 'value'}
        if self.opt_not_supported:
            return False

        changed = False

        # Apply new settings:
        for i in new_settings:
            if new_settings[i] == 'reset':
                if i in self.settings:
                    changed = self.__reset_setting(i)
                    self.settings[i] = None

            elif (i not in self.settings) or (str(new_settings[i]) != self.settings[i]):
                changed = self.__set_setting("%s = '%s'" % (i, new_settings[i]))

        return changed

    def __reset_setting(self, setting):
        query = "ALTER TABLESPACE %s RESET (%s)" % (pg_quote_identifier(self.name, 'database'), setting)
        return self.__exec_sql(query, ddl=True)

    def __set_setting(self, setting):
        query = "ALTER TABLESPACE %s SET (%s)" % (pg_quote_identifier(self.name, 'database'), setting)
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
        tablespace=dict(type='str', aliases=['name']),
        state=dict(type='str', default="present", choices=["absent", "present"]),
        location=dict(type='path', aliases=['path']),
        owner=dict(type='str'),
        set=dict(type='dict'),
        rename_to=dict(type='str'),
        db=dict(type='str', aliases=['login_db']),
        port=dict(type='int', default=5432, aliases=['login_port']),
        ssl_mode=dict(type='str', default='prefer', choices=['allow', 'disable', 'prefer', 'require', 'verify-ca', 'verify-full']),
        ca_cert=dict(type='str', aliases=['ssl_rootcert']),
        session_role=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=(('positional_args', 'named_args'),),
        supports_check_mode=True,
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg=missing_required_lib('psycopg2'))

    tablespace = module.params["tablespace"]
    state = module.params["state"]
    location = module.params["location"]
    owner = module.params["owner"]
    rename_to = module.params["rename_to"]
    settings = module.params["set"]
    sslrootcert = module.params["ca_cert"]
    session_role = module.params["session_role"]

    if state == 'absent' and (location or owner or rename_to or settings):
        module.fail_json(msg="state=absent is mutually exclusive location, "
                             "owner, rename_to, and set")

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
              if k in params_map and v != '' and v is not None)

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
            module.fail_json(msg="Could not switch role: %s" % to_native(e))

    # Change autocommit to False if check_mode:
    if module.check_mode:
        if psycopg2.__version__ >= '2.4.2':
            db_connection.set_session(autocommit=False)
        else:
            db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)

    # Set defaults:
    autocommit = False
    changed = False

    ##############
    # Create PgTablespace object and do main job:
    tblspace = PgTablespace(module, cursor, tablespace)

    # If tablespace exists with different location, exit:
    if tblspace.exists and location and location != tblspace.location:
        module.fail_json(msg="Tablespace '%s' exists with different location '%s'" % (tblspace.name, tblspace.location))

    # Create new tablespace:
    if not tblspace.exists and state == 'present':
        if rename_to:
            module.fail_json(msg="Tablespace %s does not exist, nothing to rename" % tablespace)

        if not location:
            module.fail_json(msg="'location' parameter must be passed with "
                                 "state=present if the tablespace doesn't exist")

        # Because CREATE TABLESPACE can not be run inside the transaction block:
        autocommit = True
        if psycopg2.__version__ >= '2.4.2':
            db_connection.set_session(autocommit=True)
        else:
            db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        changed = tblspace.create(location)

    # Drop non-existing tablespace:
    elif not tblspace.exists and state == 'absent':
        # Nothing to do:
        module.fail_json(msg="Tries to drop nonexistent tablespace '%s'" % tblspace.name)

    # Drop existing tablespace:
    elif tblspace.exists and state == 'absent':
        # Because DROP TABLESPACE can not be run inside the transaction block:
        autocommit = True
        if psycopg2.__version__ >= '2.4.2':
            db_connection.set_session(autocommit=True)
        else:
            db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        changed = tblspace.drop()

    # Rename tablespace:
    elif tblspace.exists and rename_to:
        if tblspace.name != rename_to:
            changed = tblspace.rename(rename_to)

    if state == 'present':
        # Refresh information:
        tblspace.get_info()

    # Change owner and settings:
    if state == 'present' and tblspace.exists:
        if owner:
            changed = tblspace.set_owner(owner)

        if settings:
            changed = tblspace.set_settings(settings)

        tblspace.get_info()

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
        tablespace=tblspace.name,
        owner=tblspace.owner,
        queries=tblspace.executed_queries,
        options=tblspace.settings,
        location=tblspace.location,
    )

    if state == 'present':
        kw['state'] = 'present'

        if tblspace.new_name:
            kw['newname'] = tblspace.new_name

    elif state == 'absent':
        kw['state'] = 'absent'

    module.exit_json(**kw)


if __name__ == '__main__':
    main()
