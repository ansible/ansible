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
module: postgresql_ping
short_description: Checks remote PostgreSQL server availability.
description:
   - Simple module to check remote PostgreSQL server availability.
version_added: "2.8"
options:
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
        certificate(s). If the file exists, the server's certificate will be
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
author: "Andrew Klychkov (@Andersson007)"
'''

EXAMPLES = '''
# PostgreSQL ping dbsrv server from the shell:
# ansible dbsrv -m postgresql_ping

- name: PostgreSQL ping dbsrv server using not default credentials and ssl
  postgresql_ping:
    db: protected_db
    login_host: dbsrv
    login_user: secret
    login_password: secret_pass
    ssl_rootcert: /root/root.crt
    ssl_mode: verify-full
'''

RETURN = '''
is_available:
    description: PostgreSQL server availability.
    returned: always
    type: bool
    sample: true

server_version:
    description: PostgreSQL server version.
    returned: always
    type: str
    sample: '11.1'
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


class PgPing(object):
    def __init__(self, module, cursor):
        self.module = module
        self.cursor = cursor
        self.is_available = False
        self.version = ""

    def do(self):
        self.get_pg_version()
        return (self.is_available, self.version)

    def get_pg_version(self):
        query = "SELECT version()"
        raw = self.__exec_sql(query)[0][0]
        if raw:
            self.is_available = True
            self.version = raw.split()[1]

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
        # except psycopg2.ProgrammingError as e:
        #     self.module.fail_json(msg="Cannot execute SQL '%s': %s" % (query, to_native(e)),
        #                           exception=traceback.format_exc())
        except Exception as e:
            self.module.warn("PostgreSQL server is unavailable: %s" % e)

        return False

# ===========================================
# Module execution.
#


def main():
    argument_spec = pgutils.postgres_common_argument_spec()
    argument_spec.update(dict(
        db=dict(default=''),
        ssl_mode=dict(default='prefer', choices=[
            'disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']),
        ssl_rootcert=dict(default=None),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg="The python psycopg2 module is required")

    sslrootcert = module.params["ssl_rootcert"]

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
        module.fail_json(
            msg='psycopg2 must be at least 2.4.3 in order to user the ssl_rootcert parameter')

    # Set some default values:
    cursor = False

    try:
        db_connection = psycopg2.connect(**kw)

        cursor = db_connection.cursor(
            cursor_factory=psycopg2.extras.DictCursor)
    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(
                msg='Postgresql server must be at least version 8.4 to support sslrootcert')
        module.fail_json(msg="unable to connect to database: %s" % to_native(e),
                         exception=traceback.format_exc())
    except Exception as e:
        module.warn("PostgreSQL server is unavailable: %s" % e)
        # module.fail_json(msg="unable to connect to database: %s" % to_native(e),
        #                  exception=traceback.format_exc())

    # Set defaults:
    changed = False

    # Do job:
    pg_ping = PgPing(module, cursor)
    if cursor:
        # If connection established:
        kw["is_available"], kw["server_version"] = pg_ping.do()
    else:
        # Return if PostgreSQL is unavailable:
        kw["is_available"], kw["server_version"] = (False, "")

    # Rollback transaction, if checkmode.
    # Otherwise, commit transaction:
    # (Nothing changes by this module, just for the order)
    if changed:
        if module.check_mode:
            db_connection.rollback()
        else:
            db_connection.commit()

    kw['changed'] = changed
    module.exit_json(**kw)


if __name__ == '__main__':
    main()
