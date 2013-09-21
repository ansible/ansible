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
from functools import partial


# copied from utils, avoid circular reference fun :)
def mk_boolean(value):
    if value is None:
        return False
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

def _get_config(p, section, key, env_var, default):
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

active_user = pwd.getpwuid(os.geteuid())[0]

# Needed so the RPM can call setup.py and have modules land in the
# correct location. See #1277 for discussion
if getattr(sys, "real_prefix", None):
    # in a virtualenv
    DIST_MODULE_PATH = os.path.join(sys.prefix, 'share/ansible/')
else:
    DIST_MODULE_PATH = '/usr/share/ansible/'

# [defaults]
get_defaults_config = partial(get_config, p, 'defaults')
# [ssh_connection]
get_ssh_connection_config = partial(get_config, p, 'ssh_connection')
# [paramiko_connection]
get_paramiko_connection_config = partial(get_config, p, 'paramiko_connection')
# [fireball_connection]
get_fireball_connection_config = partial(get_config, p, 'fireball_connection')
# [accelerate]
get_accelerate_config = partial(get_config, p, 'accelerate')

# Paths in [defaults]
DEFAULT_HOST_LIST = shell_expand_path(get_defaults_config(
    'hostfile',
    'ANSIBLE_HOSTS',
    '/etc/ansible/hosts',
))
DEFAULT_MODULE_PATH = shell_expand_path(get_defaults_config(
    'library',
    'ANSIBLE_LIBRARY',
    DIST_MODULE_PATH,
))
DEFAULT_REMOTE_TMP = shell_expand_path(get_defaults_config(
    'remote_tmp',
    'ANSIBLE_REMOTE_TEMP',
    '$HOME/.ansible/tmp',
))
DEFAULT_EXECUTABLE = shell_expand_path(get_defaults_config(
    'executable',
    'ANSIBLE_EXECUTABLE',
    '/bin/sh',
))
DEFAULT_ACTION_PLUGIN_PATH = shell_expand_path(get_defaults_config(
    'action_plugins',
    'ANSIBLE_ACTION_PLUGINS',
    '/usr/share/ansible_plugins/action_plugins',
))
DEFAULT_CALLBACK_PLUGIN_PATH = shell_expand_path(get_defaults_config(
    'callback_plugins',
    'ANSIBLE_CALLBACK_PLUGINS',
    '/usr/share/ansible_plugins/callback_plugins',
))
DEFAULT_CONNECTION_PLUGIN_PATH = shell_expand_path(get_defaults_config(
    'connection_plugins',
    'ANSIBLE_CONNECTION_PLUGINS',
    '/usr/share/ansible_plugins/connection_plugins',
))
DEFAULT_LOOKUP_PLUGIN_PATH = shell_expand_path(get_defaults_config(
    'lookup_plugins',
    'ANSIBLE_LOOKUP_PLUGINS',
    '/usr/share/ansible_plugins/lookup_plugins',
))
DEFAULT_VARS_PLUGIN_PATH = shell_expand_path(get_defaults_config(
    'vars_plugins',
    'ANSIBLE_VARS_PLUGINS',
    '/usr/share/ansible_plugins/vars_plugins',
))
DEFAULT_FILTER_PLUGIN_PATH = shell_expand_path(get_defaults_config(
    'filter_plugins',
    'ANSIBLE_FILTER_PLUGINS',
    '/usr/share/ansible_plugins/filter_plugins',
))
DEFAULT_LOG_PATH = shell_expand_path(get_defaults_config(
    'log_path',
    'ANSIBLE_LOG_PATH',
    '',
))
DEFAULT_PRIVATE_KEY_FILE  = shell_expand_path(get_defaults_config(
    'private_key_file',
    'ANSIBLE_PRIVATE_KEY_FILE',
    None,
))
# non-paths in [defaults]
DEFAULT_MODULE_NAME = get_defaults_config(
    'module_name',
    None,
    'command',
)
DEFAULT_PATTERN = get_defaults_config(
    'pattern',
    None,
    '*',
)
DEFAULT_FORKS = get_defaults_config(
    'forks',
    'ANSIBLE_FORKS',
    5, integer=True,
)
DEFAULT_MODULE_ARGS = get_defaults_config(
    'module_args',
    'ANSIBLE_MODULE_ARGS',
    '',
)
DEFAULT_MODULE_LANG = get_defaults_config(
    'module_lang',
    'ANSIBLE_MODULE_LANG',
    'C',
)
DEFAULT_TIMEOUT = get_defaults_config(
    'timeout',
    'ANSIBLE_TIMEOUT',
    10, integer=True,
)
DEFAULT_POLL_INTERVAL = get_defaults_config(
    'poll_interval',
    'ANSIBLE_POLL_INTERVAL',
    15, integer=True,
)
DEFAULT_REMOTE_USER = get_defaults_config(
    'remote_user',
    'ANSIBLE_REMOTE_USER',
    active_user,
)
DEFAULT_SUDO_USER = get_defaults_config(
    'sudo_user',
    'ANSIBLE_SUDO_USER',
    'root',
)
DEFAULT_REMOTE_PORT = get_defaults_config(
    'remote_port',
    'ANSIBLE_REMOTE_PORT',
    22, integer=True,
)
DEFAULT_TRANSPORT = get_defaults_config(
    'transport',
    'ANSIBLE_TRANSPORT',
    'smart',
)
DEFAULT_MANAGED_STR = get_defaults_config(
    'ansible_managed',
    None,
    'Ansible managed: {file} modified on %Y-%m-%d %H:%M:%S by {uid} on {host}',
)
DEFAULT_SYSLOG_FACILITY = get_defaults_config(
    'syslog_facility',
    'ANSIBLE_SYSLOG_FACILITY',
    'LOG_USER',
)
DEFAULT_SUDO_EXE = get_defaults_config(
    'sudo_exe',
    'ANSIBLE_SUDO_EXE',
    'sudo',
)
DEFAULT_SUDO_FLAGS = get_defaults_config(
    'sudo_flags',
    'ANSIBLE_SUDO_FLAGS',
    '-H',
)
DEFAULT_HASH_BEHAVIOUR = get_defaults_config(
    'hash_behaviour',
    'ANSIBLE_HASH_BEHAVIOUR',
    'replace',
)
DEFAULT_JINJA2_EXTENSIONS = get_defaults_config(
    'jinja2_extensions',
    'ANSIBLE_JINJA2_EXTENSIONS',
    None,
)
# [defaults] booleans
DEFAULT_ASK_PASS = get_defaults_config(
    'ask_pass',
    'ANSIBLE_ASK_PASS',
    False, boolean=True,
)
DEFAULT_ASK_SUDO_PASS = get_defaults_config(
    'ask_sudo_pass',
    'ANSIBLE_ASK_SUDO_PASS',
    False, boolean=True,
)
DEFAULT_KEEP_REMOTE_FILES = get_defaults_config(
    'keep_remote_files',
    'ANSIBLE_KEEP_REMOTE_FILES',
    False, boolean=True,
)
DEFAULT_SUDO = get_defaults_config(
    'sudo',
    'ANSIBLE_SUDO',
    False, boolean=True,
)
DEFAULT_LEGACY_PLAYBOOK_VARIABLES = get_defaults_config(
    'legacy_playbook_variables',
    'ANSIBLE_LEGACY_PLAYBOOK_VARIABLES',
    True, boolean=True,
)
ANSIBLE_NOCOLOR = get_defaults_config(
    'nocolor',
    'ANSIBLE_NOCOLOR',
    None, boolean=True,
)
ANSIBLE_NOCOWS = get_defaults_config(
    'nocows',
    'ANSIBLE_NOCOWS',
    None, boolean=True,
)
DEFAULT_UNDEFINED_VAR_BEHAVIOR = get_defaults_config(
    'error_on_undefined_vars',
    'ANSIBLE_ERROR_ON_UNDEFINED_VARS',
    True, boolean=True,
)
HOST_KEY_CHECKING = get_defaults_config(
    'host_key_checking',
    'ANSIBLE_HOST_KEY_CHECKING',
    True, boolean=True,
)
# [ssh_connection]
DEFAULT_SCP_IF_SSH = get_ssh_connection_config(
    'scp_if_ssh',
    'ANSIBLE_SCP_IF_SSH',
    False, boolean=True,
)
ANSIBLE_SSH_ARGS = get_ssh_connection_config(
    'ssh_args',
    'ANSIBLE_SSH_ARGS',
    None,
)
ANSIBLE_SSH_CONTROL_PATH = get_ssh_connection_config(
    'control_path',
    'ANSIBLE_SSH_CONTROL_PATH',
    "%(directory)s/ansible-ssh-%%h-%%p-%%r",
)
# [paramiko_connection]
PARAMIKO_RECORD_HOST_KEYS = get_paramiko_connection_config(
    'record_host_keys',
    'ANSIBLE_PARAMIKO_RECORD_HOST_KEYS',
    True, boolean=True,
)
# [fireball_connection]
ZEROMQ_PORT = get_fireball_connection_config(
    'zeromq_port',
    'ANSIBLE_ZEROMQ_PORT',
    5099, integer=True,
)
# [accelerate]
ACCELERATE_PORT = get_accelerate_config(
    'accelerate_port',
    'ACCELERATE_PORT',
    5099, integer=True,
)

# non-configurable things
DEFAULT_SUDO_PASS = None
DEFAULT_REMOTE_PASS = None
DEFAULT_SUBSET = None
