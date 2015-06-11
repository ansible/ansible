# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

def get_config(p, section, key, env_var, default, boolean=False, integer=False, floating=False, islist=False):
    ''' return a configuration variable with casting '''
    value = _get_config(p, section, key, env_var, default)
    if boolean:
        return mk_boolean(value)
    if value and integer:
        return int(value)
    if value and floating:
        return float(value)
    if value and islist:
        return [x.strip() for x in value.split(',')]
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
    ''' Load Config File order(first found is used): ENV, CWD, HOME, /etc/ansible '''

    p = ConfigParser.ConfigParser()

    path0 = os.getenv("ANSIBLE_CONFIG", None)
    if path0 is not None:
        path0 = os.path.expanduser(path0)
    path1 = os.getcwd() + "/ansible.cfg"
    path2 = os.path.expanduser("~/.ansible.cfg")
    path3 = "/etc/ansible/ansible.cfg"

    for path in [path0, path1, path2, path3]:
        if path is not None and os.path.exists(path):
            try:
                p.read(path)
            except ConfigParser.Error as e:
                print "Error reading config file: \n%s" % e
                sys.exit(1)
            return p
    return None

def shell_expand_path(path):
    ''' shell_expand_path is needed as os.path.expanduser does not work
        when path is None, which is the default for ANSIBLE_PRIVATE_KEY_FILE '''
    if path:
        path = os.path.expanduser(os.path.expandvars(path))
    return path

p = load_config_file()

active_user   = pwd.getpwuid(os.geteuid())[0]

# check all of these extensions when looking for yaml files for things like
# group variables -- really anything we can load
YAML_FILENAME_EXTENSIONS = [ "", ".yml", ".yaml", ".json" ]

# sections in config file
DEFAULTS='defaults'

# configurable things
DEFAULT_HOST_LIST         = shell_expand_path(get_config(p, DEFAULTS, 'inventory', 'ANSIBLE_INVENTORY', get_config(p, DEFAULTS,'hostfile','ANSIBLE_HOSTS', '/etc/ansible/hosts')))
DEFAULT_MODULE_PATH       = get_config(p, DEFAULTS, 'library',          'ANSIBLE_LIBRARY',          None)
DEFAULT_ROLES_PATH        = shell_expand_path(get_config(p, DEFAULTS, 'roles_path',       'ANSIBLE_ROLES_PATH',       '/etc/ansible/roles'))
DEFAULT_REMOTE_TMP        = get_config(p, DEFAULTS, 'remote_tmp',       'ANSIBLE_REMOTE_TEMP',      '$HOME/.ansible/tmp')
DEFAULT_MODULE_NAME       = get_config(p, DEFAULTS, 'module_name',      None,                       'command')
DEFAULT_PATTERN           = get_config(p, DEFAULTS, 'pattern',          None,                       '*')
DEFAULT_FORKS             = get_config(p, DEFAULTS, 'forks',            'ANSIBLE_FORKS',            5, integer=True)
DEFAULT_MODULE_ARGS       = get_config(p, DEFAULTS, 'module_args',      'ANSIBLE_MODULE_ARGS',      '')
DEFAULT_MODULE_LANG       = get_config(p, DEFAULTS, 'module_lang',      'ANSIBLE_MODULE_LANG',      'en_US.UTF-8')
DEFAULT_TIMEOUT           = get_config(p, DEFAULTS, 'timeout',          'ANSIBLE_TIMEOUT',          10, integer=True)
DEFAULT_POLL_INTERVAL     = get_config(p, DEFAULTS, 'poll_interval',    'ANSIBLE_POLL_INTERVAL',    15, integer=True)
DEFAULT_REMOTE_USER       = get_config(p, DEFAULTS, 'remote_user',      'ANSIBLE_REMOTE_USER',      active_user)
DEFAULT_ASK_PASS          = get_config(p, DEFAULTS, 'ask_pass',  'ANSIBLE_ASK_PASS',    False, boolean=True)
DEFAULT_PRIVATE_KEY_FILE  = shell_expand_path(get_config(p, DEFAULTS, 'private_key_file', 'ANSIBLE_PRIVATE_KEY_FILE', None))
DEFAULT_ASK_SUDO_PASS     = get_config(p, DEFAULTS, 'ask_sudo_pass',    'ANSIBLE_ASK_SUDO_PASS',    False, boolean=True)
DEFAULT_REMOTE_PORT       = get_config(p, DEFAULTS, 'remote_port',      'ANSIBLE_REMOTE_PORT',      None, integer=True)
DEFAULT_ASK_VAULT_PASS    = get_config(p, DEFAULTS, 'ask_vault_pass',    'ANSIBLE_ASK_VAULT_PASS',    False, boolean=True)
DEFAULT_VAULT_PASSWORD_FILE = shell_expand_path(get_config(p, DEFAULTS, 'vault_password_file', 'ANSIBLE_VAULT_PASSWORD_FILE', None))
DEFAULT_TRANSPORT         = get_config(p, DEFAULTS, 'transport',        'ANSIBLE_TRANSPORT',        'smart')
DEFAULT_SCP_IF_SSH        = get_config(p, 'ssh_connection', 'scp_if_ssh',       'ANSIBLE_SCP_IF_SSH',       False, boolean=True)
DEFAULT_MANAGED_STR       = get_config(p, DEFAULTS, 'ansible_managed',  None,           'Ansible managed: {file} modified on %Y-%m-%d %H:%M:%S by {uid} on {host}')
DEFAULT_SYSLOG_FACILITY   = get_config(p, DEFAULTS, 'syslog_facility',  'ANSIBLE_SYSLOG_FACILITY', 'LOG_USER')
DEFAULT_KEEP_REMOTE_FILES = get_config(p, DEFAULTS, 'keep_remote_files', 'ANSIBLE_KEEP_REMOTE_FILES', False, boolean=True)
DEFAULT_SUDO              = get_config(p, DEFAULTS, 'sudo', 'ANSIBLE_SUDO', False, boolean=True)
DEFAULT_SUDO_USER         = get_config(p, DEFAULTS, 'sudo_user',        'ANSIBLE_SUDO_USER',        'root')
DEFAULT_SUDO_EXE          = get_config(p, DEFAULTS, 'sudo_exe', 'ANSIBLE_SUDO_EXE', 'sudo')
DEFAULT_SUDO_FLAGS        = get_config(p, DEFAULTS, 'sudo_flags', 'ANSIBLE_SUDO_FLAGS', '-H')
DEFAULT_HASH_BEHAVIOUR    = get_config(p, DEFAULTS, 'hash_behaviour', 'ANSIBLE_HASH_BEHAVIOUR', 'replace')
DEFAULT_JINJA2_EXTENSIONS = get_config(p, DEFAULTS, 'jinja2_extensions', 'ANSIBLE_JINJA2_EXTENSIONS', None)
DEFAULT_EXECUTABLE        = get_config(p, DEFAULTS, 'executable', 'ANSIBLE_EXECUTABLE', '/bin/sh')
DEFAULT_SU_EXE            = get_config(p, DEFAULTS, 'su_exe', 'ANSIBLE_SU_EXE', 'su')
DEFAULT_SU                = get_config(p, DEFAULTS, 'su', 'ANSIBLE_SU', False, boolean=True)
DEFAULT_SU_FLAGS          = get_config(p, DEFAULTS, 'su_flags', 'ANSIBLE_SU_FLAGS', '')
DEFAULT_SU_USER           = get_config(p, DEFAULTS, 'su_user', 'ANSIBLE_SU_USER', 'root')
DEFAULT_ASK_SU_PASS       = get_config(p, DEFAULTS, 'ask_su_pass', 'ANSIBLE_ASK_SU_PASS', False, boolean=True)
DEFAULT_GATHERING         = get_config(p, DEFAULTS, 'gathering', 'ANSIBLE_GATHERING', 'implicit').lower()
DEFAULT_LOG_PATH          = shell_expand_path(get_config(p, DEFAULTS, 'log_path',           'ANSIBLE_LOG_PATH', ''))

# selinux
DEFAULT_SELINUX_SPECIAL_FS = get_config(p, 'selinux', 'special_context_filesystems', None, 'fuse, nfs, vboxsf', islist=True)

#TODO: get rid of ternary chain mess
BECOME_METHODS            = ['sudo','su','pbrun','pfexec','runas']
BECOME_ERROR_STRINGS      = {'sudo': 'Sorry, try again.', 'su': 'Authentication failure', 'pbrun': '', 'pfexec': '', 'runas': ''}
DEFAULT_BECOME            = get_config(p, 'privilege_escalation', 'become', 'ANSIBLE_BECOME',False, boolean=True)
DEFAULT_BECOME_METHOD     = get_config(p, 'privilege_escalation', 'become_method', 'ANSIBLE_BECOME_METHOD','sudo' if DEFAULT_SUDO else 'su' if DEFAULT_SU else 'sudo' ).lower()
DEFAULT_BECOME_USER       = get_config(p, 'privilege_escalation', 'become_user', 'ANSIBLE_BECOME_USER',default=None)
DEFAULT_BECOME_ASK_PASS   = get_config(p, 'privilege_escalation', 'become_ask_pass', 'ANSIBLE_BECOME_ASK_PASS', False, boolean=True)
# need to rethink impementing these 2
DEFAULT_BECOME_EXE = None
#DEFAULT_BECOME_EXE        = get_config(p, DEFAULTS, 'become_exe', 'ANSIBLE_BECOME_EXE','sudo' if DEFAULT_SUDO else 'su' if DEFAULT_SU else 'sudo')
#DEFAULT_BECOME_FLAGS      = get_config(p, DEFAULTS, 'become_flags', 'ANSIBLE_BECOME_FLAGS',DEFAULT_SUDO_FLAGS if DEFAULT_SUDO else DEFAULT_SU_FLAGS if DEFAULT_SU else '-H')


DEFAULT_ACTION_PLUGIN_PATH     = get_config(p, DEFAULTS, 'action_plugins',     'ANSIBLE_ACTION_PLUGINS', '~/.ansible/plugins/action_plugins:/usr/share/ansible_plugins/action_plugins')
DEFAULT_CACHE_PLUGIN_PATH      = get_config(p, DEFAULTS, 'cache_plugins',      'ANSIBLE_CACHE_PLUGINS', '~/.ansible/plugins/cache_plugins:/usr/share/ansible_plugins/cache_plugins')
DEFAULT_CALLBACK_PLUGIN_PATH   = get_config(p, DEFAULTS, 'callback_plugins',   'ANSIBLE_CALLBACK_PLUGINS', '~/.ansible/plugins/callback_plugins:/usr/share/ansible_plugins/callback_plugins')
DEFAULT_CONNECTION_PLUGIN_PATH = get_config(p, DEFAULTS, 'connection_plugins', 'ANSIBLE_CONNECTION_PLUGINS', '~/.ansible/plugins/connection_plugins:/usr/share/ansible_plugins/connection_plugins')
DEFAULT_LOOKUP_PLUGIN_PATH     = get_config(p, DEFAULTS, 'lookup_plugins',     'ANSIBLE_LOOKUP_PLUGINS', '~/.ansible/plugins/lookup_plugins:/usr/share/ansible_plugins/lookup_plugins')
DEFAULT_VARS_PLUGIN_PATH       = get_config(p, DEFAULTS, 'vars_plugins',       'ANSIBLE_VARS_PLUGINS', '~/.ansible/plugins/vars_plugins:/usr/share/ansible_plugins/vars_plugins')
DEFAULT_FILTER_PLUGIN_PATH     = get_config(p, DEFAULTS, 'filter_plugins',     'ANSIBLE_FILTER_PLUGINS', '~/.ansible/plugins/filter_plugins:/usr/share/ansible_plugins/filter_plugins')

CACHE_PLUGIN                   = get_config(p, DEFAULTS, 'fact_caching', 'ANSIBLE_CACHE_PLUGIN', 'memory')
CACHE_PLUGIN_CONNECTION        = get_config(p, DEFAULTS, 'fact_caching_connection', 'ANSIBLE_CACHE_PLUGIN_CONNECTION', None)
CACHE_PLUGIN_PREFIX            = get_config(p, DEFAULTS, 'fact_caching_prefix', 'ANSIBLE_CACHE_PLUGIN_PREFIX', 'ansible_facts')
CACHE_PLUGIN_TIMEOUT           = get_config(p, DEFAULTS, 'fact_caching_timeout', 'ANSIBLE_CACHE_PLUGIN_TIMEOUT', 24 * 60 * 60, integer=True)

ANSIBLE_FORCE_COLOR            = get_config(p, DEFAULTS, 'force_color', 'ANSIBLE_FORCE_COLOR', None, boolean=True)
ANSIBLE_NOCOLOR                = get_config(p, DEFAULTS, 'nocolor', 'ANSIBLE_NOCOLOR', None, boolean=True)
ANSIBLE_NOCOWS                 = get_config(p, DEFAULTS, 'nocows', 'ANSIBLE_NOCOWS', None, boolean=True)
DISPLAY_SKIPPED_HOSTS          = get_config(p, DEFAULTS, 'display_skipped_hosts', 'DISPLAY_SKIPPED_HOSTS', True, boolean=True)
DEFAULT_UNDEFINED_VAR_BEHAVIOR = get_config(p, DEFAULTS, 'error_on_undefined_vars', 'ANSIBLE_ERROR_ON_UNDEFINED_VARS', True, boolean=True)
HOST_KEY_CHECKING              = get_config(p, DEFAULTS, 'host_key_checking',  'ANSIBLE_HOST_KEY_CHECKING',    True, boolean=True)
SYSTEM_WARNINGS                = get_config(p, DEFAULTS, 'system_warnings', 'ANSIBLE_SYSTEM_WARNINGS', True, boolean=True)
DEPRECATION_WARNINGS           = get_config(p, DEFAULTS, 'deprecation_warnings', 'ANSIBLE_DEPRECATION_WARNINGS', True, boolean=True)
DEFAULT_CALLABLE_WHITELIST     = get_config(p, DEFAULTS, 'callable_whitelist', 'ANSIBLE_CALLABLE_WHITELIST', [], islist=True)
COMMAND_WARNINGS               = get_config(p, DEFAULTS, 'command_warnings', 'ANSIBLE_COMMAND_WARNINGS', False, boolean=True)
DEFAULT_LOAD_CALLBACK_PLUGINS  = get_config(p, DEFAULTS, 'bin_ansible_callbacks', 'ANSIBLE_LOAD_CALLBACK_PLUGINS', False, boolean=True)
DEFAULT_FORCE_HANDLERS         = get_config(p, DEFAULTS, 'force_handlers', 'ANSIBLE_FORCE_HANDLERS', False, boolean=True)


RETRY_FILES_ENABLED            = get_config(p, DEFAULTS, 'retry_files_enabled', 'ANSIBLE_RETRY_FILES_ENABLED', True, boolean=True)
RETRY_FILES_SAVE_PATH          = get_config(p, DEFAULTS, 'retry_files_save_path', 'ANSIBLE_RETRY_FILES_SAVE_PATH', '~/')

# CONNECTION RELATED
ANSIBLE_SSH_ARGS               = get_config(p, 'ssh_connection', 'ssh_args', 'ANSIBLE_SSH_ARGS', None)
ANSIBLE_SSH_CONTROL_PATH       = get_config(p, 'ssh_connection', 'control_path', 'ANSIBLE_SSH_CONTROL_PATH', "%(directory)s/ansible-ssh-%%h-%%p-%%r")
ANSIBLE_SSH_PIPELINING         = get_config(p, 'ssh_connection', 'pipelining', 'ANSIBLE_SSH_PIPELINING', False, boolean=True)
PARAMIKO_RECORD_HOST_KEYS      = get_config(p, 'paramiko_connection', 'record_host_keys', 'ANSIBLE_PARAMIKO_RECORD_HOST_KEYS', True, boolean=True)
# obsolete -- will be formally removed
ZEROMQ_PORT                    = get_config(p, 'fireball_connection', 'zeromq_port', 'ANSIBLE_ZEROMQ_PORT', 5099, integer=True)
ACCELERATE_PORT                = get_config(p, 'accelerate', 'accelerate_port', 'ACCELERATE_PORT', 5099, integer=True)
ACCELERATE_TIMEOUT             = get_config(p, 'accelerate', 'accelerate_timeout', 'ACCELERATE_TIMEOUT', 30, integer=True)
ACCELERATE_CONNECT_TIMEOUT     = get_config(p, 'accelerate', 'accelerate_connect_timeout', 'ACCELERATE_CONNECT_TIMEOUT', 1.0, floating=True)
ACCELERATE_DAEMON_TIMEOUT      = get_config(p, 'accelerate', 'accelerate_daemon_timeout', 'ACCELERATE_DAEMON_TIMEOUT', 30, integer=True)
ACCELERATE_KEYS_DIR            = get_config(p, 'accelerate', 'accelerate_keys_dir', 'ACCELERATE_KEYS_DIR', '~/.fireball.keys')
ACCELERATE_KEYS_DIR_PERMS      = get_config(p, 'accelerate', 'accelerate_keys_dir_perms', 'ACCELERATE_KEYS_DIR_PERMS', '700')
ACCELERATE_KEYS_FILE_PERMS     = get_config(p, 'accelerate', 'accelerate_keys_file_perms', 'ACCELERATE_KEYS_FILE_PERMS', '600')
ACCELERATE_MULTI_KEY           = get_config(p, 'accelerate', 'accelerate_multi_key', 'ACCELERATE_MULTI_KEY', False, boolean=True)
PARAMIKO_PTY                   = get_config(p, 'paramiko_connection', 'pty', 'ANSIBLE_PARAMIKO_PTY', True, boolean=True)

# characters included in auto-generated passwords
DEFAULT_PASSWORD_CHARS = ascii_letters + digits + ".,:-_"

# non-configurable things
DEFAULT_BECOME_PASS       = None
DEFAULT_SUDO_PASS         = None
DEFAULT_REMOTE_PASS       = None
DEFAULT_SUBSET            = None
DEFAULT_SU_PASS           = None
VAULT_VERSION_MIN         = 1.0
VAULT_VERSION_MAX         = 1.0
