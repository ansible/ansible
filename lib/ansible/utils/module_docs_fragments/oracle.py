#
# (c) 2017, Thomas Krahn (@nosmoht)
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
    DOCUMENTATION = '''
options:
  oracle_host:
    description:
    - Hostname or IP address of Oracle DB
    required: False
    default: 127.0.0.1
  oracle_port:
    description:
    - Listener Port
    required: False
    default: 1521
  oracle_user:
    description:
    - Account to connect as
    required: False
    default: SYSTEM
  oracle_pass:
    description:
    - Password to be used to authenticate.
    - Can be omitted if environment variable C(ORACLE_PASS) is set.
    required: False
    default: None
  oracle_mode:
    description:
    - Connection mode.
    - Omit for normal connection.
    required: False
    default: None
    choices: ['SYSDBA', 'SYSOPER']
  oracle_sid:
    description:
    - SID to connect to
    required: False
    default: None
  oracle_service:
    description:
    - Service name to connect to
    required: False
    default: None
requirements:
- cx_Oracle
'''
