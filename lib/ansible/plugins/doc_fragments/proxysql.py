# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt


class ModuleDocFragment(object):

    # Documentation fragment for ProxySQL connectivity
    CONNECTIVITY = r'''
options:
  login_user:
    description:
      - The username used to authenticate to ProxySQL admin interface.
    type: str
  login_password:
    description:
      - The password used to authenticate to ProxySQL admin interface.
    type: str
  login_host:
    description:
      - The host used to connect to ProxySQL admin interface.
    type: str
    default: '127.0.0.1'
  login_port:
    description:
      - The port used to connect to ProxySQL admin interface.
    type: int
    default: 6032
  config_file:
    description:
      - Specify a config file from which I(login_user) and I(login_password)
        are to be read.
    type: path
    default: ''
requirements:
   - PyMySQL (Python 2.7 and Python 3.X), or
   - MySQLdb (Python 2.x)
'''

    # Documentation fragment for managing ProxySQL configuration
    MANAGING_CONFIG = r'''
options:
  save_to_disk:
    description:
      - Save config to sqlite db on disk to persist the configuration.
    type: bool
    default: 'yes'
  load_to_runtime:
    description:
      - Dynamically load config to runtime memory.
    type: bool
    default: 'yes'
'''
