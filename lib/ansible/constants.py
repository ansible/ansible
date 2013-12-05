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
import sys
import ConfigParser
from string import ascii_letters, digits

# copied from utils, avoid circular reference fun :)
def mk_boolean(value):
    if value is None:
        return False
    val = str(value)
    if val.lower() in [ "true", "t", "y", "1", "yes" ]:
        return True
    else:
        return False

def get_config(p, section, key, env_var, default, boolean=False, integer=False, floating=False):
    ''' return a configuration variable with casting '''
    value = _get_config(p, section, key, env_var, default)
    if boolean:
        return mk_boolean(value)
    if integer:
        return int(value)
    if floating:
        return float(value)
    return value

def _get_config(p, section, key, env_var, default, boolean=True):
    ''' helper function for get_config '''
    if env_var is not None:
        value = os.environ.get(env_var, None)
        if value is not None:
            return value
    if p is not None:
        try:
            return p.get(section, key, raw=True)
        except:
            return default
    return default

def load_config_file(path=None):
    p = ConfigParser.ConfigParser()
    paths = []
    if path == None:
        paths.append(os.getcwd() + "/ansible.cfg")
    else:
        paths.append(path + "/ansible.cfg")
    paths.append(os.path.expanduser(os.environ.get('ANSIBLE_CONFIG', "~/.ansible.cfg")))
    paths.append("/etc/ansible/ansible.cfg")

    for entry in paths:
        if os.path.exists(entry):
            p.read(entry)
            return p
    else:
        return None

def shell_expand_path(path):
    ''' shell_expand_path is needed as os.path.expanduser does not work
        when path is None, which is the default for ANSIBLE_PRIVATE_KEY_FILE '''
    if path:
        path = os.path.expanduser(path)
    return path

def reload_config(path=None):
    global p
    p = load_config_file(path)
    load_constants(_TABLE)

p = None

active_user   = pwd.getpwuid(os.geteuid())[0]

# Needed so the RPM can call setup.py and have modules land in the
# correct location. See #1277 for discussion
if getattr(sys, "real_prefix", None):
    # in a virtualenv
    DIST_MODULE_PATH = os.path.join(sys.prefix, 'share/ansible/')
else:
    DIST_MODULE_PATH = '/usr/share/ansible/'

# check all of these extensions when looking for yaml files for things like
# group variables
YAML_FILENAME_EXTENSIONS = [ "", ".yml", ".yaml" ]

# sections in config file
DEFAULTS='defaults'

# configurable things
_TABLE = '''
# constant_name              key               env_var                    default         flags

DEFAULT_HOST_LIST         hostfile          ANSIBLE_HOSTS             /etc/ansible/hosts  X
DEFAULT_REMOTE_TMP        remote_tmp        ANSIBLE_REMOTE_TEMP       $HOME/.ansible/tmp  X
DEFAULT_PRIVATE_KEY_FILE  private_key_file  ANSIBLE_PRIVATE_KEY_FILE  None                X
DEFAULT_LOG_PATH          log_path          ANSIBLE_LOG_PATH          ''                  X

# path to standard system location for shared files
DEFAULT_MODULE_PATH       library           ANSIBLE_LIBRARY           DIST_MODULE_PATH    G
DEFAULT_ROLES_PATH        roles_path        ANSIBLE_ROLES_PATH        None

# default hosts pattern
DEFAULT_PATTERN           pattern           None                      *

DEFAULT_MODULE_NAME       module_name       None                      command
DEFAULT_MODULE_ARGS       module_args       ANSIBLE_MODULE_ARGS
DEFAULT_MODULE_LANG       module_lang       ANSIBLE_MODULE_LANG       C

DEFAULT_FORKS             forks             ANSIBLE_FORKS             5                   I
DEFAULT_TIMEOUT           timeout           ANSIBLE_TIMEOUT           10                  I
DEFAULT_POLL_INTERVAL     poll_interval     ANSIBLE_POLL_INTERVAL     15                  I

# connection related
DEFAULT_REMOTE_USER       remote_user       ANSIBLE_REMOTE_USER       active_user         G
DEFAULT_SUDO_USER         sudo_user         ANSIBLE_SUDO_USER         root
DEFAULT_ASK_PASS          ask_pass          ANSIBLE_ASK_PASS          False               B
DEFAULT_ASK_SUDO_PASS     ask_sudo_pass     ANSIBLE_ASK_SUDO_PASS     False               B
DEFAULT_SUDO              sudo              ANSIBLE_SUDO              False               B
DEFAULT_SUDO_EXE          sudo_exe          ANSIBLE_SUDO_EXE          sudo
DEFAULT_SUDO_FLAGS        sudo_flags        ANSIBLE_SUDO_FLAGS        -H

DEFAULT_TRANSPORT         transport         ANSIBLE_TRANSPORT         smart
DEFAULT_REMOTE_PORT       remote_port       ANSIBLE_REMOTE_PORT       22                  I


DEFAULT_ACTION_PLUGIN_PATH      action_plugins      ANSIBLE_ACTION_PLUGINS      /usr/share/ansible_plugins/action_plugins
DEFAULT_CALLBACK_PLUGIN_PATH    callback_plugins    ANSIBLE_CALLBACK_PLUGINS    /usr/share/ansible_plugins/callback_plugins
DEFAULT_CONNECTION_PLUGIN_PATH  connection_plugins  ANSIBLE_CONNECTION_PLUGINS  /usr/share/ansible_plugins/connection_plugins
DEFAULT_LOOKUP_PLUGIN_PATH      lookup_plugins      ANSIBLE_LOOKUP_PLUGINS      /usr/share/ansible_plugins/lookup_plugins
DEFAULT_VARS_PLUGIN_PATH        vars_plugins        ANSIBLE_VARS_PLUGINS        /usr/share/ansible_plugins/vars_plugins
DEFAULT_FILTER_PLUGIN_PATH      filter_plugins      ANSIBLE_FILTER_PLUGINS      /usr/share/ansible_plugins/filter_plugins

# lookup plugin related
ANSIBLE_ETCD_URL          etcd_url          ANSIBLE_ETCD_URL          http://127.0.0.1:4001
'''

def load_constants(config_str):
    """
    Set module constants by parsing definition from config_str.
    This method can be used to relod constants after import phase
    finished (for example, when detecting and loading ansible.cfg
    from alternative location, such a playbook dir)
    """
    global p
    keys = ['name', 'key', 'env', 'default', 'flags']
    for line in config_str.splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        const = line.split()
        # pad to length 5
        const += ['']*(5 - len(const))
        row = dict(zip(keys, const))
        # normalize
        if row['env'] == 'None':
            row['env'] = None
        if row['default'] == 'None':
            row['default'] = None
        elif row['default'] == "''":
            row['default'] = ''
        elif 'G' in row['flags']:   # value is the name of global variable
            row['default'] = globals()[row['default']]
        # set global variable
        if   'X' in row['flags']:   # constant_name = shell_expand_path(key, env_var, default) 
            globals()[row['name']] = shell_expand_path(get_config(p, DEFAULTS, row['key'], row['env'], row['default']))
        elif 'I' in row['flags']:   # constant_name = get_config(key, env, int(default), integer=True)
            globals()[row['name']] = get_config(p, DEFAULTS, row['key'], row['env'], int(row['default']), integer=True)
        elif 'B' in row['flags']:
            if row['default'] not in ['True', 'False']:
                raise
            value = True
            if row['default'] == 'False':
                value = False
            globals()[row['name']] = get_config(p, DEFAULTS, row['key'], row['env'], value, boolean=True)
        else:
            globals()[row['name']] = get_config(p, DEFAULTS, row['key'], row['env'], row['default'])


DEFAULT_SCP_IF_SSH        = get_config(p, 'ssh_connection', 'scp_if_ssh',       'ANSIBLE_SCP_IF_SSH',       False, boolean=True)
DEFAULT_MANAGED_STR       = get_config(p, DEFAULTS, 'ansible_managed',  None,           'Ansible managed: {file} modified on %Y-%m-%d %H:%M:%S by {uid} on {host}')
DEFAULT_SYSLOG_FACILITY   = get_config(p, DEFAULTS, 'syslog_facility',  'ANSIBLE_SYSLOG_FACILITY', 'LOG_USER')
DEFAULT_KEEP_REMOTE_FILES = get_config(p, DEFAULTS, 'keep_remote_files', 'ANSIBLE_KEEP_REMOTE_FILES', False, boolean=True)
DEFAULT_HASH_BEHAVIOUR    = get_config(p, DEFAULTS, 'hash_behaviour', 'ANSIBLE_HASH_BEHAVIOUR', 'replace')
DEFAULT_LEGACY_PLAYBOOK_VARIABLES = get_config(p, DEFAULTS, 'legacy_playbook_variables', 'ANSIBLE_LEGACY_PLAYBOOK_VARIABLES', True, boolean=True)
DEFAULT_JINJA2_EXTENSIONS = get_config(p, DEFAULTS, 'jinja2_extensions', 'ANSIBLE_JINJA2_EXTENSIONS', None)
DEFAULT_EXECUTABLE        = get_config(p, DEFAULTS, 'executable', 'ANSIBLE_EXECUTABLE', '/bin/sh')

ANSIBLE_NOCOLOR                = get_config(p, DEFAULTS, 'nocolor', 'ANSIBLE_NOCOLOR', None, boolean=True)
ANSIBLE_NOCOWS                 = get_config(p, DEFAULTS, 'nocows', 'ANSIBLE_NOCOWS', None, boolean=True)
DISPLAY_SKIPPED_HOSTS          = get_config(p, DEFAULTS, 'display_skipped_hosts', 'DISPLAY_SKIPPED_HOSTS', True, boolean=True)
DEFAULT_UNDEFINED_VAR_BEHAVIOR = get_config(p, DEFAULTS, 'error_on_undefined_vars', 'ANSIBLE_ERROR_ON_UNDEFINED_VARS', True, boolean=True)
HOST_KEY_CHECKING              = get_config(p, DEFAULTS, 'host_key_checking',  'ANSIBLE_HOST_KEY_CHECKING',    True, boolean=True)
DEPRECATION_WARNINGS           = get_config(p, DEFAULTS, 'deprecation_warnings', 'ANSIBLE_DEPRECATION_WARNINGS', True, boolean=True)

# CONNECTION RELATED
ANSIBLE_SSH_ARGS               = get_config(p, 'ssh_connection', 'ssh_args', 'ANSIBLE_SSH_ARGS', None)
ANSIBLE_SSH_CONTROL_PATH       = get_config(p, 'ssh_connection', 'control_path', 'ANSIBLE_SSH_CONTROL_PATH', "%(directory)s/ansible-ssh-%%h-%%p-%%r")
PARAMIKO_RECORD_HOST_KEYS      = get_config(p, 'paramiko_connection', 'record_host_keys', 'ANSIBLE_PARAMIKO_RECORD_HOST_KEYS', True, boolean=True)
ZEROMQ_PORT                    = get_config(p, 'fireball_connection', 'zeromq_port', 'ANSIBLE_ZEROMQ_PORT', 5099, integer=True)
ACCELERATE_PORT                = get_config(p, 'accelerate', 'accelerate_port', 'ACCELERATE_PORT', 5099, integer=True)
ACCELERATE_TIMEOUT             = get_config(p, 'accelerate', 'accelerate_timeout', 'ACCELERATE_TIMEOUT', 30, integer=True)
ACCELERATE_CONNECT_TIMEOUT     = get_config(p, 'accelerate', 'accelerate_connect_timeout', 'ACCELERATE_CONNECT_TIMEOUT', 1.0, floating=True)
PARAMIKO_PTY                   = get_config(p, 'paramiko_connection', 'pty', 'ANSIBLE_PARAMIKO_PTY', True, boolean=True)

# characters included in auto-generated passwords
DEFAULT_PASSWORD_CHARS = ascii_letters + digits + ".,:-_"

# non-configurable things
DEFAULT_SUDO_PASS         = None
DEFAULT_REMOTE_PASS       = None
DEFAULT_SUBSET            = None

reload_config()


