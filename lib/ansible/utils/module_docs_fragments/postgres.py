# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


class ModuleDocFragment(object):
    # Postgres documentation fragment
    DOCUMENTATION = """
options:
  login_user:
    description:
      - The username used to authenticate with
    default: postgres
  login_password:
    description:
      - The password used to authenticate with
  login_host:
    description:
      - Host running the database
  login_unix_socket:
    description:
      - Path to a Unix domain socket for local connections
  port:
    description:
      - Database port to connect to.
    default: 5432
  ssl_mode:
    description:
      - Determines whether or with what priority a secure SSL TCP/IP connection will be negotiated with the server.
      - See https://www.postgresql.org/docs/current/static/libpq-ssl.html for more information on the modes.
      - Default of C(prefer) matches libpq default.
    default: prefer
    choices: [disable, allow, prefer, require, verify-ca, verify-full]
    version_added: '2.3'
  ssl_rootcert:
    description:
      - Specifies the name of a file containing SSL certificate authority (CA) certificate(s).
      - If the file exists, the server's certificate will be verified to be signed by one of these authorities.
    version_added: '2.3'
notes:
- The default authentication assumes that you are either logging in as or sudo'ing to the C(postgres) account on the host.
- This module uses I(psycopg2), a Python PostgreSQL database adapter. You must ensure that psycopg2 is installed on
  the host before using this module. If the remote host is the PostgreSQL server (which is the default case), then
  PostgreSQL must also be installed on the remote host. For Ubuntu-based systems, install the C(postgresql), C(libpq-dev),
  and C(python-psycopg2) packages on the remote host before using this module.
- The ssl_rootcert parameter requires at least Postgres version 8.4 and I(psycopg2) version 2.4.3.
requirements: [ psycopg2 ]
"""
