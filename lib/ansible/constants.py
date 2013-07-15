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

# copied from utils, avoid circular reference fun :)
def mk_boolean(value):
    val = str(value)
    if val.lower() in [ "true", "t", "y", "1", "yes" ]:
        return True
    else:
        return False

def get_config(p, section, key, env_var, default, boolean=False, integer=False):
    ''' return a configuration variable with casting '''
    value = _get_config(p, section, key, env_var, default)
    if boolean:
        return mk_boolean(value)
    if integer:
        return int(value)
    return value

def _get_config(p, section, key, env_var, default, boolean=True):
    ''' helper function for get_config '''
    if env_var is not None:
        value = os.environ.get(env_var, None)
        if value is not None:
            return value
    if p is not None:
        try:
            return p.get(section, key)
        except:
            return default
    return default

def load_config_file():
    p = ConfigParser.ConfigParser()
    path1 = os.path.expanduser(os.environ.get('ANSIBLE_CONFIG', "~/.ansible.cfg"))
    path2 = os.getcwd() + "/ansible.cfg"
    path3 = "/etc/ansible/ansible.cfg"

    if os.path.exists(path1):
        p.read(path1)
    elif os.path.exists(path2):
        p.read(path2)
    elif os.path.exists(path3):
        p.read(path3)
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

# Needed so the RPM can call setup.py and have modules land in the
# correct location. See #1277 for discussion
if getattr(sys, "real_prefix", None):
    DIST_MODULE_PATH = os.path.join(sys.prefix, 'share/ansible/')
else:
    DIST_MODULE_PATH = '/usr/share/ansible/'

# sections in config file
DEFAULTS='defaults'

# configurable things
DEFAULT_HOST_LIST         = shell_expand_path(get_config(p, DEFAULTS, 'hostfile', 'ANSIBLE_HOSTS', '/etc/ansible/hosts'))
DEFAULT_MODULE_PATH       = get_config(p, DEFAULTS, 'library',          'ANSIBLE_LIBRARY',          DIST_MODULE_PATH)
DEFAULT_REMOTE_TMP        = shell_expand_path(get_config(p, DEFAULTS, 'remote_tmp',       'ANSIBLE_REMOTE_TEMP',      '$HOME/.ansible/tmp'))
DEFAULT_MODULE_NAME       = get_config(p, DEFAULTS, 'module_name',      None,                       'command')
DEFAULT_PATTERN           = get_config(p, DEFAULTS, 'pattern',          None,                       '*')
DEFAULT_FORKS             = get_config(p, DEFAULTS, 'forks',            'ANSIBLE_FORKS',            5)
DEFAULT_MODULE_ARGS       = get_config(p, DEFAULTS, 'module_args',      'ANSIBLE_MODULE_ARGS',      '')
DEFAULT_MODULE_LANG       = get_config(p, DEFAULTS, 'module_lang',      'ANSIBLE_MODULE_LANG',      'C')
DEFAULT_TIMEOUT           = get_config(p, DEFAULTS, 'timeout',          'ANSIBLE_TIMEOUT',          10)
DEFAULT_POLL_INTERVAL     = get_config(p, DEFAULTS, 'poll_interval',    'ANSIBLE_POLL_INTERVAL',    15)
DEFAULT_REMOTE_USER       = get_config(p, DEFAULTS, 'remote_user',      'ANSIBLE_REMOTE_USER',      active_user)
DEFAULT_ASK_PASS          = get_config(p, DEFAULTS, 'ask_pass',  'ANSIBLE_ASK_PASS',    False, boolean=True)
DEFAULT_PRIVATE_KEY_FILE  = shell_expand_path(get_config(p, DEFAULTS, 'private_key_file', 'ANSIBLE_PRIVATE_KEY_FILE', None))
DEFAULT_SUDO_USER         = get_config(p, DEFAULTS, 'sudo_user',        'ANSIBLE_SUDO_USER',        'root')
DEFAULT_ASK_SUDO_PASS     = get_config(p, DEFAULTS, 'ask_sudo_pass',    'ANSIBLE_ASK_SUDO_PASS',    False, boolean=True)
DEFAULT_REMOTE_PORT       = int(get_config(p, DEFAULTS, 'remote_port',      'ANSIBLE_REMOTE_PORT',      22))
DEFAULT_TRANSPORT         = get_config(p, DEFAULTS, 'transport',        'ANSIBLE_TRANSPORT',        'smart')
DEFAULT_SCP_IF_SSH        = get_config(p, 'ssh_connection', 'scp_if_ssh',       'ANSIBLE_SCP_IF_SSH',       False, boolean=True)
DEFAULT_MANAGED_STR       = get_config(p, DEFAULTS, 'ansible_managed',  None,           'Ansible managed: {file} modified on %Y-%m-%d %H:%M:%S by {uid} on {host}')
DEFAULT_SYSLOG_FACILITY   = get_config(p, DEFAULTS, 'syslog_facility',  'ANSIBLE_SYSLOG_FACILITY', 'LOG_USER')
DEFAULT_KEEP_REMOTE_FILES = get_config(p, DEFAULTS, 'keep_remote_files', 'ANSIBLE_KEEP_REMOTE_FILES', False, boolean=True)
DEFAULT_SUDO              = get_config(p, DEFAULTS, 'sudo', 'ANSIBLE_SUDO', False, boolean=True)
DEFAULT_SUDO_EXE          = get_config(p, DEFAULTS, 'sudo_exe', 'ANSIBLE_SUDO_EXE', 'sudo')
DEFAULT_SUDO_FLAGS        = get_config(p, DEFAULTS, 'sudo_flags', 'ANSIBLE_SUDO_FLAGS', '-H')
DEFAULT_HASH_BEHAVIOUR    = get_config(p, DEFAULTS, 'hash_behaviour', 'ANSIBLE_HASH_BEHAVIOUR', 'replace')
DEFAULT_LEGACY_PLAYBOOK_VARIABLES = get_config(p, DEFAULTS, 'legacy_playbook_variables', 'ANSIBLE_LEGACY_PLAYBOOK_VARIABLES', True, boolean=True)
DEFAULT_JINJA2_EXTENSIONS = get_config(p, DEFAULTS, 'jinja2_extensions', 'ANSIBLE_JINJA2_EXTENSIONS', None)
DEFAULT_EXECUTABLE        = get_config(p, DEFAULTS, 'executable', 'ANSIBLE_EXECUTABLE', '/bin/sh')

DEFAULT_ACTION_PLUGIN_PATH     = get_config(p, DEFAULTS, 'action_plugins',     'ANSIBLE_ACTION_PLUGINS', '/usr/share/ansible_plugins/action_plugins')
DEFAULT_CALLBACK_PLUGIN_PATH   = get_config(p, DEFAULTS, 'callback_plugins',   'ANSIBLE_CALLBACK_PLUGINS', '/usr/share/ansible_plugins/callback_plugins')
DEFAULT_CONNECTION_PLUGIN_PATH = get_config(p, DEFAULTS, 'connection_plugins', 'ANSIBLE_CONNECTION_PLUGINS', '/usr/share/ansible_plugins/connection_plugins')
DEFAULT_LOOKUP_PLUGIN_PATH     = get_config(p, DEFAULTS, 'lookup_plugins',     'ANSIBLE_LOOKUP_PLUGINS', '/usr/share/ansible_plugins/lookup_plugins')
DEFAULT_VARS_PLUGIN_PATH       = get_config(p, DEFAULTS, 'vars_plugins',       'ANSIBLE_VARS_PLUGINS', '/usr/share/ansible_plugins/vars_plugins')
DEFAULT_FILTER_PLUGIN_PATH     = get_config(p, DEFAULTS, 'filter_plugins',     'ANSIBLE_FILTER_PLUGINS', '/usr/share/ansible_plugins/filter_plugins')
DEFAULT_LOG_PATH               = shell_expand_path(get_config(p, DEFAULTS, 'log_path',           'ANSIBLE_LOG_PATH', ''))

ANSIBLE_NOCOWS                 = get_config(p, DEFAULTS, 'nocows', 'ANSIBLE_NOCOWS', None)
ANSIBLE_SSH_ARGS               = get_config(p, 'ssh_connection', 'ssh_args', 'ANSIBLE_SSH_ARGS', None)
PARAMIKO_RECORD_HOST_KEYS      = get_config(p, 'paramiko_connection', 'record_host_keys', 'ANSIBLE_PARAMIKO_RECORD_HOST_KEYS', True, boolean=True)
ZEROMQ_PORT                    = int(get_config(p, 'fireball_connection', 'zeromq_port', 'ANSIBLE_ZEROMQ_PORT', 5099))

DEFAULT_UNDEFINED_VAR_BEHAVIOR = get_config(p, DEFAULTS, 'error_on_undefined_vars', 'ANSIBLE_ERROR_ON_UNDEFINED_VARS', False, boolean=True)
HOST_KEY_CHECKING              = get_config(p, DEFAULTS, 'host_key_checking',  'ANSIBLE_HOST_KEY_CHECKING',    True, boolean=True)

# non-configurable things
DEFAULT_SUDO_PASS         = None
DEFAULT_REMOTE_PASS       = None
DEFAULT_SUBSET            = None

