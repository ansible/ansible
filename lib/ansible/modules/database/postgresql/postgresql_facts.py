#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: postgresql_facts
short_description: Gather facts about remote PostgreSQL servers
description:
   - Gathers facts about remote PostgreSQL servers.
version_added: "2.8"
options:
  incl_filter:
    description:
      - Limit collected facts by comma separated string or list.
      - Allowable values are C(version),
        C(databases), C(settings), C(tablespaces), C(languages), C(roles), C(namespaces),
        C(replications), C(repl_slots), C(extensions).
      - By default, collects all subsets.
      - You can use shell-style (fnmatch) wildcard to pass groups of values (see Examples).
    default: "*"
    type: list
  excl_filter:
    description:
      - Exclude subsets from the collection.
      - Allowable values are similar as in I(incl_filter).
      - You can also use shell-style (fnmatch) wildcard.
      - Mutually exclusive with incl_filter.
    type: list
  db:
    description:
      - Name of database to connect.
    type: str
  port:
    description:
      - Database port to connect.
    type: int
    default: 5432
  login_user:
    description:
      - User (role) used to authenticate with PostgreSQL.
    type: str
    default: postgres
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
    type: str
    default: prefer
    choices: ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
  ssl_rootcert:
    description:
      - Specifies the name of a file containing SSL certificate authority (CA)
        certificate(s).
      - If the file exists, the server's certificate will be
        verified to be signed by one of these authorities.
    type: str
notes:
   - The default authentication assumes that you are either logging in as or
     sudo'ing to the postgres account on the host.
   - This module uses psycopg2, a Python PostgreSQL database adapter. You must
     ensure that psycopg2 is installed on the host before using this module. If
     the remote host is the PostgreSQL server (which is the default case), then
     PostgreSQL must also be installed on the remote host. For Ubuntu-based
     systems, install the postgresql, libpq-dev, and python-psycopg2 packages
     on the remote host before using this module.
requirements: [ psycopg2 ]
author:
- Andrew Klychkov (@Andersson007)
'''

EXAMPLES = '''
# Display facts from postgres hosts.
# ansible postgres -m postgresql_facts

# Display only databases and roles facts from all hosts using shell-style wildcards:
# ansible all -m postgresql_facts -a "incl_filter=dat*,rol*"

# Display only replications and repl_slots facts from standby hosts using shell-style wildcards:
# ansible standby -m postgresql_facts -a "incl_filter=repl*"

# Display all facts from databases hosts except settings:
# ansible databases -m postgresql_facts -a "excl_filter=settings"

- name: Collect PostgreSQL version and extensions
  postgresql_facts:
    incl_filter: ver*, ext*

- name: Collect all subsets, excluding settings and roles
  postgresql_facts:
    excl_filter: settings, roles

- name: Collect tablespaces and repl_slots facts
  postgresql_facts:
    incl_filter:
      - tablespaces
      - repl_s*
'''

RETURN = '''
ansible_facts:
    description: Dictionary containing the detailed information about the PostgreSQL instance.
    returned: always
    type: complex
    contains:
        version:
            description: Database server version U(https://www.postgresql.org/support/versioning/).
            returned: always
            type: dict
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
            contains:
                database_name:
                    description: Database name.
                    returned: always
                    type: dict
                    sample: template0
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
                              - Database owner
                                U(https://www.postgresql.org/docs/current/sql-createdatabase.html).
                            returned: always
                            type: str
                            sample: postgres
                        size:
                            description: Database size.
                            returned: always
                            type: str
                            sample: 7861 kB
        extensions:
            description:
                - Extensions U(https://www.postgresql.org/docs/current/sql-createextension.html).
            returned: always
            type: dict
            sample: plpgsql
            contains:
                description:
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
                    description: Namecpase where the extension is.
                    returned: always
                    type: str
                    sample: pg_catalog
        languages:
            description: Procedural languages U(https://www.postgresql.org/docs/current/xplang.html).
            returned: always
            type: dict
            sample: sql
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
            sample: pg_catalog
            contains:
                nspacl:
                    description:
                      - Assess privileges U(https://www.postgresql.org/docs/current/catalog-pg-namespace.html).
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
                U(https://www.postgresql.org/docs/current/catalog-pg-replication-slots.html).
            returned: if existent
            type: dict
            sample: slot0
            contains:
                active:
                    description: True if this slot is currently actively being used.
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
                      - The base name of the shared object containing the the output plugin
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
            sample: 47823
            contains:
                usename:
                    description: Name of the user logged into this WAL sender process.
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
              - Information about tablespaces
                U(https://www.postgresql.org/docs/current/catalog-pg-tablespace.html).
            returned: always
            type: dict
            sample: test
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
            sample: test_role
            contains:
                canlogin:
                    description: Login privilege U(https://www.postgresql.org/docs/current/role-attributes.html).
                    returned: always
                    type: bool
                    sample: true
                member_of:
                    description: Role membership U(https://www.postgresql.org/docs/current/role-membership.html).
                    returned: always
                    type: list
                    sample: [ "read_only_users" ]
                superuser:
                    description: User is a superuser or not.
                    returned: always
                    type: bool
                    sample: false
                valid_until:
                    description: Password expiration date U(https://www.postgresql.org/docs/current/sql-alterrole.html).
                    returned: always
                    type: str
                    sample: "9999-12-31T23:59:59.999999+00:00"
        settings:
            description:
              - Information about run-time server parameters
                U(https://www.postgresql.org/docs/current/view-pg-settings.html).
            returned: always
            type: dict
            sample: work_mem
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
'''


import traceback
from fnmatch import fnmatch

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    HAS_PSYCOPG2 = False
else:
    HAS_PSYCOPG2 = True

import ansible.module_utils.postgres as pgutils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import SQLParseError
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems


# ===========================================
# PostgreSQL module specific support methods.
#


class PgClusterFacts(object):
    def __init__(self, module, cursor):
        self.module = module
        self.cursor = cursor
        self.pg_facts = {
            "version": {},
            "tablespaces": {},
            "databases": {},
            "languages": {},
            "namespaces": {},
            "replications": {},
            "repl_slots": {},
            "settings": {},
            "roles": {},
            "extensions": {},
        }

    def collect(self, include=False, exclude=False):
        subset_map = {
            "version": self.get_pg_version,
            "tablespaces": self.get_tablespaces,
            "databases": self.get_db_info,
            "languages": self.get_lang_info,
            "namespaces": self.get_namespaces,
            "replications": self.get_repl_info,
            "repl_slots": self.get_rslot_info,
            "settings": self.get_settings,
            "roles": self.get_role_info,
            "extensions": self.get_ext_info,
        }

        if include:
            # Collect info:
            for s in subset_map:
                for i in include:
                    if fnmatch(s, i):
                        subset_map[s]()
                        break

        elif exclude:
            found = False
            # Collect info:
            for s in subset_map:
                for e in exclude:
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

        return self.pg_facts

    def get_tablespaces(self):
        """
        Get information about tablespaces.
        """
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
            ts_info = {}
            ts_info["spcowner"] = i[1]
            ts_info["spcacl"] = i[2] if i[2] else ''
            if opt:
                ts_info["spcoptions"] = i[3] if i[3] else []

            ts_dict[ts_name] = ts_info

        self.pg_facts["tablespaces"] = ts_dict

    def get_ext_info(self):
        """
        Get information about existing extensions.
        """
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

        self.pg_facts["extensions"] = ext_dict

    def get_role_info(self):
        """
        Get information about roles (in PgSQL groups and users are roles).
        """
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

        self.pg_facts["roles"] = rol_dict

    def get_rslot_info(self):
        """
        Get information about replication slots if exist.
        """
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

        self.pg_facts["repl_slots"] = rslot_dict

    def get_settings(self):
        """
        Get server settings.
        """
        query = ("SELECT name, setting, unit, context, vartype, "
                 "boot_val, min_val, max_val, sourcefile "
                 "FROM pg_settings")
        res = self.__exec_sql(query)

        set_dict = {}
        for i in res:
            set_dict[i[0]] = dict(
                setting=i[1],
                unit=i[2] if i[2] else '',
                context=i[3],
                vartype=i[4],
                boot_val=i[5] if i[5] else '',
                min_val=i[6] if i[6] else '',
                max_val=i[7] if i[7] else '',
                sourcefile=i[8] if i[8] else '',
            )

        self.pg_facts["settings"] = set_dict

    def get_repl_info(self):
        """
        Get information about replication if the server is a master.
        """
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

        self.pg_facts["replications"] = repl_dict

    def get_lang_info(self):
        """
        Get information about current supported languages.
        """
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

        self.pg_facts["languages"] = lang_dict

    def get_namespaces(self):
        """
        Get information about namespaces.
        """
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

        self.pg_facts["namespaces"] = nsp_dict

    def get_pg_version(self):
        query = "SELECT version()"
        raw = self.__exec_sql(query)[0][0]
        raw = raw.split()[1].split('.')
        self.pg_facts["version"] = dict(
            major=int(raw[0]),
            miror=int(raw[1]),
        )

    def get_db_info(self):
        # Following query returns:
        # Name, Owner, Encoding, Collate, Ctype, Access Priv, Size
        query = ("SELECT d.datname, "
                 "pg_catalog.pg_get_userbyid(d.datdba), "
                 "pg_catalog.pg_encoding_to_char(d.encoding), "
                 "d.datcollate, "
                 "d.datctype, "
                 "pg_catalog.array_to_string(d.datacl, E'\n'), "
                 "CASE WHEN pg_catalog.has_database_privilege(d.datname, 'CONNECT') "
                 "THEN pg_catalog.pg_size_pretty(pg_catalog.pg_database_size(d.datname)) "
                 "ELSE 'No Access' END, "
                 "t.spcname "
                 "FROM pg_catalog.pg_database AS d "
                 "JOIN pg_catalog.pg_tablespace t on d.dattablespace = t.oid")
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

        self.pg_facts["databases"] = db_dict

    def __exec_sql(self, query):
        try:
            self.cursor.execute(query)
            res = self.cursor.fetchall()
            if res:
                return res
        except SQLParseError as e:
            self.module.fail_json(msg=to_native(e),
                                  exception=traceback.format_exc())
            self.cursor.close()
        except psycopg2.ProgrammingError as e:
            self.module.fail_json(msg="Cannot execute SQL '%s': %s" % (query, to_native(e)),
                                  exception=traceback.format_exc())
            self.cursor.close()
        return False

# ===========================================
# Module execution.
#


def main():
    argument_spec = pgutils.postgres_common_argument_spec()
    argument_spec.update(dict(
        db=dict(type='str'),
        incl_filter=dict(type='str', default="*"),
        excl_filter=dict(type='str'),
        ssl_mode=dict(type='str', default='prefer', choices=[
            'disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']),
        ssl_rootcert=dict(type='str'),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg="The python psycopg2 module is required")

    incl_filters = module.params["incl_filter"]
    excl_filters = module.params["excl_filter"]
    sslrootcert = module.params["ssl_rootcert"]

    if incl_filters != "*" and excl_filters:
        module.fail_json(msg="incl_filter and excl_filter parameters "
                             "are mutually exclusive")

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
        "ssl_rootcert": "sslrootcert"
    }
    kw = dict((params_map[k], v) for (k, v) in iteritems(module.params)
              if k in params_map and v != "" and v is not None)

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] == "" or kw["host"] == "localhost"
    if is_localhost and module.params["login_unix_socket"] != "":
        kw["host"] = module.params["login_unix_socket"]

    if psycopg2.__version__ < '2.4.3' and sslrootcert:
        module.fail_json(msg='psycopg2 must be at least 2.4.3 in order '
                             'to user the ssl_rootcert parameter')

    try:
        db_connection = psycopg2.connect(**kw)
        cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least version 8.4 '
                                 'to support sslrootcert')
        module.fail_json(msg="unable to connect to database: %s" % to_native(e),
                         exception=traceback.format_exc())
    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e),
                         exception=traceback.format_exc())

    # Do job:
    pg_facts = PgClusterFacts(module, cursor)

    if incl_filters != "*":
        incl_filters = [s.strip(" \'][") for s in incl_filters.split(',')]
        kw['ansible_facts'] = pg_facts.collect(include=incl_filters)

    elif excl_filters:
        excl_filters = [s.strip(" \'][") for s in excl_filters.split(',')]
        kw['ansible_facts'] = pg_facts.collect(exclude=excl_filters)

    else:
        kw['ansible_facts'] = pg_facts.collect()

    # Rollback transaction, if checkmode.
    # Otherwise, commit transaction:
    # (It doesn't make sense in this praticular case, just for order)
    if module.check_mode:
        db_connection.rollback()
    else:
        db_connection.commit()

    module.exit_json(**kw)


if __name__ == '__main__':
    main()
