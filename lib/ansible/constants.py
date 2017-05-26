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
import tempfile
from string import ascii_letters, digits

from ansible.compat.six import string_types
from ansible.compat.six.moves import configparser
from ansible.errors import AnsibleOptionsError
from ansible.module_utils._text import to_text
from ansible.parsing.quoting import unquote
from ansible.utils.path import makedirs_safe

BOOL_TRUE = frozenset([ "true", "t", "y", "1", "yes", "on" ])

def mk_boolean(value):
    ret = value
    if not isinstance(value, bool):
        if value is None:
            ret = False
        ret = (str(value).lower() in BOOL_TRUE)
    return ret

def shell_expand(path, expand_relative_paths=False):
    '''
    shell_expand is needed as os.path.expanduser does not work
    when path is None, which is the default for ANSIBLE_PRIVATE_KEY_FILE
    '''
    if path:
        path = os.path.expanduser(os.path.expandvars(path))
        if expand_relative_paths and not path.startswith('/'):
            # paths are always 'relative' to the config?
            if 'CONFIG_FILE' in globals():
                CFGDIR = os.path.dirname(CONFIG_FILE)
                path = os.path.join(CFGDIR, path)
            path = os.path.abspath(path)
    return path

def get_config(p, section, key, env_var, default, value_type=None, expand_relative_paths=False):
    ''' return a configuration variable with casting

    :arg p: A ConfigParser object to look for the configuration in
    :arg section: A section of the ini config that should be examined for this section.
    :arg key: The config key to get this config from
    :arg env_var: An Environment variable to check for the config var.  If
        this is set to None then no environment variable will be used.
    :arg default: A default value to assign to the config var if nothing else sets it.
    :kwarg value_type: The type of the value.  This can be any of the following strings:
        :boolean: sets the value to a True or False value
        :integer: Sets the value to an integer or raises a ValueType error
        :float: Sets the value to a float or raises a ValueType error
        :list: Treats the value as a comma separated list.  Split the value
            and return it as a python list.
        :none: Sets the value to None
        :path: Expands any environment variables and tilde's in the value.
        :tmp_path: Create a unique temporary directory inside of the directory
            specified by value and return its path.
        :pathlist: Treat the value as a typical PATH string.  (On POSIX, this
            means colon separated strings.)  Split the value and then expand
            each part for environment variables and tildes.
    :kwarg expand_relative_paths: for pathlist and path types, if this is set
        to True then also change any relative paths into absolute paths.  The
        default is False.
    '''
    value = _get_config(p, section, key, env_var, default)
    if value_type == 'boolean':
        value = mk_boolean(value)

    elif value:
        if value_type == 'integer':
            value = int(value)

        elif value_type == 'float':
            value = float(value)

        elif value_type == 'list':
            if isinstance(value, string_types):
                value = [x.strip() for x in value.split(',')]

        elif value_type == 'none':
            if value == "None":
                value = None

        elif value_type == 'path':
            value = shell_expand(value, expand_relative_paths=expand_relative_paths)

        elif value_type == 'tmppath':
            value = shell_expand(value)
            if not os.path.exists(value):
                makedirs_safe(value, 0o700)
            prefix = 'ansible-local-%s' % os.getpid()
            value = tempfile.mkdtemp(prefix=prefix, dir=value)

        elif value_type == 'pathlist':
            if isinstance(value, string_types):
                value = [shell_expand(x, expand_relative_paths=expand_relative_paths) \
                         for x in value.split(os.pathsep)]

        elif isinstance(value, string_types):
            value = unquote(value)

    return to_text(value, errors='surrogate_or_strict', nonstring='passthru')


def _get_config(p, section, key, env_var, default):
    ''' helper function for get_config '''
    value = default

    if p is not None:
        try:
            value = p.get(section, key, raw=True)
        except:
            pass

    if env_var is not None:
        env_value = os.environ.get(env_var, None)
        if env_value is not None:
            value = env_value

    return to_text(value, errors='surrogate_or_strict', nonstring='passthru')


def load_config_file():
    ''' Load Config File order(first found is used): ENV, CWD, HOME, /etc/ansible '''

    p = configparser.ConfigParser()

    path0 = os.getenv("ANSIBLE_CONFIG", None)
    if path0 is not None:
        path0 = os.path.expanduser(path0)
        if os.path.isdir(path0):
            path0 += "/ansible.cfg"
    try:
        path1 = os.getcwd() + "/ansible.cfg"
    except OSError:
        path1 = None
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
DEPRECATED_HOST_LIST  = get_config(p, DEFAULTS, 'hostfile', 'ANSIBLE_HOSTS', '/etc/ansible/hosts', value_type='path')
# this is not used since 0.5 but people might still have in config
DEFAULT_PATTERN           = get_config(p, DEFAULTS, 'pattern', None, None)
# If --tags or --skip-tags is given multiple times on the CLI and this is
# True, merge the lists of tags together.  If False, let the last argument
# overwrite any previous ones.  Behaviour is overwrite through 2.2.  2.3
# overwrites but prints deprecation.  2.4 the default is to merge.
MERGE_MULTIPLE_CLI_TAGS = get_config(p, DEFAULTS, 'merge_multiple_cli_tags', 'ANSIBLE_MERGE_MULTIPLE_CLI_TAGS', False, value_type='boolean')

#### GENERALLY CONFIGURABLE THINGS ####
DEFAULT_DEBUG             = get_config(p, DEFAULTS, 'debug',            'ANSIBLE_DEBUG',            False, value_type='boolean')
DEFAULT_VERBOSITY         = get_config(p, DEFAULTS, 'verbosity',        'ANSIBLE_VERBOSITY',        0, value_type='integer')
DEFAULT_HOST_LIST         = get_config(p, DEFAULTS,'inventory', 'ANSIBLE_INVENTORY', DEPRECATED_HOST_LIST, value_type='path')
DEFAULT_ROLES_PATH        = get_config(p, DEFAULTS, 'roles_path',       'ANSIBLE_ROLES_PATH',       '/etc/ansible/roles', value_type='pathlist', expand_relative_paths=True)
DEFAULT_REMOTE_TMP        = get_config(p, DEFAULTS, 'remote_tmp',       'ANSIBLE_REMOTE_TEMP',      '~/.ansible/tmp')
DEFAULT_LOCAL_TMP         = get_config(p, DEFAULTS, 'local_tmp',        'ANSIBLE_LOCAL_TEMP',      '~/.ansible/tmp', value_type='tmppath')
DEFAULT_MODULE_NAME       = get_config(p, DEFAULTS, 'module_name',      None,                       'command')
DEFAULT_FACT_PATH         = get_config(p, DEFAULTS, 'fact_path',        'ANSIBLE_FACT_PATH', None, value_type='path')
DEFAULT_FORKS             = get_config(p, DEFAULTS, 'forks',            'ANSIBLE_FORKS',            5, value_type='integer')
DEFAULT_MODULE_ARGS       = get_config(p, DEFAULTS, 'module_args',      'ANSIBLE_MODULE_ARGS',      '')
DEFAULT_MODULE_LANG       = get_config(p, DEFAULTS, 'module_lang',      'ANSIBLE_MODULE_LANG',      os.getenv('LANG', 'en_US.UTF-8'))
DEFAULT_MODULE_SET_LOCALE = get_config(p, DEFAULTS, 'module_set_locale','ANSIBLE_MODULE_SET_LOCALE',False, value_type='boolean')
DEFAULT_MODULE_COMPRESSION= get_config(p, DEFAULTS, 'module_compression', None, 'ZIP_DEFLATED')
DEFAULT_TIMEOUT           = get_config(p, DEFAULTS, 'timeout',          'ANSIBLE_TIMEOUT',          10, value_type='integer')
DEFAULT_POLL_INTERVAL     = get_config(p, DEFAULTS, 'poll_interval',    'ANSIBLE_POLL_INTERVAL',    15, value_type='integer')
DEFAULT_REMOTE_USER       = get_config(p, DEFAULTS, 'remote_user',      'ANSIBLE_REMOTE_USER',      None)
DEFAULT_ASK_PASS          = get_config(p, DEFAULTS, 'ask_pass',  'ANSIBLE_ASK_PASS',    False, value_type='boolean')
DEFAULT_PRIVATE_KEY_FILE  = get_config(p, DEFAULTS, 'private_key_file', 'ANSIBLE_PRIVATE_KEY_FILE', None, value_type='path')
DEFAULT_REMOTE_PORT       = get_config(p, DEFAULTS, 'remote_port',      'ANSIBLE_REMOTE_PORT',      None, value_type='integer')
DEFAULT_ASK_VAULT_PASS    = get_config(p, DEFAULTS, 'ask_vault_pass',    'ANSIBLE_ASK_VAULT_PASS',    False, value_type='boolean')
DEFAULT_VAULT_PASSWORD_FILE = get_config(p, DEFAULTS, 'vault_password_file', 'ANSIBLE_VAULT_PASSWORD_FILE', None, value_type='path')
DEFAULT_TRANSPORT         = get_config(p, DEFAULTS, 'transport',        'ANSIBLE_TRANSPORT',        'smart')
DEFAULT_SCP_IF_SSH        = get_config(p, 'ssh_connection', 'scp_if_ssh',       'ANSIBLE_SCP_IF_SSH',       'smart')
DEFAULT_SFTP_BATCH_MODE   = get_config(p, 'ssh_connection', 'sftp_batch_mode', 'ANSIBLE_SFTP_BATCH_MODE', True, value_type='boolean')
DEFAULT_SSH_TRANSFER_METHOD = get_config(p, 'ssh_connection', 'transfer_method', 'ANSIBLE_SSH_TRANSFER_METHOD', None)
DEFAULT_MANAGED_STR       = get_config(p, DEFAULTS, 'ansible_managed',  None,           'Ansible managed')
DEFAULT_SYSLOG_FACILITY   = get_config(p, DEFAULTS, 'syslog_facility',  'ANSIBLE_SYSLOG_FACILITY', 'LOG_USER')
DEFAULT_KEEP_REMOTE_FILES = get_config(p, DEFAULTS, 'keep_remote_files', 'ANSIBLE_KEEP_REMOTE_FILES', False, value_type='boolean')
DEFAULT_HASH_BEHAVIOUR    = get_config(p, DEFAULTS, 'hash_behaviour', 'ANSIBLE_HASH_BEHAVIOUR', 'replace')
DEFAULT_PRIVATE_ROLE_VARS = get_config(p, DEFAULTS, 'private_role_vars', 'ANSIBLE_PRIVATE_ROLE_VARS', False, value_type='boolean')
DEFAULT_JINJA2_EXTENSIONS = get_config(p, DEFAULTS, 'jinja2_extensions', 'ANSIBLE_JINJA2_EXTENSIONS', None)
DEFAULT_EXECUTABLE        = get_config(p, DEFAULTS, 'executable', 'ANSIBLE_EXECUTABLE', '/bin/sh')
DEFAULT_GATHERING         = get_config(p, DEFAULTS, 'gathering', 'ANSIBLE_GATHERING', 'implicit').lower()
DEFAULT_GATHER_SUBSET     = get_config(p, DEFAULTS, 'gather_subset', 'ANSIBLE_GATHER_SUBSET', 'all').lower()
DEFAULT_GATHER_TIMEOUT    = get_config(p, DEFAULTS, 'gather_timeout', 'ANSIBLE_GATHER_TIMEOUT', 10, value_type='integer')
DEFAULT_LOG_PATH          = get_config(p, DEFAULTS, 'log_path',           'ANSIBLE_LOG_PATH', '', value_type='path')
DEFAULT_FORCE_HANDLERS    = get_config(p, DEFAULTS, 'force_handlers', 'ANSIBLE_FORCE_HANDLERS', False, value_type='boolean')
DEFAULT_INVENTORY_IGNORE  = get_config(p, DEFAULTS, 'inventory_ignore_extensions', 'ANSIBLE_INVENTORY_IGNORE', ["~", ".orig", ".bak", ".ini", ".cfg", ".retry", ".pyc", ".pyo"], value_type='list')
DEFAULT_VAR_COMPRESSION_LEVEL = get_config(p, DEFAULTS, 'var_compression_level', 'ANSIBLE_VAR_COMPRESSION_LEVEL', 0, value_type='integer')
DEFAULT_INTERNAL_POLL_INTERVAL = get_config(p, DEFAULTS, 'internal_poll_interval', None, 0.001, value_type='float')
DEFAULT_ALLOW_UNSAFE_LOOKUPS = get_config(p, DEFAULTS, 'allow_unsafe_lookups', None, False, value_type='boolean')
ERROR_ON_MISSING_HANDLER  = get_config(p, DEFAULTS, 'error_on_missing_handler', 'ANSIBLE_ERROR_ON_MISSING_HANDLER', True, value_type='boolean')
SHOW_CUSTOM_STATS = get_config(p, DEFAULTS, 'show_custom_stats', 'ANSIBLE_SHOW_CUSTOM_STATS', False, value_type='boolean')

# static includes
DEFAULT_TASK_INCLUDES_STATIC    = get_config(p, DEFAULTS, 'task_includes_static', 'ANSIBLE_TASK_INCLUDES_STATIC', False, value_type='boolean')
DEFAULT_HANDLER_INCLUDES_STATIC = get_config(p, DEFAULTS, 'handler_includes_static', 'ANSIBLE_HANDLER_INCLUDES_STATIC', False, value_type='boolean')

# disclosure
DEFAULT_NO_LOG           = get_config(p, DEFAULTS, 'no_log', 'ANSIBLE_NO_LOG', False, value_type='boolean')
DEFAULT_NO_TARGET_SYSLOG   = get_config(p, DEFAULTS, 'no_target_syslog', 'ANSIBLE_NO_TARGET_SYSLOG', False, value_type='boolean')
ALLOW_WORLD_READABLE_TMPFILES = get_config(p, DEFAULTS, 'allow_world_readable_tmpfiles', None, False, value_type='boolean')

# selinux
DEFAULT_SELINUX_SPECIAL_FS = get_config(p, 'selinux', 'special_context_filesystems', None, 'fuse, nfs, vboxsf, ramfs, 9p', value_type='list')
DEFAULT_LIBVIRT_LXC_NOSECLABEL = get_config(p, 'selinux', 'libvirt_lxc_noseclabel', 'LIBVIRT_LXC_NOSECLABEL', False, value_type='boolean')

### PRIVILEGE ESCALATION ###
# Backwards Compat
DEFAULT_SU                = get_config(p, DEFAULTS, 'su', 'ANSIBLE_SU', False, value_type='boolean')
DEFAULT_SU_USER           = get_config(p, DEFAULTS, 'su_user', 'ANSIBLE_SU_USER', 'root')
DEFAULT_SU_EXE            = get_config(p, DEFAULTS, 'su_exe', 'ANSIBLE_SU_EXE', None)
DEFAULT_SU_FLAGS          = get_config(p, DEFAULTS, 'su_flags', 'ANSIBLE_SU_FLAGS', None)
DEFAULT_ASK_SU_PASS       = get_config(p, DEFAULTS, 'ask_su_pass', 'ANSIBLE_ASK_SU_PASS', False, value_type='boolean')
DEFAULT_SUDO              = get_config(p, DEFAULTS, 'sudo', 'ANSIBLE_SUDO', False, value_type='boolean')
DEFAULT_SUDO_USER         = get_config(p, DEFAULTS, 'sudo_user',        'ANSIBLE_SUDO_USER',        'root')
DEFAULT_SUDO_EXE          = get_config(p, DEFAULTS, 'sudo_exe', 'ANSIBLE_SUDO_EXE', None)
DEFAULT_SUDO_FLAGS        = get_config(p, DEFAULTS, 'sudo_flags', 'ANSIBLE_SUDO_FLAGS', '-H -S -n')
DEFAULT_ASK_SUDO_PASS     = get_config(p, DEFAULTS, 'ask_sudo_pass',    'ANSIBLE_ASK_SUDO_PASS',    False, value_type='boolean')

# Become
BECOME_ERROR_STRINGS      = {'sudo': 'Sorry, try again.', 'su': 'Authentication failure', 'pbrun': '', 'pfexec': '', 'doas': 'Permission denied', 'dzdo': '', 'ksu': 'Password incorrect'} #FIXME: deal with i18n
BECOME_MISSING_STRINGS    = {'sudo': 'sorry, a password is required to run sudo', 'su': '', 'pbrun': '', 'pfexec': '', 'doas': 'Authorization required', 'dzdo': '', 'ksu': 'No password given'} #FIXME: deal with i18n
BECOME_METHODS            = ['sudo','su','pbrun','pfexec','doas','dzdo','ksu','runas']
BECOME_ALLOW_SAME_USER    = get_config(p, 'privilege_escalation', 'become_allow_same_user', 'ANSIBLE_BECOME_ALLOW_SAME_USER', False, value_type='boolean')
DEFAULT_BECOME_METHOD     = get_config(p, 'privilege_escalation', 'become_method', 'ANSIBLE_BECOME_METHOD','sudo' if DEFAULT_SUDO else 'su' if DEFAULT_SU else 'sudo' ).lower()
DEFAULT_BECOME            = get_config(p, 'privilege_escalation', 'become', 'ANSIBLE_BECOME',False, value_type='boolean')
DEFAULT_BECOME_USER       = get_config(p, 'privilege_escalation', 'become_user', 'ANSIBLE_BECOME_USER', 'root')
DEFAULT_BECOME_EXE        = get_config(p, 'privilege_escalation', 'become_exe', 'ANSIBLE_BECOME_EXE', None)
DEFAULT_BECOME_FLAGS      = get_config(p, 'privilege_escalation', 'become_flags', 'ANSIBLE_BECOME_FLAGS', None)
DEFAULT_BECOME_ASK_PASS   = get_config(p, 'privilege_escalation', 'become_ask_pass', 'ANSIBLE_BECOME_ASK_PASS', False, value_type='boolean')


# PLUGINS

# Modules that can optimize with_items loops into a single call.  Currently
# these modules must (1) take a "name" or "pkg" parameter that is a list.  If
# the module takes both, bad things could happen.
# In the future we should probably generalize this even further
# (mapping of param: squash field)
DEFAULT_SQUASH_ACTIONS         = get_config(p, DEFAULTS, 'squash_actions',     'ANSIBLE_SQUASH_ACTIONS', "apk, apt, dnf, homebrew, openbsd_pkg, pacman, pkgng, yum, zypper", value_type='list')
# paths

DEFAULT_ACTION_PLUGIN_PATH     = get_config(p, DEFAULTS, 'action_plugins',     'ANSIBLE_ACTION_PLUGINS', '~/.ansible/plugins/action:/usr/share/ansible/plugins/action', value_type='pathlist')
DEFAULT_CACHE_PLUGIN_PATH      = get_config(p, DEFAULTS, 'cache_plugins',      'ANSIBLE_CACHE_PLUGINS', '~/.ansible/plugins/cache:/usr/share/ansible/plugins/cache', value_type='pathlist')
DEFAULT_CALLBACK_PLUGIN_PATH   = get_config(p, DEFAULTS, 'callback_plugins',   'ANSIBLE_CALLBACK_PLUGINS', '~/.ansible/plugins/callback:/usr/share/ansible/plugins/callback', value_type='pathlist')
DEFAULT_CONNECTION_PLUGIN_PATH = get_config(p, DEFAULTS, 'connection_plugins', 'ANSIBLE_CONNECTION_PLUGINS', '~/.ansible/plugins/connection:/usr/share/ansible/plugins/connection', value_type='pathlist')
DEFAULT_LOOKUP_PLUGIN_PATH     = get_config(p, DEFAULTS, 'lookup_plugins',     'ANSIBLE_LOOKUP_PLUGINS', '~/.ansible/plugins/lookup:/usr/share/ansible/plugins/lookup', value_type='pathlist')
DEFAULT_MODULE_PATH            = get_config(p, DEFAULTS, 'library',            'ANSIBLE_LIBRARY',        None, value_type='pathlist')
DEFAULT_MODULE_UTILS_PATH      = get_config(p, DEFAULTS, 'module_utils',       'ANSIBLE_MODULE_UTILS',   None, value_type='pathlist')
DEFAULT_INVENTORY_PLUGIN_PATH  = get_config(p, DEFAULTS, 'inventory_plugins',  'ANSIBLE_INVENTORY_PLUGINS', '~/.ansible/plugins/inventory:/usr/share/ansible/plugins/inventory', value_type='pathlist')
DEFAULT_VARS_PLUGIN_PATH       = get_config(p, DEFAULTS, 'vars_plugins',       'ANSIBLE_VARS_PLUGINS', '~/.ansible/plugins/vars:/usr/share/ansible/plugins/vars', value_type='pathlist')
DEFAULT_FILTER_PLUGIN_PATH     = get_config(p, DEFAULTS, 'filter_plugins',     'ANSIBLE_FILTER_PLUGINS', '~/.ansible/plugins/filter:/usr/share/ansible/plugins/filter', value_type='pathlist')
DEFAULT_TEST_PLUGIN_PATH       = get_config(p, DEFAULTS, 'test_plugins',       'ANSIBLE_TEST_PLUGINS', '~/.ansible/plugins/test:/usr/share/ansible/plugins/test', value_type='pathlist')
DEFAULT_STRATEGY_PLUGIN_PATH   = get_config(p, DEFAULTS, 'strategy_plugins',   'ANSIBLE_STRATEGY_PLUGINS', '~/.ansible/plugins/strategy:/usr/share/ansible/plugins/strategy', value_type='pathlist')

NETWORK_GROUP_MODULES          = get_config(p, DEFAULTS, 'network_group_modules','NETWORK_GROUP_MODULES', ['eos', 'nxos', 'ios', 'iosxr', 'junos',
                                                                                                           'vyos', 'sros', 'dellos9', 'dellos10', 'dellos6'],
                                            value_type='list')

DEFAULT_STRATEGY               = get_config(p, DEFAULTS, 'strategy',           'ANSIBLE_STRATEGY', 'linear')
DEFAULT_STDOUT_CALLBACK        = get_config(p, DEFAULTS, 'stdout_callback',    'ANSIBLE_STDOUT_CALLBACK', 'default')
# cache
CACHE_PLUGIN                   = get_config(p, DEFAULTS, 'fact_caching', 'ANSIBLE_CACHE_PLUGIN', 'memory')
CACHE_PLUGIN_CONNECTION        = get_config(p, DEFAULTS, 'fact_caching_connection', 'ANSIBLE_CACHE_PLUGIN_CONNECTION', None)
CACHE_PLUGIN_PREFIX            = get_config(p, DEFAULTS, 'fact_caching_prefix', 'ANSIBLE_CACHE_PLUGIN_PREFIX', 'ansible_facts')
CACHE_PLUGIN_TIMEOUT           = get_config(p, DEFAULTS, 'fact_caching_timeout', 'ANSIBLE_CACHE_PLUGIN_TIMEOUT', 24 * 60 * 60, value_type='integer')

# Display
ANSIBLE_FORCE_COLOR            = get_config(p, DEFAULTS, 'force_color', 'ANSIBLE_FORCE_COLOR', None, value_type='boolean')
ANSIBLE_NOCOLOR                = get_config(p, DEFAULTS, 'nocolor', 'ANSIBLE_NOCOLOR', None, value_type='boolean')
ANSIBLE_NOCOWS                 = get_config(p, DEFAULTS, 'nocows', 'ANSIBLE_NOCOWS', None, value_type='boolean')
ANSIBLE_COW_SELECTION          = get_config(p, DEFAULTS, 'cow_selection', 'ANSIBLE_COW_SELECTION', 'default')
ANSIBLE_COW_WHITELIST          = get_config(p, DEFAULTS, 'cow_whitelist', 'ANSIBLE_COW_WHITELIST', DEFAULT_COW_WHITELIST, value_type='list')
DISPLAY_SKIPPED_HOSTS          = get_config(p, DEFAULTS, 'display_skipped_hosts', 'DISPLAY_SKIPPED_HOSTS', True, value_type='boolean')
DEFAULT_UNDEFINED_VAR_BEHAVIOR = get_config(p, DEFAULTS, 'error_on_undefined_vars', 'ANSIBLE_ERROR_ON_UNDEFINED_VARS', True, value_type='boolean')
HOST_KEY_CHECKING              = get_config(p, DEFAULTS, 'host_key_checking',  'ANSIBLE_HOST_KEY_CHECKING',    True, value_type='boolean')
SYSTEM_WARNINGS                = get_config(p, DEFAULTS, 'system_warnings', 'ANSIBLE_SYSTEM_WARNINGS', True, value_type='boolean')
DEPRECATION_WARNINGS           = get_config(p, DEFAULTS, 'deprecation_warnings', 'ANSIBLE_DEPRECATION_WARNINGS', True, value_type='boolean')
DEFAULT_CALLABLE_WHITELIST     = get_config(p, DEFAULTS, 'callable_whitelist', 'ANSIBLE_CALLABLE_WHITELIST', [], value_type='list')
COMMAND_WARNINGS               = get_config(p, DEFAULTS, 'command_warnings', 'ANSIBLE_COMMAND_WARNINGS', True, value_type='boolean')
DEFAULT_LOAD_CALLBACK_PLUGINS  = get_config(p, DEFAULTS, 'bin_ansible_callbacks', 'ANSIBLE_LOAD_CALLBACK_PLUGINS', False, value_type='boolean')
DEFAULT_CALLBACK_WHITELIST     = get_config(p, DEFAULTS, 'callback_whitelist', 'ANSIBLE_CALLBACK_WHITELIST', [], value_type='list')
RETRY_FILES_ENABLED            = get_config(p, DEFAULTS, 'retry_files_enabled', 'ANSIBLE_RETRY_FILES_ENABLED', True, value_type='boolean')
RETRY_FILES_SAVE_PATH          = get_config(p, DEFAULTS, 'retry_files_save_path', 'ANSIBLE_RETRY_FILES_SAVE_PATH', None, value_type='path')
DEFAULT_NULL_REPRESENTATION    = get_config(p, DEFAULTS, 'null_representation', 'ANSIBLE_NULL_REPRESENTATION', None, value_type='none')
DISPLAY_ARGS_TO_STDOUT         = get_config(p, DEFAULTS, 'display_args_to_stdout', 'ANSIBLE_DISPLAY_ARGS_TO_STDOUT', False, value_type='boolean')
MAX_FILE_SIZE_FOR_DIFF         = get_config(p, DEFAULTS, 'max_diff_size', 'ANSIBLE_MAX_DIFF_SIZE', 1024*1024, value_type='integer')

# CONNECTION RELATED
USE_PERSISTENT_CONNECTIONS     = get_config(p, DEFAULTS, 'use_persistent_connections', 'ANSIBLE_USE_PERSISTENT_CONNECTIONS', False, value_type='boolean')
ANSIBLE_SSH_ARGS               = get_config(p, 'ssh_connection', 'ssh_args', 'ANSIBLE_SSH_ARGS', '-C -o ControlMaster=auto -o ControlPersist=60s')
### WARNING: Someone might be tempted to switch this from percent-formatting
# to .format() in the future.  be sure to read this:
# http://lucumr.pocoo.org/2016/12/29/careful-with-str-format/ and understand
# that it may be a security risk to do so.
ANSIBLE_SSH_CONTROL_PATH       = get_config(p, 'ssh_connection', 'control_path', 'ANSIBLE_SSH_CONTROL_PATH', None)
ANSIBLE_SSH_CONTROL_PATH_DIR   = get_config(p, 'ssh_connection', 'control_path_dir', 'ANSIBLE_SSH_CONTROL_PATH_DIR', u'~/.ansible/cp')
ANSIBLE_SSH_PIPELINING         = get_config(p, 'ssh_connection', 'pipelining', 'ANSIBLE_SSH_PIPELINING', False, value_type='boolean')
ANSIBLE_SSH_RETRIES            = get_config(p, 'ssh_connection', 'retries', 'ANSIBLE_SSH_RETRIES', 0, value_type='integer')
ANSIBLE_SSH_EXECUTABLE         = get_config(p, 'ssh_connection', 'ssh_executable', 'ANSIBLE_SSH_EXECUTABLE', 'ssh')
PARAMIKO_RECORD_HOST_KEYS      = get_config(p, 'paramiko_connection', 'record_host_keys', 'ANSIBLE_PARAMIKO_RECORD_HOST_KEYS', True, value_type='boolean')
PARAMIKO_HOST_KEY_AUTO_ADD     = get_config(p, 'paramiko_connection', 'host_key_auto_add', 'ANSIBLE_PARAMIKO_HOST_KEY_AUTO_ADD', False, value_type='boolean')
PARAMIKO_PROXY_COMMAND         = get_config(p, 'paramiko_connection', 'proxy_command', 'ANSIBLE_PARAMIKO_PROXY_COMMAND', None)
PARAMIKO_LOOK_FOR_KEYS         = get_config(p, 'paramiko_connection', 'look_for_keys', 'ANSIBLE_PARAMIKO_LOOK_FOR_KEYS', True, value_type='boolean')
PERSISTENT_CONNECT_TIMEOUT     = get_config(p, 'persistent_connection', 'connect_timeout', 'ANSIBLE_PERSISTENT_CONNECT_TIMEOUT', 30, value_type='integer')
PERSISTENT_CONNECT_RETRIES     = get_config(p, 'persistent_connection', 'connect_retries', 'ANSIBLE_PERSISTENT_CONNECT_RETRIES', 30, value_type='integer')
PERSISTENT_CONNECT_INTERVAL    = get_config(p, 'persistent_connection', 'connect_interval', 'ANSIBLE_PERSISTENT_CONNECT_INTERVAL', 1, value_type='integer')

# obsolete -- will be formally removed
ACCELERATE_PORT                = get_config(p, 'accelerate', 'accelerate_port', 'ACCELERATE_PORT', 5099, value_type='integer')
ACCELERATE_TIMEOUT             = get_config(p, 'accelerate', 'accelerate_timeout', 'ACCELERATE_TIMEOUT', 30, value_type='integer')
ACCELERATE_CONNECT_TIMEOUT     = get_config(p, 'accelerate', 'accelerate_connect_timeout', 'ACCELERATE_CONNECT_TIMEOUT', 1.0, value_type='float')
ACCELERATE_DAEMON_TIMEOUT      = get_config(p, 'accelerate', 'accelerate_daemon_timeout', 'ACCELERATE_DAEMON_TIMEOUT', 30, value_type='integer')
ACCELERATE_KEYS_DIR            = get_config(p, 'accelerate', 'accelerate_keys_dir', 'ACCELERATE_KEYS_DIR', '~/.fireball.keys')
ACCELERATE_KEYS_DIR_PERMS      = get_config(p, 'accelerate', 'accelerate_keys_dir_perms', 'ACCELERATE_KEYS_DIR_PERMS', '700')
ACCELERATE_KEYS_FILE_PERMS     = get_config(p, 'accelerate', 'accelerate_keys_file_perms', 'ACCELERATE_KEYS_FILE_PERMS', '600')
ACCELERATE_MULTI_KEY           = get_config(p, 'accelerate', 'accelerate_multi_key', 'ACCELERATE_MULTI_KEY', False, value_type='boolean')
PARAMIKO_PTY                   = get_config(p, 'paramiko_connection', 'pty', 'ANSIBLE_PARAMIKO_PTY', True, value_type='boolean')

# galaxy related
GALAXY_SERVER                  = get_config(p, 'galaxy', 'server', 'ANSIBLE_GALAXY_SERVER', 'https://galaxy.ansible.com')
GALAXY_IGNORE_CERTS            = get_config(p, 'galaxy', 'ignore_certs', 'ANSIBLE_GALAXY_IGNORE', False, value_type='boolean')
# this can be configured to blacklist SCMS but cannot add new ones unless the code is also updated
GALAXY_SCMS                    = get_config(p, 'galaxy', 'scms', 'ANSIBLE_GALAXY_SCMS', 'git, hg', value_type='list')
GALAXY_ROLE_SKELETON = get_config(p, 'galaxy', 'role_skeleton', 'ANSIBLE_GALAXY_ROLE_SKELETON', None, value_type='path')
GALAXY_ROLE_SKELETON_IGNORE = get_config(p, 'galaxy', 'role_skeleton_ignore', 'ANSIBLE_GALAXY_ROLE_SKELETON_IGNORE', ['^.git$', '^.*/.git_keep$'], value_type='list')

STRING_TYPE_FILTERS = get_config(p, 'jinja2', 'dont_type_filters', 'ANSIBLE_STRING_TYPE_FILTERS', ['string', 'to_json', 'to_nice_json', 'to_yaml', 'ppretty', 'json'], value_type='list' )

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
COLOR_CHANGED     = get_config(p, 'colors', 'changed', 'ANSIBLE_COLOR_CHANGED', 'yellow')
COLOR_DIFF_ADD    = get_config(p, 'colors', 'diff_add', 'ANSIBLE_COLOR_DIFF_ADD', 'green')
COLOR_DIFF_REMOVE = get_config(p, 'colors', 'diff_remove', 'ANSIBLE_COLOR_DIFF_REMOVE', 'red')
COLOR_DIFF_LINES  = get_config(p, 'colors', 'diff_lines', 'ANSIBLE_COLOR_DIFF_LINES', 'cyan')

# diff
DIFF_CONTEXT = get_config(p, 'diff', 'context', 'ANSIBLE_DIFF_CONTEXT', 3, value_type='integer')
DIFF_ALWAYS = get_config(p, 'diff', 'always', 'ANSIBLE_DIFF_ALWAYS', False, value_type='bool')

# non-configurable things
MODULE_REQUIRE_ARGS       = ['command', 'win_command', 'shell', 'win_shell', 'raw', 'script']
MODULE_NO_JSON            = ['command', 'win_command', 'shell', 'win_shell', 'raw']
DEFAULT_BECOME_PASS       = None
DEFAULT_PASSWORD_CHARS = to_text(ascii_letters + digits + ".,:-_", errors='strict')  # characters included in auto-generated passwords
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
IGNORE_FILES = ["COPYING", "CONTRIBUTING", "LICENSE", "README", "VERSION", "GUIDELINES"]
INTERNAL_RESULT_KEYS      = ['add_host', 'add_group']
RESTRICTED_RESULT_KEYS    = ['ansible_rsync_path', 'ansible_playbook_python']

