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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
from string import ascii_letters, digits

from ansible.compat.six import string_types
from ansible.compat.six.moves import configparser

from ansible.parsing.quoting import unquote
from ansible.errors import AnsibleOptionsError

# copied from utils, avoid circular reference fun :)
def mk_boolean(value):
    if value is None:
        return False
    val = str(value)
    if val.lower() in [ "true", "t", "y", "1", "yes" ]:
        return True
    else:
        return False

def shell_expand(path):
    '''
    shell_expand is needed as os.path.expanduser does not work
    when path is None, which is the default for ANSIBLE_PRIVATE_KEY_FILE
    '''
    if path:
        path = os.path.expanduser(os.path.expandvars(path))
    return path

def get_config(p, section, key, env_var, default, boolean=False, integer=False, floating=False, islist=False, isnone=False, ispath=False):
    ''' return a configuration variable with casting '''
    value = _get_config(p, section, key, env_var, default)
    if boolean:
        value = mk_boolean(value)
    if value:
        if integer:
            value = int(value)
        elif floating:
            value = float(value)
        elif islist:
            if isinstance(value, string_types):
                value = [x.strip() for x in value.split(',')]
        elif isnone:
            if value == "None":
                value = None
        elif ispath:
            value = shell_expand(value)
        elif isinstance(value, string_types):
            value = unquote(value)
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

    p = configparser.ConfigParser()

    path0 = os.getenv("ANSIBLE_CONFIG", None)
    if path0 is not None:
        path0 = os.path.expanduser(path0)
        if os.path.isdir(path0):
            path0 += "/ansible.cfg"
    path1 = os.getcwd() + "/ansible.cfg"
    path2 = os.path.expanduser("~/.ansible.cfg")
    path3 = "/etc/ansible/ansible.cfg"

    for path in [path0, path1, path2, path3]:
        if path is not None and os.path.exists(path):
            try:
                p.read(path)
            except configparser.Error as e:
                raise AnsibleOptionsError("Error reading config file: \n{0}".format(e))
            return p, path
    return None, ''

p, CONFIG_FILE = load_config_file()

# check all of these extensions when looking for yaml files for things like
# group variables -- really anything we can load
YAML_FILENAME_EXTENSIONS = [ "", ".yml", ".yaml", ".json" ]

# the default whitelist for cow stencils
DEFAULT_COW_WHITELIST = ['bud-frogs', 'bunny', 'cheese', 'daemon', 'default', 'dragon', 'elephant-in-snake', 'elephant',
                         'eyes', 'hellokitty', 'kitty', 'luke-koala', 'meow', 'milk', 'moofasa', 'moose', 'ren', 'sheep',
                         'small', 'stegosaurus', 'stimpy', 'supermilker', 'three-eyes', 'turkey', 'turtle', 'tux', 'udder',
                         'vader-koala', 'vader', 'www',]

# sections in config file
DEFAULTS='defaults'

# FIXME: add deprecation warning when these get set
#### DEPRECATED VARS #### 
# use more sanely named 'inventory'
DEPRECATED_HOST_LIST  = get_config(p, DEFAULTS, 'hostfile', 'ANSIBLE_HOSTS', '/etc/ansible/hosts', ispath=True)
# this is not used since 0.5 but people might still have in config
DEFAULT_PATTERN           = get_config(p, DEFAULTS, 'pattern', None, None)

#### GENERALLY CONFIGURABLE THINGS ####
DEFAULT_DEBUG             = get_config(p, DEFAULTS, 'debug',            'ANSIBLE_DEBUG',            False, boolean=True)
DEFAULT_HOST_LIST         = get_config(p, DEFAULTS,'inventory', 'ANSIBLE_INVENTORY', DEPRECATED_HOST_LIST, ispath=True)
DEFAULT_MODULE_PATH       = get_config(p, DEFAULTS, 'library',          'ANSIBLE_LIBRARY',          None, ispath=True)
DEFAULT_ROLES_PATH        = get_config(p, DEFAULTS, 'roles_path',       'ANSIBLE_ROLES_PATH',       '/etc/ansible/roles', ispath=True)
DEFAULT_REMOTE_TMP        = get_config(p, DEFAULTS, 'remote_tmp',       'ANSIBLE_REMOTE_TEMP',      '$HOME/.ansible/tmp')
DEFAULT_MODULE_NAME       = get_config(p, DEFAULTS, 'module_name',      None,                       'command')
DEFAULT_FORKS             = get_config(p, DEFAULTS, 'forks',            'ANSIBLE_FORKS',            5, integer=True)
DEFAULT_MODULE_ARGS       = get_config(p, DEFAULTS, 'module_args',      'ANSIBLE_MODULE_ARGS',      '')
DEFAULT_MODULE_LANG       = get_config(p, DEFAULTS, 'module_lang',      'ANSIBLE_MODULE_LANG',      os.getenv('LANG', 'en_US.UTF-8'))
DEFAULT_TIMEOUT           = get_config(p, DEFAULTS, 'timeout',          'ANSIBLE_TIMEOUT',          10, integer=True)
DEFAULT_POLL_INTERVAL     = get_config(p, DEFAULTS, 'poll_interval',    'ANSIBLE_POLL_INTERVAL',    15, integer=True)
DEFAULT_REMOTE_USER       = get_config(p, DEFAULTS, 'remote_user',      'ANSIBLE_REMOTE_USER',      None)
DEFAULT_ASK_PASS          = get_config(p, DEFAULTS, 'ask_pass',  'ANSIBLE_ASK_PASS',    False, boolean=True)
DEFAULT_PRIVATE_KEY_FILE  = get_config(p, DEFAULTS, 'private_key_file', 'ANSIBLE_PRIVATE_KEY_FILE', None, ispath=True)
DEFAULT_REMOTE_PORT       = get_config(p, DEFAULTS, 'remote_port',      'ANSIBLE_REMOTE_PORT',      None, integer=True)
DEFAULT_ASK_VAULT_PASS    = get_config(p, DEFAULTS, 'ask_vault_pass',    'ANSIBLE_ASK_VAULT_PASS',    False, boolean=True)
DEFAULT_VAULT_PASSWORD_FILE = get_config(p, DEFAULTS, 'vault_password_file', 'ANSIBLE_VAULT_PASSWORD_FILE', None, ispath=True)
DEFAULT_TRANSPORT         = get_config(p, DEFAULTS, 'transport',        'ANSIBLE_TRANSPORT',        'smart')
DEFAULT_SCP_IF_SSH        = get_config(p, 'ssh_connection', 'scp_if_ssh',       'ANSIBLE_SCP_IF_SSH',       False, boolean=True)
DEFAULT_SFTP_BATCH_MODE   = get_config(p, 'ssh_connection', 'sftp_batch_mode', 'ANSIBLE_SFTP_BATCH_MODE', True, boolean=True)
DEFAULT_MANAGED_STR       = get_config(p, DEFAULTS, 'ansible_managed',  None,           'Ansible managed: {file} modified on %Y-%m-%d %H:%M:%S by {uid} on {host}')
DEFAULT_SYSLOG_FACILITY   = get_config(p, DEFAULTS, 'syslog_facility',  'ANSIBLE_SYSLOG_FACILITY', 'LOG_USER')
DEFAULT_KEEP_REMOTE_FILES = get_config(p, DEFAULTS, 'keep_remote_files', 'ANSIBLE_KEEP_REMOTE_FILES', False, boolean=True)
DEFAULT_HASH_BEHAVIOUR    = get_config(p, DEFAULTS, 'hash_behaviour', 'ANSIBLE_HASH_BEHAVIOUR', 'replace')
DEFAULT_PRIVATE_ROLE_VARS = get_config(p, DEFAULTS, 'private_role_vars', 'ANSIBLE_PRIVATE_ROLE_VARS', False, boolean=True)
DEFAULT_JINJA2_EXTENSIONS = get_config(p, DEFAULTS, 'jinja2_extensions', 'ANSIBLE_JINJA2_EXTENSIONS', None)
DEFAULT_EXECUTABLE        = get_config(p, DEFAULTS, 'executable', 'ANSIBLE_EXECUTABLE', '/bin/sh')
DEFAULT_GATHERING         = get_config(p, DEFAULTS, 'gathering', 'ANSIBLE_GATHERING', 'implicit').lower()
DEFAULT_LOG_PATH          = get_config(p, DEFAULTS, 'log_path',           'ANSIBLE_LOG_PATH', '', ispath=True)
DEFAULT_FORCE_HANDLERS    = get_config(p, DEFAULTS, 'force_handlers', 'ANSIBLE_FORCE_HANDLERS', False, boolean=True)
DEFAULT_INVENTORY_IGNORE  = get_config(p, DEFAULTS, 'inventory_ignore_extensions', 'ANSIBLE_INVENTORY_IGNORE', ["~", ".orig", ".bak", ".ini", ".cfg", ".retry", ".pyc", ".pyo"], islist=True)
DEFAULT_VAR_COMPRESSION_LEVEL = get_config(p, DEFAULTS, 'var_compression_level', 'ANSIBLE_VAR_COMPRESSION_LEVEL', 0, integer=True)

# disclosure
DEFAULT_NO_LOG           = get_config(p, DEFAULTS, 'no_log', 'ANSIBLE_NO_LOG', False, boolean=True)
DEFAULT_NO_TARGET_SYSLOG   = get_config(p, DEFAULTS, 'no_target_syslog', 'ANSIBLE_NO_TARGET_SYSLOG', False, boolean=True)

# selinux
DEFAULT_SELINUX_SPECIAL_FS = get_config(p, 'selinux', 'special_context_filesystems', None, 'fuse, nfs, vboxsf, ramfs', islist=True)
DEFAULT_LIBVIRT_LXC_NOSECLABEL = get_config(p, 'selinux', 'libvirt_lxc_noseclabel', 'LIBVIRT_LXC_NOSECLABEL', False, boolean=True)

### PRIVILEGE ESCALATION ###
# Backwards Compat
DEFAULT_SU                = get_config(p, DEFAULTS, 'su', 'ANSIBLE_SU', False, boolean=True)
DEFAULT_SU_USER           = get_config(p, DEFAULTS, 'su_user', 'ANSIBLE_SU_USER', 'root')
DEFAULT_SU_EXE            = get_config(p, DEFAULTS, 'su_exe', 'ANSIBLE_SU_EXE', None)
DEFAULT_SU_FLAGS          = get_config(p, DEFAULTS, 'su_flags', 'ANSIBLE_SU_FLAGS', None)
DEFAULT_ASK_SU_PASS       = get_config(p, DEFAULTS, 'ask_su_pass', 'ANSIBLE_ASK_SU_PASS', False, boolean=True)
DEFAULT_SUDO              = get_config(p, DEFAULTS, 'sudo', 'ANSIBLE_SUDO', False, boolean=True)
DEFAULT_SUDO_USER         = get_config(p, DEFAULTS, 'sudo_user',        'ANSIBLE_SUDO_USER',        'root')
DEFAULT_SUDO_EXE          = get_config(p, DEFAULTS, 'sudo_exe', 'ANSIBLE_SUDO_EXE', None)
DEFAULT_SUDO_FLAGS        = get_config(p, DEFAULTS, 'sudo_flags', 'ANSIBLE_SUDO_FLAGS', '-H -S -n')
DEFAULT_ASK_SUDO_PASS     = get_config(p, DEFAULTS, 'ask_sudo_pass',    'ANSIBLE_ASK_SUDO_PASS',    False, boolean=True)

# Become
BECOME_ERROR_STRINGS      = {'sudo': 'Sorry, try again.', 'su': 'Authentication failure', 'pbrun': '', 'pfexec': '', 'runas': '', 'doas': 'Permission denied'} #FIXME: deal with i18n
BECOME_MISSING_STRINGS    = {'sudo': 'sorry, a password is required to run sudo', 'su': '', 'pbrun': '', 'pfexec': '', 'runas': '', 'doas': 'Authorization required'} #FIXME: deal with i18n
BECOME_METHODS            = ['sudo','su','pbrun','pfexec','runas','doas']
BECOME_ALLOW_SAME_USER    = get_config(p, 'privilege_escalation', 'become_allow_same_user', 'ANSIBLE_BECOME_ALLOW_SAME_USER', False, boolean=True)
DEFAULT_BECOME_METHOD     = get_config(p, 'privilege_escalation', 'become_method', 'ANSIBLE_BECOME_METHOD','sudo' if DEFAULT_SUDO else 'su' if DEFAULT_SU else 'sudo' ).lower()
DEFAULT_BECOME            = get_config(p, 'privilege_escalation', 'become', 'ANSIBLE_BECOME',False, boolean=True)
DEFAULT_BECOME_USER       = get_config(p, 'privilege_escalation', 'become_user', 'ANSIBLE_BECOME_USER', 'root')
DEFAULT_BECOME_EXE        = get_config(p, 'privilege_escalation', 'become_exe', 'ANSIBLE_BECOME_EXE', None)
DEFAULT_BECOME_FLAGS      = get_config(p, 'privilege_escalation', 'become_flags', 'ANSIBLE_BECOME_FLAGS', None)
DEFAULT_BECOME_ASK_PASS   = get_config(p, 'privilege_escalation', 'become_ask_pass', 'ANSIBLE_BECOME_ASK_PASS', False, boolean=True)


# PLUGINS

# Modules that can optimize with_items loops into a single call.  Currently
# these modules must (1) take a "name" or "pkg" parameter that is a list.  If
# the module takes both, bad things could happen.
# In the future we should probably generalize this even further
# (mapping of param: squash field)
DEFAULT_SQUASH_ACTIONS         = get_config(p, DEFAULTS, 'squash_actions',     'ANSIBLE_SQUASH_ACTIONS', "apt, dnf, package, pkgng, yum, zypper", islist=True)
# paths
DEFAULT_ACTION_PLUGIN_PATH     = get_config(p, DEFAULTS, 'action_plugins',     'ANSIBLE_ACTION_PLUGINS', '~/.ansible/plugins/action:/usr/share/ansible/plugins/action', ispath=True)
DEFAULT_CACHE_PLUGIN_PATH      = get_config(p, DEFAULTS, 'cache_plugins',      'ANSIBLE_CACHE_PLUGINS', '~/.ansible/plugins/cache:/usr/share/ansible/plugins/cache', ispath=True)
DEFAULT_CALLBACK_PLUGIN_PATH   = get_config(p, DEFAULTS, 'callback_plugins',   'ANSIBLE_CALLBACK_PLUGINS', '~/.ansible/plugins/callback:/usr/share/ansible/plugins/callback', ispath=True)
DEFAULT_CONNECTION_PLUGIN_PATH = get_config(p, DEFAULTS, 'connection_plugins', 'ANSIBLE_CONNECTION_PLUGINS', '~/.ansible/plugins/connection:/usr/share/ansible/plugins/connection', ispath=True)
DEFAULT_LOOKUP_PLUGIN_PATH     = get_config(p, DEFAULTS, 'lookup_plugins',     'ANSIBLE_LOOKUP_PLUGINS', '~/.ansible/plugins/lookup:/usr/share/ansible/plugins/lookup', ispath=True)
DEFAULT_INVENTORY_PLUGIN_PATH  = get_config(p, DEFAULTS, 'inventory_plugins',  'ANSIBLE_INVENTORY_PLUGINS', '~/.ansible/plugins/inventory:/usr/share/ansible/plugins/inventory', ispath=True)
DEFAULT_VARS_PLUGIN_PATH       = get_config(p, DEFAULTS, 'vars_plugins',       'ANSIBLE_VARS_PLUGINS', '~/.ansible/plugins/vars:/usr/share/ansible/plugins/vars', ispath=True)
DEFAULT_FILTER_PLUGIN_PATH     = get_config(p, DEFAULTS, 'filter_plugins',     'ANSIBLE_FILTER_PLUGINS', '~/.ansible/plugins/filter:/usr/share/ansible/plugins/filter', ispath=True)
DEFAULT_TEST_PLUGIN_PATH       = get_config(p, DEFAULTS, 'test_plugins',       'ANSIBLE_TEST_PLUGINS', '~/.ansible/plugins/test:/usr/share/ansible/plugins/test', ispath=True)
DEFAULT_STRATEGY_PLUGIN_PATH   = get_config(p, DEFAULTS, 'strategy_plugins',   'ANSIBLE_STRATEGY_PLUGINS', '~/.ansible/plugins/strategy:/usr/share/ansible/plugins/strategy', ispath=True)
DEFAULT_STDOUT_CALLBACK        = get_config(p, DEFAULTS, 'stdout_callback',    'ANSIBLE_STDOUT_CALLBACK', 'default')
# cache
CACHE_PLUGIN                   = get_config(p, DEFAULTS, 'fact_caching', 'ANSIBLE_CACHE_PLUGIN', 'memory')
CACHE_PLUGIN_CONNECTION        = get_config(p, DEFAULTS, 'fact_caching_connection', 'ANSIBLE_CACHE_PLUGIN_CONNECTION', None)
CACHE_PLUGIN_PREFIX            = get_config(p, DEFAULTS, 'fact_caching_prefix', 'ANSIBLE_CACHE_PLUGIN_PREFIX', 'ansible_facts')
CACHE_PLUGIN_TIMEOUT           = get_config(p, DEFAULTS, 'fact_caching_timeout', 'ANSIBLE_CACHE_PLUGIN_TIMEOUT', 24 * 60 * 60, integer=True)

# Display
ANSIBLE_FORCE_COLOR            = get_config(p, DEFAULTS, 'force_color', 'ANSIBLE_FORCE_COLOR', None, boolean=True)
ANSIBLE_NOCOLOR                = get_config(p, DEFAULTS, 'nocolor', 'ANSIBLE_NOCOLOR', None, boolean=True)
ANSIBLE_NOCOWS                 = get_config(p, DEFAULTS, 'nocows', 'ANSIBLE_NOCOWS', None, boolean=True)
ANSIBLE_COW_SELECTION          = get_config(p, DEFAULTS, 'cow_selection', 'ANSIBLE_COW_SELECTION', 'default')
ANSIBLE_COW_WHITELIST          = get_config(p, DEFAULTS, 'cow_whitelist', 'ANSIBLE_COW_WHITELIST', DEFAULT_COW_WHITELIST, islist=True)
DISPLAY_ARGS_TO_STDOUT         = get_config(p, DEFAULTS, 'display_args_to_stdout', 'DISPLAY_ARGS_TO_STDOUT', False, boolean=True)
DISPLAY_SKIPPED_HOSTS          = get_config(p, DEFAULTS, 'display_skipped_hosts', 'DISPLAY_SKIPPED_HOSTS', True, boolean=True)
DEFAULT_UNDEFINED_VAR_BEHAVIOR = get_config(p, DEFAULTS, 'error_on_undefined_vars', 'ANSIBLE_ERROR_ON_UNDEFINED_VARS', True, boolean=True)
HOST_KEY_CHECKING              = get_config(p, DEFAULTS, 'host_key_checking',  'ANSIBLE_HOST_KEY_CHECKING',    True, boolean=True)
SYSTEM_WARNINGS                = get_config(p, DEFAULTS, 'system_warnings', 'ANSIBLE_SYSTEM_WARNINGS', True, boolean=True)
DEPRECATION_WARNINGS           = get_config(p, DEFAULTS, 'deprecation_warnings', 'ANSIBLE_DEPRECATION_WARNINGS', True, boolean=True)
DEFAULT_CALLABLE_WHITELIST     = get_config(p, DEFAULTS, 'callable_whitelist', 'ANSIBLE_CALLABLE_WHITELIST', [], islist=True)
COMMAND_WARNINGS               = get_config(p, DEFAULTS, 'command_warnings', 'ANSIBLE_COMMAND_WARNINGS', True, boolean=True)
DEFAULT_LOAD_CALLBACK_PLUGINS  = get_config(p, DEFAULTS, 'bin_ansible_callbacks', 'ANSIBLE_LOAD_CALLBACK_PLUGINS', False, boolean=True)
DEFAULT_CALLBACK_WHITELIST     = get_config(p, DEFAULTS, 'callback_whitelist', 'ANSIBLE_CALLBACK_WHITELIST', [], islist=True)
RETRY_FILES_ENABLED            = get_config(p, DEFAULTS, 'retry_files_enabled', 'ANSIBLE_RETRY_FILES_ENABLED', True, boolean=True)
RETRY_FILES_SAVE_PATH          = get_config(p, DEFAULTS, 'retry_files_save_path', 'ANSIBLE_RETRY_FILES_SAVE_PATH', None, ispath=True)
DEFAULT_NULL_REPRESENTATION    = get_config(p, DEFAULTS, 'null_representation', 'ANSIBLE_NULL_REPRESENTATION', None, isnone=True)
DISPLAY_ARGS_TO_STDOUT         = get_config(p, DEFAULTS, 'display_args_to_stdout', 'ANSIBLE_DISPLAY_ARGS_TO_STDOUT', False, boolean=True)
MAX_FILE_SIZE_FOR_DIFF         = get_config(p, DEFAULTS, 'max_diff_size', 'ANSIBLE_MAX_DIFF_SIZE', 1024*1024, integer=True)

# CONNECTION RELATED
ANSIBLE_SSH_ARGS               = get_config(p, 'ssh_connection', 'ssh_args', 'ANSIBLE_SSH_ARGS', '-o ControlMaster=auto -o ControlPersist=60s')
ANSIBLE_SSH_CONTROL_PATH       = get_config(p, 'ssh_connection', 'control_path', 'ANSIBLE_SSH_CONTROL_PATH', "%(directory)s/ansible-ssh-%%h-%%p-%%r")
ANSIBLE_SSH_PIPELINING         = get_config(p, 'ssh_connection', 'pipelining', 'ANSIBLE_SSH_PIPELINING', False, boolean=True)
ANSIBLE_SSH_RETRIES            = get_config(p, 'ssh_connection', 'retries', 'ANSIBLE_SSH_RETRIES', 0, integer=True)
PARAMIKO_RECORD_HOST_KEYS      = get_config(p, 'paramiko_connection', 'record_host_keys', 'ANSIBLE_PARAMIKO_RECORD_HOST_KEYS', True, boolean=True)
PARAMIKO_PROXY_COMMAND         = get_config(p, 'paramiko_connection', 'proxy_command', 'ANSIBLE_PARAMIKO_PROXY_COMMAND', None)


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

# galaxy related
GALAXY_SERVER                  = get_config(p, 'galaxy', 'server', 'ANSIBLE_GALAXY_SERVER', 'https://galaxy.ansible.com')
GALAXY_IGNORE_CERTS            = get_config(p, 'galaxy', 'ignore_certs', 'ANSIBLE_GALAXY_IGNORE', False, boolean=True)
# this can be configured to blacklist SCMS but cannot add new ones unless the code is also updated
GALAXY_SCMS                    = get_config(p, 'galaxy', 'scms', 'ANSIBLE_GALAXY_SCMS', 'git, hg', islist=True)

# characters included in auto-generated passwords
DEFAULT_PASSWORD_CHARS = ascii_letters + digits + ".,:-_"
STRING_TYPE_FILTERS = get_config(p, 'jinja2', 'dont_type_filters', 'ANSIBLE_STRING_TYPE_FILTERS', ['string', 'to_json', 'to_nice_json', 'to_yaml', 'ppretty', 'json'], islist=True )

# colors
COLOR_HIGHLIGHT   = get_config(p, 'colors', 'highlight', 'ANSIBLE_COLOR_HIGHLIGHT', 'white')
COLOR_VERBOSE     = get_config(p, 'colors', 'verbose', 'ANSIBLE_COLOR_VERBOSE', 'blue')
COLOR_WARN        = get_config(p, 'colors', 'warn', 'ANSIBLE_COLOR_WARN', 'bright purple')
COLOR_ERROR       = get_config(p, 'colors', 'error', 'ANSIBLE_COLOR_ERROR', 'red')
COLOR_DEBUG       = get_config(p, 'colors', 'debug', 'ANSIBLE_COLOR_DEBUG', 'dark gray')
COLOR_DEPRECATE   = get_config(p, 'colors', 'deprecate', 'ANSIBLE_COLOR_DEPRECATE', 'purple')
COLOR_SKIP        = get_config(p, 'colors', 'skip', 'ANSIBLE_COLOR_SKIP', 'cyan')
COLOR_UNREACHABLE = get_config(p, 'colors', 'unreachable', 'ANSIBLE_COLOR_UNREACHABLE', 'bright red')
COLOR_OK          = get_config(p, 'colors', 'ok', 'ANSIBLE_COLOR_OK', 'green')
COLOR_CHANGED     = get_config(p, 'colors', 'ok', 'ANSIBLE_COLOR_CHANGED', 'yellow')
COLOR_DIFF_ADD    = get_config(p, 'colors', 'diff_add', 'ANSIBLE_COLOR_DIFF_ADD', 'green')
COLOR_DIFF_REMOVE = get_config(p, 'colors', 'diff_remove', 'ANSIBLE_COLOR_DIFF_REMOVE', 'red')
COLOR_DIFF_LINES  = get_config(p, 'colors', 'diff_lines', 'ANSIBLE_COLOR_DIFF_LINES', 'cyan')

# diff
DIFF_CONTEXT = get_config(p, 'diff', 'context', 'ANSIBLE_DIFF_CONTEXT', 3, integer=True)

# non-configurable things
MODULE_REQUIRE_ARGS       = ['command', 'shell', 'raw', 'script']
MODULE_NO_JSON            = ['command', 'shell', 'raw']
DEFAULT_BECOME_PASS       = None
DEFAULT_SUDO_PASS         = None
DEFAULT_REMOTE_PASS       = None
DEFAULT_SUBSET            = None
DEFAULT_SU_PASS           = None
VAULT_VERSION_MIN         = 1.0
VAULT_VERSION_MAX         = 1.0
TREE_DIR                  = None
LOCALHOST                 = frozenset(['127.0.0.1', 'localhost', '::1'])
# module search
BLACKLIST_EXTS = ('.pyc', '.swp', '.bak', '~', '.rpm', '.md', '.txt')
IGNORE_FILES = [ "COPYING", "CONTRIBUTING", "LICENSE", "README", "VERSION", "GUIDELINES", "test-docs.sh"]
