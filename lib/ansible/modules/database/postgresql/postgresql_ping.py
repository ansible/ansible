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

DOCUMENTATION = r'''
---
module: postgresql_ping
short_description: Check remote PostgreSQL server availability
description:
- Simple module to check remote PostgreSQL server availability.
version_added: '2.8'
options:
  db:
    description:
    - Name of database to connect.
    type: str
    aliases:
    - login_db
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
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
# PostgreSQL ping dbsrv server from the shell:
# ansible dbsrv -m postgresql_ping

# In the example below you need to generate sertificates previously.
# See https://www.postgresql.org/docs/current/libpq-ssl.html for more information.
- name: PostgreSQL ping dbsrv server using not default credentials and ssl
  postgresql_ping:
    db: protected_db
    login_host: dbsrv
    login_user: secret
    login_password: secret_pass
    ca_cert: /root/root.crt
    ssl_mode: verify-full
'''

RETURN = r'''
is_available:
  description: PostgreSQL server availability.
  returned: always
  type: bool
  sample: true
server_version:
  description: PostgreSQL server version.
  returned: always
  type: dict
  sample: { major: 10, minor: 1 }
'''


try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import SQLParseError
from ansible.module_utils.postgres import postgres_common_argument_spec
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
        self.version = {}

    def do(self):
        self.get_pg_version()
        return (self.is_available, self.version)

    def get_pg_version(self):
        query = "SELECT version()"
        raw = self.__exec_sql(query)[0][0]
        if raw:
            self.is_available = True
            raw = raw.split()[1].split('.')
            self.version = dict(
                major=int(raw[0]),
                minor=int(raw[1]),
            )

    def __exec_sql(self, query):
        try:
            self.cursor.execute(query)
            res = self.cursor.fetchall()
            if res:
                return res
        except SQLParseError as e:
            self.module.fail_json(msg=to_native(e))
            self.cursor.close()
        except Exception as e:
            self.module.warn("PostgreSQL server is unavailable: %s" % to_native(e))

        return False

# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        db=dict(type='str', aliases=['login_db']),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_PSYCOPG2:
        module.fail_json(msg="The python psycopg2 module is required")

    sslrootcert = module.params["ca_cert"]

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

    if psycopg2.__version__ < '2.4.3' and sslrootcert is not None:
        module.fail_json(msg='psycopg2 must be at least 2.4.3 in order '
                             'to user the ca_cert parameter')

    # Set some default values:
    cursor = False
    db_connection = False
    result = dict(
        changed=False,
        is_available=False,
        server_version=dict(),
    )

    try:
        db_connection = psycopg2.connect(**kw)
        cursor = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least '
                                 'version 8.4 to support sslrootcert')
        module.fail_json(msg="unable to connect to database: %s" % to_native(e))
    except Exception as e:
        module.warn("PostgreSQL server is unavailable: %s" % to_native(e))

    # Do job:
    pg_ping = PgPing(module, cursor)
    if cursor:
        # If connection established:
        result["is_available"], result["server_version"] = pg_ping.do()
        db_connection.rollback()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
