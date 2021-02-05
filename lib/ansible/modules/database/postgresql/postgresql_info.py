#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
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
module: postgresql_info
short_description: Gather information about PostgreSQL servers
description:
- Gathers information about PostgreSQL servers.
version_added: '2.8'
options:
  filter:
    description:
    - Limit the collected information by comma separated string or YAML list.
    - Allowable values are C(version),
      C(databases), C(settings), C(tablespaces), C(roles),
      C(replications), C(repl_slots).
    - By default, collects all subsets.
    - You can use shell-style (fnmatch) wildcard to pass groups of values (see Examples).
    - You can use '!' before value (for example, C(!settings)) to exclude it from the information.
    - If you pass including and excluding values to the filter, for example, I(filter=!settings,ver),
      the excluding values will be ignored.
    type: list
    elements: str
  db:
    description:
    - Name of database to connect.
    type: str
    aliases:
    - login_db
  session_role:
    description:
    - Switch to session_role after connecting. The specified session_role must
      be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though
      the session_role were the one that had logged in originally.
    type: str
seealso:
- module: postgresql_ping
author:
- Andrew Klychkov (@Andersson007)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
# Display info from postgres hosts.
# ansible postgres -m postgresql_info

# Display only databases and roles info from all hosts using shell-style wildcards:
# ansible all -m postgresql_info -a 'filter=dat*,rol*'

# Display only replications and repl_slots info from standby hosts using shell-style wildcards:
# ansible standby -m postgresql_info -a 'filter=repl*'

# Display all info from databases hosts except settings:
# ansible databases -m postgresql_info -a 'filter=!settings'

- name: Collect PostgreSQL version and extensions
  become: yes
  become_user: postgres
  postgresql_info:
    filter: ver*,ext*

- name: Collect all info except settings and roles
  become: yes
  become_user: postgres
  postgresql_info:
    filter: "!settings,!roles"

# On FreeBSD with PostgreSQL 9.5 version and lower use pgsql user to become
# and pass "postgres" as a database to connect to
- name: Collect tablespaces and repl_slots info
  become: yes
  become_user: pgsql
  postgresql_info:
    db: postgres
    filter:
    - tablesp*
    - repl_sl*

- name: Collect all info except databases
  become: yes
  become_user: postgres
  postgresql_info:
    filter:
    - "!databases"
'''

RETURN = r'''
version:
  description: Database server version U(https://www.postgresql.org/support/versioning/).
  returned: always
  type: dict
  sample: { "version": { "major": 10, "minor": 6 } }
  contains:
    major:
      description: Major server version.
      returned: always
      type: int
      sample: 11
    minor:
      description: Minor server version.
      returned: always
      type: int
      sample: 1
databases:
  description: Information about databases.
  returned: always
  type: dict
  sample:
  - { "postgres": { "access_priv": "", "collate": "en_US.UTF-8",
  "ctype": "en_US.UTF-8", "encoding": "UTF8", "owner": "postgres", "size": "7997 kB" } }
  contains:
    database_name:
      description: Database name.
      returned: always
      type: dict
      sample: template1
      contains:
        access_priv:
          description: Database access privileges.
          returned: always
          type: str
          sample: "=c/postgres_npostgres=CTc/postgres"
        collate:
          description:
          - Database collation U(https://www.postgresql.org/docs/current/collation.html).
          returned: always
          type: str
          sample: en_US.UTF-8
        ctype:
          description:
          - Database LC_CTYPE U(https://www.postgresql.org/docs/current/multibyte.html).
          returned: always
          type: str
          sample: en_US.UTF-8
        encoding:
          description:
          - Database encoding U(https://www.postgresql.org/docs/current/multibyte.html).
          returned: always
          type: str
          sample: UTF8
        owner:
          description:
          - Database owner U(https://www.postgresql.org/docs/current/sql-createdatabase.html).
          returned: always
          type: str
          sample: postgres
        size:
          description: Database size in bytes.
          returned: always
          type: str
          sample: 8189415
        extensions:
          description:
          - Extensions U(https://www.postgresql.org/docs/current/sql-createextension.html).
          returned: always
          type: dict
          sample:
          - { "plpgsql": { "description": "PL/pgSQL procedural language",
            "extversion": { "major": 1, "minor": 0 } } }
          contains:
            extdescription:
              description: Extension description.
              returned: if existent
              type: str
              sample: PL/pgSQL procedural language
            extversion:
              description: Extension description.
              returned: always
              type: dict
              contains:
                major:
                  description: Extension major version.
                  returned: always
                  type: int
                  sample: 1
                minor:
                  description: Extension minor version.
                  returned: always
                  type: int
                  sample: 0
            nspname:
              description: Namespace where the extension is.
              returned: always
              type: str
              sample: pg_catalog
        languages:
          description: Procedural languages U(https://www.postgresql.org/docs/current/xplang.html).
          returned: always
          type: dict
          sample: { "sql": { "lanacl": "", "lanowner": "postgres" } }
          contains:
            lanacl:
              description:
              - Language access privileges
                U(https://www.postgresql.org/docs/current/catalog-pg-language.html).
              returned: always
              type: str
              sample: "{postgres=UC/postgres,=U/postgres}"
            lanowner:
              description:
              - Language owner U(https://www.postgresql.org/docs/current/catalog-pg-language.html).
              returned: always
              type: str
              sample: postgres
        namespaces:
          description:
          - Namespaces (schema) U(https://www.postgresql.org/docs/current/sql-createschema.html).
          returned: always
          type: dict
          sample: { "pg_catalog": { "nspacl": "{postgres=UC/postgres,=U/postgres}", "nspowner": "postgres" } }
          contains:
            nspacl:
              description:
              - Access privileges U(https://www.postgresql.org/docs/current/catalog-pg-namespace.html).
              returned: always
              type: str
              sample: "{postgres=UC/postgres,=U/postgres}"
            nspowner:
              description:
              - Schema owner U(https://www.postgresql.org/docs/current/catalog-pg-namespace.html).
              returned: always
              type: str
              sample: postgres
repl_slots:
  description:
  - Replication slots (available in 9.4 and later)
    U(https://www.postgresql.org/docs/current/view-pg-replication-slots.html).
  returned: if existent
  type: dict
  sample: { "slot0": { "active": false, "database": null, "plugin": null, "slot_type": "physical" } }
  contains:
    active:
      description:
      - True means that a receiver has connected to it, and it is currently reserving archives.
      returned: always
      type: bool
      sample: true
    database:
      description: Database name this slot is associated with, or null.
      returned: always
      type: str
      sample: acme
    plugin:
      description:
      - Base name of the shared object containing the output plugin
        this logical slot is using, or null for physical slots.
      returned: always
      type: str
      sample: pgoutput
    slot_type:
      description: The slot type - physical or logical.
      returned: always
      type: str
      sample: logical
replications:
  description:
  - Information about the current replications by process PIDs
    U(https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-STATS-VIEWS-TABLE).
  returned: if pg_stat_replication view existent
  type: dict
  sample:
  - { 76580: { "app_name": "standby1", "backend_start": "2019-02-03 00:14:33.908593+03",
    "client_addr": "10.10.10.2", "client_hostname": "", "state": "streaming", "usename": "postgres" } }
  contains:
    usename:
      description:
      - Name of the user logged into this WAL sender process ('usename' is a column name in pg_stat_replication view).
      returned: always
      type: str
      sample: replication_user
    app_name:
      description: Name of the application that is connected to this WAL sender.
      returned: if existent
      type: str
      sample: acme_srv
    client_addr:
      description:
      - IP address of the client connected to this WAL sender.
      - If this field is null, it indicates that the client is connected
        via a Unix socket on the server machine.
      returned: always
      type: str
      sample: 10.0.0.101
    client_hostname:
      description:
      - Host name of the connected client, as reported by a reverse DNS lookup of client_addr.
      - This field will only be non-null for IP connections, and only when log_hostname is enabled.
      returned: always
      type: str
      sample: dbsrv1
    backend_start:
      description: Time when this process was started, i.e., when the client connected to this WAL sender.
      returned: always
      type: str
      sample: "2019-02-03 00:14:33.908593+03"
    state:
      description: Current WAL sender state.
      returned: always
      type: str
      sample: streaming
tablespaces:
  description:
  - Information about tablespaces U(https://www.postgresql.org/docs/current/catalog-pg-tablespace.html).
  returned: always
  type: dict
  sample:
  - { "test": { "spcacl": "{postgres=C/postgres,andreyk=C/postgres}", "spcoptions": [ "seq_page_cost=1" ],
    "spcowner": "postgres" } }
  contains:
    spcacl:
      description: Tablespace access privileges.
      returned: always
      type: str
      sample: "{postgres=C/postgres,andreyk=C/postgres}"
    spcoptions:
      description: Tablespace-level options.
      returned: always
      type: list
      sample: [ "seq_page_cost=1" ]
    spcowner:
      description: Owner of the tablespace.
      returned: always
      type: str
      sample: test_user
roles:
  description:
  - Information about roles U(https://www.postgresql.org/docs/current/user-manag.html).
  returned: always
  type: dict
  sample:
  - { "test_role": { "canlogin": true, "member_of": [ "user_ro" ], "superuser": false,
    "valid_until": "9999-12-31T23:59:59.999999+00:00" } }
  contains:
    canlogin:
      description: Login privilege U(https://www.postgresql.org/docs/current/role-attributes.html).
      returned: always
      type: bool
      sample: true
    member_of:
      description:
      - Role membership U(https://www.postgresql.org/docs/current/role-membership.html).
      returned: always
      type: list
      sample: [ "read_only_users" ]
    superuser:
      description: User is a superuser or not.
      returned: always
      type: bool
      sample: false
    valid_until:
      description:
      - Password expiration date U(https://www.postgresql.org/docs/current/sql-alterrole.html).
      returned: always
      type: str
      sample: "9999-12-31T23:59:59.999999+00:00"
pending_restart_settings:
  description:
  - List of settings that are pending restart to be set.
  returned: always
  type: list
  sample: [ "shared_buffers" ]
settings:
  description:
  - Information about run-time server parameters
    U(https://www.postgresql.org/docs/current/view-pg-settings.html).
  returned: always
  type: dict
  sample:
  - { "work_mem": { "boot_val": "4096", "context": "user", "max_val": "2147483647",
    "min_val": "64", "setting": "8192", "sourcefile": "/var/lib/pgsql/10/data/postgresql.auto.conf",
    "unit": "kB", "vartype": "integer", "val_in_bytes": 4194304 } }
  contains:
    setting:
      description: Current value of the parameter.
      returned: always
      type: str
      sample: 49152
    unit:
      description: Implicit unit of the parameter.
      returned: always
      type: str
      sample: kB
    boot_val:
      description:
      - Parameter value assumed at server startup if the parameter is not otherwise set.
      returned: always
      type: str
      sample: 4096
    min_val:
      description:
      - Minimum allowed value of the parameter (null for non-numeric values).
      returned: always
      type: str
      sample: 64
    max_val:
      description:
      - Maximum allowed value of the parameter (null for non-numeric values).
      returned: always
      type: str
      sample: 2147483647
    sourcefile:
      description:
      - Configuration file the current value was set in.
      - Null for values set from sources other than configuration files,
        or when examined by a user who is neither a superuser or a member of pg_read_all_settings.
      - Helpful when using include directives in configuration files.
      returned: always
      type: str
      sample: /var/lib/pgsql/10/data/postgresql.auto.conf
    context:
      description:
      - Context required to set the parameter's value.
      - For more information see U(https://www.postgresql.org/docs/current/view-pg-settings.html).
      returned: always
      type: str
      sample: user
    vartype:
      description:
      - Parameter type (bool, enum, integer, real, or string).
      returned: always
      type: str
      sample: integer
    val_in_bytes:
      description:
      - Current value of the parameter in bytes.
      returned: if supported
      type: int
      sample: 2147483647
    pretty_val:
      description:
      - Value presented in the pretty form.
      returned: always
      type: str
      sample: 2MB
    pending_restart:
      description:
      - True if the value has been changed in the configuration file but needs a restart; or false otherwise.
      - Returns only if C(settings) is passed.
      returned: always
      type: bool
      sample: false
'''

from fnmatch import fnmatch

try:
    from psycopg2.extras import DictCursor
except ImportError:
    # psycopg2 is checked by connect_to_db()
    # from ansible.module_utils.postgres
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.postgres import (
    connect_to_db,
    get_conn_params,
    postgres_common_argument_spec,
)
from ansible.module_utils._text import to_native


# ===========================================
# PostgreSQL module specific support methods.
#

class PgDbConn(object):

    """Auxiliary class for working with PostgreSQL connection objects.

    Arguments:
        module (AnsibleModule): Object of AnsibleModule class that
            contains connection parameters.
    """

    def __init__(self, module):
        self.module = module
        self.db_conn = None
        self.cursor = None

    def connect(self):
        """Connect to a PostgreSQL database and return a cursor object.

        Note: connection parameters are passed by self.module object.
        """
        conn_params = get_conn_params(self.module, self.module.params, warn_db_default=False)
        self.db_conn = connect_to_db(self.module, conn_params)
        return self.db_conn.cursor(cursor_factory=DictCursor)

    def reconnect(self, dbname):
        """Reconnect to another database and return a PostgreSQL cursor object.

        Arguments:
            dbname (string): Database name to connect to.
        """
        self.db_conn.close()

        self.module.params['database'] = dbname
        return self.connect()


class PgClusterInfo(object):

    """Class for collection information about a PostgreSQL instance.

    Arguments:
        module (AnsibleModule): Object of AnsibleModule class.
        db_conn_obj (psycopg2.connect): PostgreSQL connection object.
    """

    def __init__(self, module, db_conn_obj):
        self.module = module
        self.db_obj = db_conn_obj
        self.cursor = db_conn_obj.connect()
        self.pg_info = {
            "version": {},
            "tablespaces": {},
            "databases": {},
            "replications": {},
            "repl_slots": {},
            "settings": {},
            "roles": {},
            "pending_restart_settings": [],
        }

    def collect(self, val_list=False):
        """Collect information based on 'filter' option."""
        subset_map = {
            "version": self.get_pg_version,
            "tablespaces": self.get_tablespaces,
            "databases": self.get_db_info,
            "replications": self.get_repl_info,
            "repl_slots": self.get_rslot_info,
            "settings": self.get_settings,
            "roles": self.get_role_info,
        }

        incl_list = []
        excl_list = []
        # Notice: incl_list and excl_list
        # don't make sense together, therefore,
        # if incl_list is not empty, we collect
        # only values from it:
        if val_list:
            for i in val_list:
                if i[0] != '!':
                    incl_list.append(i)
                else:
                    excl_list.append(i.lstrip('!'))

            if incl_list:
                for s in subset_map:
                    for i in incl_list:
                        if fnmatch(s, i):
                            subset_map[s]()
                            break
            elif excl_list:
                found = False
                # Collect info:
                for s in subset_map:
                    for e in excl_list:
                        if fnmatch(s, e):
                            found = True

                    if not found:
                        subset_map[s]()
                    else:
                        found = False

        # Default behaviour, if include or exclude is not passed:
        else:
            # Just collect info for each item:
            for s in subset_map:
                subset_map[s]()

        return self.pg_info

    def get_tablespaces(self):
        """Get information about tablespaces."""
        # Check spcoption exists:
        opt = self.__exec_sql("SELECT column_name "
                              "FROM information_schema.columns "
                              "WHERE table_name = 'pg_tablespace' "
                              "AND column_name = 'spcoptions'")

        if not opt:
            query = ("SELECT s.spcname, a.rolname, s.spcacl "
                     "FROM pg_tablespace AS s "
                     "JOIN pg_authid AS a ON s.spcowner = a.oid")
        else:
            query = ("SELECT s.spcname, a.rolname, s.spcacl, s.spcoptions "
                     "FROM pg_tablespace AS s "
                     "JOIN pg_authid AS a ON s.spcowner = a.oid")

        res = self.__exec_sql(query)
        ts_dict = {}
        for i in res:
            ts_name = i[0]
            ts_info = dict(
                spcowner=i[1],
                spcacl=i[2] if i[2] else '',
            )
            if opt:
                ts_info['spcoptions'] = i[3] if i[3] else []

            ts_dict[ts_name] = ts_info

        self.pg_info["tablespaces"] = ts_dict

    def get_ext_info(self):
        """Get information about existing extensions."""
        # Check that pg_extension exists:
        res = self.__exec_sql("SELECT EXISTS (SELECT 1 FROM "
                              "information_schema.tables "
                              "WHERE table_name = 'pg_extension')")
        if not res[0][0]:
            return True

        query = ("SELECT e.extname, e.extversion, n.nspname, c.description "
                 "FROM pg_catalog.pg_extension AS e "
                 "LEFT JOIN pg_catalog.pg_namespace AS n "
                 "ON n.oid = e.extnamespace "
                 "LEFT JOIN pg_catalog.pg_description AS c "
                 "ON c.objoid = e.oid "
                 "AND c.classoid = 'pg_catalog.pg_extension'::pg_catalog.regclass")
        res = self.__exec_sql(query)
        ext_dict = {}
        for i in res:
            ext_ver = i[1].split('.')

            ext_dict[i[0]] = dict(
                extversion=dict(
                    major=int(ext_ver[0]),
                    minor=int(ext_ver[1]),
                ),
                nspname=i[2],
                description=i[3],
            )

        return ext_dict

    def get_role_info(self):
        """Get information about roles (in PgSQL groups and users are roles)."""
        query = ("SELECT r.rolname, r.rolsuper, r.rolcanlogin, "
                 "r.rolvaliduntil, "
                 "ARRAY(SELECT b.rolname "
                 "FROM pg_catalog.pg_auth_members AS m "
                 "JOIN pg_catalog.pg_roles AS b ON (m.roleid = b.oid) "
                 "WHERE m.member = r.oid) AS memberof "
                 "FROM pg_catalog.pg_roles AS r "
                 "WHERE r.rolname !~ '^pg_'")

        res = self.__exec_sql(query)
        rol_dict = {}
        for i in res:
            rol_dict[i[0]] = dict(
                superuser=i[1],
                canlogin=i[2],
                valid_until=i[3] if i[3] else '',
                member_of=i[4] if i[4] else [],
            )

        self.pg_info["roles"] = rol_dict

    def get_rslot_info(self):
        """Get information about replication slots if exist."""
        # Check that pg_replication_slots exists:
        res = self.__exec_sql("SELECT EXISTS (SELECT 1 FROM "
                              "information_schema.tables "
                              "WHERE table_name = 'pg_replication_slots')")
        if not res[0][0]:
            return True

        query = ("SELECT slot_name, plugin, slot_type, database, "
                 "active FROM pg_replication_slots")
        res = self.__exec_sql(query)

        # If there is no replication:
        if not res:
            return True

        rslot_dict = {}
        for i in res:
            rslot_dict[i[0]] = dict(
                plugin=i[1],
                slot_type=i[2],
                database=i[3],
                active=i[4],
            )

        self.pg_info["repl_slots"] = rslot_dict

    def get_settings(self):
        """Get server settings."""
        # Check pending restart column exists:
        pend_rest_col_exists = self.__exec_sql("SELECT 1 FROM information_schema.columns "
                                               "WHERE table_name = 'pg_settings' "
                                               "AND column_name = 'pending_restart'")
        if not pend_rest_col_exists:
            query = ("SELECT name, setting, unit, context, vartype, "
                     "boot_val, min_val, max_val, sourcefile "
                     "FROM pg_settings")
        else:
            query = ("SELECT name, setting, unit, context, vartype, "
                     "boot_val, min_val, max_val, sourcefile, pending_restart "
                     "FROM pg_settings")

        res = self.__exec_sql(query)

        set_dict = {}
        for i in res:
            val_in_bytes = None
            setting = i[1]
            if i[2]:
                unit = i[2]
            else:
                unit = ''

            if unit == 'kB':
                val_in_bytes = int(setting) * 1024

            elif unit == '8kB':
                val_in_bytes = int(setting) * 1024 * 8

            elif unit == 'MB':
                val_in_bytes = int(setting) * 1024 * 1024

            if val_in_bytes is not None and val_in_bytes < 0:
                val_in_bytes = 0

            setting_name = i[0]
            pretty_val = self.__get_pretty_val(setting_name)

            pending_restart = None
            if pend_rest_col_exists:
                pending_restart = i[9]

            set_dict[setting_name] = dict(
                setting=setting,
                unit=unit,
                context=i[3],
                vartype=i[4],
                boot_val=i[5] if i[5] else '',
                min_val=i[6] if i[6] else '',
                max_val=i[7] if i[7] else '',
                sourcefile=i[8] if i[8] else '',
                pretty_val=pretty_val,
            )
            if val_in_bytes is not None:
                set_dict[setting_name]['val_in_bytes'] = val_in_bytes

            if pending_restart is not None:
                set_dict[setting_name]['pending_restart'] = pending_restart
                if pending_restart:
                    self.pg_info["pending_restart_settings"].append(setting_name)

        self.pg_info["settings"] = set_dict

    def get_repl_info(self):
        """Get information about replication if the server is a master."""
        # Check that pg_replication_slots exists:
        res = self.__exec_sql("SELECT EXISTS (SELECT 1 FROM "
                              "information_schema.tables "
                              "WHERE table_name = 'pg_stat_replication')")
        if not res[0][0]:
            return True

        query = ("SELECT r.pid, a.rolname, r.application_name, r.client_addr, "
                 "r.client_hostname, r.backend_start::text, r.state "
                 "FROM pg_stat_replication AS r "
                 "JOIN pg_authid AS a ON r.usesysid = a.oid")
        res = self.__exec_sql(query)

        # If there is no replication:
        if not res:
            return True

        repl_dict = {}
        for i in res:
            repl_dict[i[0]] = dict(
                usename=i[1],
                app_name=i[2] if i[2] else '',
                client_addr=i[3],
                client_hostname=i[4] if i[4] else '',
                backend_start=i[5],
                state=i[6],
            )

        self.pg_info["replications"] = repl_dict

    def get_lang_info(self):
        """Get information about current supported languages."""
        query = ("SELECT l.lanname, a.rolname, l.lanacl "
                 "FROM pg_language AS l "
                 "JOIN pg_authid AS a ON l.lanowner = a.oid")
        res = self.__exec_sql(query)
        lang_dict = {}
        for i in res:
            lang_dict[i[0]] = dict(
                lanowner=i[1],
                lanacl=i[2] if i[2] else '',
            )

        return lang_dict

    def get_namespaces(self):
        """Get information about namespaces."""
        query = ("SELECT n.nspname, a.rolname, n.nspacl "
                 "FROM pg_catalog.pg_namespace AS n "
                 "JOIN pg_authid AS a ON a.oid = n.nspowner")
        res = self.__exec_sql(query)

        nsp_dict = {}
        for i in res:
            nsp_dict[i[0]] = dict(
                nspowner=i[1],
                nspacl=i[2] if i[2] else '',
            )

        return nsp_dict

    def get_pg_version(self):
        """Get major and minor PostgreSQL server version."""
        query = "SELECT version()"
        raw = self.__exec_sql(query)[0][0]
        raw = raw.split()[1].split('.')
        self.pg_info["version"] = dict(
            major=int(raw[0]),
            minor=int(raw[1].rstrip(',')),
        )

    def get_db_info(self):
        """Get information about the current database."""
        # Following query returns:
        # Name, Owner, Encoding, Collate, Ctype, Access Priv, Size
        query = ("SELECT d.datname, "
                 "pg_catalog.pg_get_userbyid(d.datdba), "
                 "pg_catalog.pg_encoding_to_char(d.encoding), "
                 "d.datcollate, "
                 "d.datctype, "
                 "pg_catalog.array_to_string(d.datacl, E'\n'), "
                 "CASE WHEN pg_catalog.has_database_privilege(d.datname, 'CONNECT') "
                 "THEN pg_catalog.pg_database_size(d.datname)::text "
                 "ELSE 'No Access' END, "
                 "t.spcname "
                 "FROM pg_catalog.pg_database AS d "
                 "JOIN pg_catalog.pg_tablespace t ON d.dattablespace = t.oid "
                 "WHERE d.datname != 'template0'")

        res = self.__exec_sql(query)

        db_dict = {}
        for i in res:
            db_dict[i[0]] = dict(
                owner=i[1],
                encoding=i[2],
                collate=i[3],
                ctype=i[4],
                access_priv=i[5] if i[5] else '',
                size=i[6],
            )

        for datname in db_dict:
            self.cursor = self.db_obj.reconnect(datname)
            db_dict[datname]['namespaces'] = self.get_namespaces()
            db_dict[datname]['extensions'] = self.get_ext_info()
            db_dict[datname]['languages'] = self.get_lang_info()

        self.pg_info["databases"] = db_dict

    def __get_pretty_val(self, setting):
        """Get setting's value represented by SHOW command."""
        return self.__exec_sql("SHOW %s" % setting)[0][0]

    def __exec_sql(self, query):
        """Execute SQL and return the result."""
        try:
            self.cursor.execute(query)
            res = self.cursor.fetchall()
            if res:
                return res
        except Exception as e:
            self.module.fail_json(msg="Cannot execute SQL '%s': %s" % (query, to_native(e)))
            self.cursor.close()
        return False

# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        db=dict(type='str', aliases=['login_db']),
        filter=dict(type='list'),
        session_role=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    filter_ = module.params["filter"]

    db_conn_obj = PgDbConn(module)

    # Do job:
    pg_info = PgClusterInfo(module, db_conn_obj)

    module.exit_json(**pg_info.collect(filter_))


if __name__ == '__main__':
    main()
