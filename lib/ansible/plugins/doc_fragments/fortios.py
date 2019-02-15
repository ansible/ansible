# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Benjamin Jolivot <bjolivot@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  file_mode:
    description:
      - Don't connect to any device, only use I(config_file) as input and Output.
    type: bool
    default: no
    version_added: "2.4"
  config_file:
    description:
      - Path to configuration file. Required when I(file_mode) is True.
    type: path
    version_added: "2.4"
  host:
    description:
      - Specifies the DNS hostname or IP address for connecting to the remote fortios device. Required when I(file_mode) is False.
    type: str
  username:
    description:
      - Configures the username used to authenticate to the remote device. Required when I(file_mode) is True.
    type: str
  password:
    description:
      - Specifies the password used to authenticate to the remote device. Required when I(file_mode) is True.
    type: str
  timeout:
    description:
      - Timeout in seconds for connecting to the remote device.
    type: int
    default: 60
  vdom:
    description:
      - Specifies on which vdom to apply configuration
    type: str
  backup:
    description:
      - This argument will cause the module to create a backup of
        the current C(running-config) from the remote device before any
        changes are made.  The backup file is written to the i(backup)
        folder.
    type: bool
    default: no
  backup_path:
    description:
      - Specifies where to store backup files. Required if I(backup=yes).
    type: path
  backup_filename:
    description:
      - Specifies the backup filename. If omitted filename will be
        formatted like HOST_config.YYYY-MM-DD@HH:MM:SS
    type: str
'''
