#
# (c) 2017, Benjamin Jolivot <bjolivot@gmail.com>
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
#


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = """
options:
  file_mode:
    description:
      - Don't connect to any device, only use I(config_file) as input and Output.
    default: false
    type: bool
    version_added: "2.4"
  config_file:
    description:
      - Path to configuration file. Required when I(file_mode) is True.
    version_added: "2.4"
  host:
    description:
      - Specifies the DNS hostname or IP address for connecting to the remote fortios device. Required when I(file_mode) is False.
  username:
    description:
      - Configures the username used to authenticate to the remote device. Required when I(file_mode) is True.
  password:
    description:
      - Specifies the password used to authenticate to the remote device. Required when I(file_mode) is True.
  timeout:
    description:
      - Timeout in seconds for connecting to the remote device.
    default: 60
  vdom:
    description:
      - Specifies on which vdom to apply configuration
  backup:
    description:
      - This argument will cause the module to create a backup of
        the current C(running-config) from the remote device before any
        changes are made.  The backup file is written to the i(backup)
        folder.
    default: no
    type: bool
  backup_path:
    description:
      - Specifies where to store backup files. Required if I(backup=yes).
  backup_filename:
    description:
      - Specifies the backup filename. If omitted filename will be
        formatted like HOST_config.YYYY-MM-DD@HH:MM:SS
"""
