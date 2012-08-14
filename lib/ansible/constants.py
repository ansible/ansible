# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import os
import pwd
import ConfigParser
import traceback

def get_config(p, section, key, env_var, default):
    if p is not None:
        try:
            return p.get(section, key)
        except:
            if env_var is not None:
                return os.environ.get(env_var, default)
            return default
    else:
        if env_var is not None:
            return os.environ.get(env_var, default)
        return default

def load_config_file():
    p = ConfigParser.ConfigParser()
    path1 = os.path.expanduser(
        os.environ.get('ANSIBLE_CONFIG', "~/.ansible.cfg"))
    path2 = "/etc/ansible/ansible.cfg"
    if os.path.exists(path1):
        p.read(path1)
    elif os.path.exists(path2):
        p.read(path2)
    else:
        return None
    return p

def shell_expand_path(path):
    ''' shell_expand_path is needed as os.path.expanduser does not work 
        when path is None, which is the default for ANSIBLE_PRIVATE_KEY_FILE '''
    if path:
        path = os.path.expanduser(path)
    return path

p = load_config_file()

active_user   = pwd.getpwuid(os.geteuid())[0]

# sections in config file
DEFAULTS='defaults'

# configurable things
DEFAULT_HOST_LIST         = shell_expand_path(get_config(p, DEFAULTS, 'hostfile',         'ANSIBLE_HOSTS',            '/etc/ansible/hosts'))
DEFAULT_MODULE_PATH       = shell_expand_path(get_config(p, DEFAULTS, 'library',          'ANSIBLE_LIBRARY',          '/usr/share/ansible'))
DEFAULT_REMOTE_TMP        = shell_expand_path(get_config(p, DEFAULTS, 'remote_tmp',       'ANSIBLE_REMOTE_TEMP',      '$HOME/.ansible/tmp'))
DEFAULT_MODULE_NAME       = get_config(p, DEFAULTS, 'module_name',      None,                       'command')
DEFAULT_PATTERN           = get_config(p, DEFAULTS, 'pattern',          None,                       '*')
DEFAULT_FORKS             = get_config(p, DEFAULTS, 'forks',            'ANSIBLE_FORKS',            5)
DEFAULT_MODULE_ARGS       = get_config(p, DEFAULTS, 'module_args',      'ANSIBLE_MODULE_ARGS',      '')
DEFAULT_TIMEOUT           = get_config(p, DEFAULTS, 'timeout',          'ANSIBLE_TIMEOUT',          10)
DEFAULT_POLL_INTERVAL     = get_config(p, DEFAULTS, 'poll_interval',    'ANSIBLE_POLL_INTERVAL',    15)
DEFAULT_REMOTE_USER       = get_config(p, DEFAULTS, 'remote_user',      'ANSIBLE_REMOTE_USER',      active_user)
DEFAULT_PRIVATE_KEY_FILE  = shell_expand_path(get_config(p, DEFAULTS, 'private_key_file', 'ANSIBLE_PRIVATE_KEY_FILE', None))
DEFAULT_SUDO_USER         = get_config(p, DEFAULTS, 'sudo_user',        'ANSIBLE_SUDO_USER',        'root')
DEFAULT_REMOTE_PORT       = int(get_config(p, DEFAULTS, 'remote_port',      'ANSIBLE_REMOTE_PORT',      22))
DEFAULT_TRANSPORT         = get_config(p, DEFAULTS, 'transport',        'ANSIBLE_TRANSPORT',        'paramiko')

# non-configurable things
DEFAULT_REMOTE_PASS       = None
DEFAULT_TRANSPORT_OPTS    = ['local', 'paramiko', 'ssh']
DEFAULT_SUDO_PASS         = None
DEFAULT_SUBSET            = None

