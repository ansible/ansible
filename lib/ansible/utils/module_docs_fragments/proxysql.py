# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt


class ModuleDocFragment(object):

    # Documentation fragment for ProxySQL connectivity
    CONNECTIVITY = '''
options:
  login_user:
    description:
      - The username used to authenticate to ProxySQL admin interface.
  login_password:
    description:
      - The password used to authenticate to ProxySQL admin interface.
  login_host:
    description:
      - The host used to connect to ProxySQL admin interface.
    default: '127.0.0.1'
  login_port:
    description:
      - The port used to connect to ProxySQL admin interface.
    default: 6032
  config_file:
    description:
      - Specify a config file from which I(login_user) and I(login_password)
        are to be read.
    default: ''
requirements:
   - MySQLdb
'''

    # Documentation fragment for managing ProxySQL configuration
    MANAGING_CONFIG = '''
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
