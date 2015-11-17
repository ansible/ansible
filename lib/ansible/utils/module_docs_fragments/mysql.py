# -*- coding: utf-8 -*-
# Copyright (c) 2015 Jonathan Mainguy <jon@soh.re>
#
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

    # Standard mysql documentation fragment
    DOCUMENTATION = '''
options:
  login_user:
    description:
      - The username used to authenticate with
    required: false
    default: null
  login_password:
    description:
      - The password used to authenticate with
    required: false
    default: null
  login_host:
    description:
      - Host running the database
    required: false
    default: localhost
  login_port:
    description:
      - Port of the MySQL server. Requires login_host be defined as other then localhost if login_port is used
    required: false
    default: 3306
  login_unix_socket:
    description:
      - The path to a Unix domain socket for local connections
    required: false
    default: null
  config_file:
    description:
      - Specify a config file from which user and password are to be read
    required: false
    default: '~/.my.cnf'
    version_added: "2.0"
  ssl_ca:
    required: false
    default: null
    version_added: "2.0"
    description:
      - The path to a Certificate Authority (CA) certificate. This option, if used, must specify the same certificate as used by the server.
  ssl_cert:
    required: false
    default: null
    version_added: "2.0"
    description:
      - The path to a client public key certificate.
  ssl_key:
    required: false
    default: null
    version_added: "2.0"
    description:
      - The path to the client private key.
requirements:
   - MySQLdb
notes:
   - Requires the MySQLdb Python package on the remote host. For Ubuntu, this
     is as easy as apt-get install python-mysqldb. (See M(apt).) For CentOS/Fedora, this
     is as easy as yum install MySQL-python. (See M(yum).)
   - Both C(login_password) and C(login_user) are required when you are
     passing credentials. If none are present, the module will attempt to read
     the credentials from C(~/.my.cnf), and finally fall back to using the MySQL
     default login of 'root' with no password.
'''
