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
  incl_subset:
    description:
      - Limit collected subsets by comma separated string.
      - Allowable values are C(version),
        C(databases), C(settings), C(tablespaces), C(languages), C(roles), C(namespaces),
        C(replications), C(repl_slots), C(extensions).
      - By default, collects all subsets.
      - You can use shell-style (fnmatch) wildcard to pass groups of values (see Examples).
    default: "*"
    type: list
  excl_subset:
    description:
      - Exclude subsets from the collection.
      - Allowable values are similar as in I(incl_subset).
      - You can also use shell-style (fnmatch) wildcard.
      - Mutually exclusive with incl_subset.
    type: list
  db:
    description:
      - Name of database to connect.
  port:
    description:
      - Database port to connect.
    default: 5432
  login_user:
    description:
      - User (role) used to authenticate with PostgreSQL.
    default: postgres
  login_password:
    description:
      - Password used to authenticate with PostgreSQL.
  login_host:
    description:
      - Host running PostgreSQL.
  login_unix_socket:
    description:
      - Path to a Unix domain socket for local connections.
  ssl_mode:
    description:
      - Determines whether or with what priority a secure SSL TCP/IP connection
        will be negotiated with the server.
      - See U(https://www.postgresql.org/docs/current/static/libpq-ssl.html) for
        more information on the modes.
      - Default of C(prefer) matches libpq default.
    default: prefer
    choices: ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
  ssl_rootcert:
    description:
      - Specifies the name of a file containing SSL certificate authority (CA)
        certificate(s).
      - If the file exists, the server's certificate will be
        verified to be signed by one of these authorities.
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
# ansible all -m postgresql_facts -a "incl_subset=dat*,rol*"

# Display only replications and repl_slots facts from standby hosts using shell-style wildcards:
# ansible standby -m postgresql_facts -a "incl_subset=repl*"

# Display all facts from databases hosts except settings:
# ansible databases -m postgresql_facts -a "excl_subset=settings"

- name: Collect PostgreSQL version and extensions
  postgresql_facts:
    incl_subset: ver*, ext*

- name: Collect all subsets, excluding settings and roles
  postgresql_facts:
    excl_subset: settings, roles

- name: Collect tablespaces and repl_slots facts
  postgresql_facts:
    incl_subset:
      - tablespaces
      - repl_s*
'''

RETURN = '''
ansible_facts:
    description: Dictionary containing the detailed information about the PostgreSQL instance.
    returned: always
    type: complex
    contains:
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
                    type: str
                    sample: 1.0
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
            "version": "",
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
            if i[2]:
                ts_info["spcacl"] = i[2]
            else:
                ts_info["spcacl"] = ""

            if opt:
                if i[3]:
                    ts_info["spcoptions"] = i[3]
                else:
                    ts_info["spcoptions"] = []

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
            ext_name = i[0]
            ext_info = {}
            ext_info["extversion"] = i[1]
            ext_info["nspname"] = i[2]
            ext_info["description"] = i[3]
            ext_dict[ext_name] = ext_info

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
            rol_name = i[0]
            rol_info = {}
            rol_info["superuser"] = i[1]
            rol_info["canlogin"] = i[2]

            if i[3]:
                rol_info["valid_until"] = i[3]
            else:
                rol_info["valid_until"] = ""

            if i[4]:
                rol_info["member_of"] = i[4]
            else:
                rol_info["member_of"] = []

            rol_dict[rol_name] = rol_info

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
            rslot_name = i[0]
            rslot_info = {}
            rslot_info["plugin"] = i[1]
            rslot_info["slot_type"] = i[2]
            rslot_info["database"] = i[3]
            rslot_info["active"] = i[4]

            rslot_dict[rslot_name] = rslot_info

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
            set_name = i[0]
            set_info = {}
            set_info["setting"] = i[1]

            if i[2]:
                set_info["unit"] = i[2]
            else:
                set_info["unit"] = ""

            set_info["context"] = i[3]
            set_info["vartype"] = i[4]
            if i[5]:
                set_info["boot_val"] = i[5]
            else:
                set_info["boot_val"] = ""

            if i[6]:
                set_info["min_val"] = i[6]
            else:
                set_info["min_val"] = ""

            if i[7]:
                set_info["max_val"] = i[7]
            else:
                set_info["max_val"] = ""

            if i[8]:
                set_info["sourcefile"] = i[8]
            else:
                set_info["sourcefile"] = ""

            set_dict[set_name] = set_info

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
        repl_dict = {}

        # If there is no replication:
        if not res:
            return True

        for i in res:
            repl_pid = i[0]
            repl_info = {}
            repl_info["usename"] = i[1]
            if i[2]:
                repl_info["app_name"] = i[2]
            else:
                repl_info["app_name"] = ""

            repl_info["client_addr"] = i[3]
            if i[4]:
                repl_info["client_hostname"] = i[4]
            else:
                repl_info["client_hostname"] = ""

            repl_info["backend_start"] = i[5]
            repl_info["state"] = i[6]

            repl_dict[repl_pid] = repl_info

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
            lang_name = i[0]
            lang_info = {}
            lang_info["lanowner"] = i[1]
            if i[2]:
                lang_info["lanacl"] = i[2]
            else:
                lang_info["lanacl"] = ""

            lang_dict[lang_name] = lang_info

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
            nsp_name = i[0]
            nsp_info = {}
            nsp_info["nspowner"] = i[1]
            if i[2]:
                nsp_info["nspacl"] = i[2]
            else:
                nsp_info["nspacl"] = ""

            nsp_dict[nsp_name] = nsp_info

        self.pg_facts["namespaces"] = nsp_dict

    def get_pg_version(self):
        query = "SELECT version()"
        raw = self.__exec_sql(query)[0][0]
        self.pg_facts["version"] = raw.split()[1]

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
            db_name = i[0]
            db_info = {}
            db_info['owner'] = i[1]
            db_info['encoding'] = i[2]
            db_info['collate'] = i[3]
            db_info['ctype'] = i[4]
            db_info['size'] = i[6]
            if i[5]:
                db_info['access_priv'] = i[5]
            else:
                db_info['access_priv'] = ''

            db_dict[db_name] = db_info

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
        db=dict(default='', type=str),
        incl_subset=dict(default="*", type=str),
        excl_subset=dict(default="", type=str),
        ssl_mode=dict(default='prefer', choices=[
            'disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']),
        ssl_rootcert=dict(default=None, type=str),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg="The python psycopg2 module is required")

    incl_subsets = module.params["incl_subset"]
    excl_subsets = module.params["excl_subset"]
    sslrootcert = module.params["ssl_rootcert"]

    if incl_subsets != "*" and excl_subsets:
        module.fail_json(msg="incl_subset and excl_subset parameters "
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

    if psycopg2.__version__ < '2.4.3' and sslrootcert is not None:
        module.fail_json(msg='psycopg2 must be at least 2.4.3 in order to user the ssl_rootcert parameter')

    try:
        db_connection = psycopg2.connect(**kw)

        cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least version 8.4 to support sslrootcert')
        module.fail_json(msg="unable to connect to database: %s" % to_native(e),
                         exception=traceback.format_exc())
    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e),
                         exception=traceback.format_exc())

    # Do job:
    pg_facts = PgClusterFacts(module, cursor)

    if incl_subsets != "*":
        incl_subsets = [s.strip(" \'][") for s in incl_subsets.split(',')]
        kw['ansible_facts'] = pg_facts.collect(include=incl_subsets)

    elif excl_subsets:
        excl_subsets = [s.strip(" \'][") for s in excl_subsets.split(',')]
        kw['ansible_facts'] = pg_facts.collect(exclude=excl_subsets)

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
