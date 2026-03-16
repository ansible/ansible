# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import re

from string import ascii_letters, digits

from ansible.config.manager import ConfigManager
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE
from ansible.utils.fqcn import add_internal_fqcns

# initialize config manager/config data to read/store global settings
# and generate 'pseudo constants' for app consumption.
config = ConfigManager()


def set_constant(name, value, export=vars()):
    """ sets constants and returns resolved options dict """
    export[name] = value


# CONSTANTS ### yes, actual ones

# The following are hard-coded action names
_ACTION_DEBUG = add_internal_fqcns(('debug', ))
_ACTION_IMPORT_PLAYBOOK = add_internal_fqcns(('import_playbook', ))
_ACTION_IMPORT_ROLE = add_internal_fqcns(('import_role', ))
_ACTION_IMPORT_TASKS = add_internal_fqcns(('import_tasks', ))
_ACTION_INCLUDE_ROLE = add_internal_fqcns(('include_role', ))
_ACTION_INCLUDE_TASKS = add_internal_fqcns(('include_tasks', ))
_ACTION_INCLUDE_VARS = add_internal_fqcns(('include_vars', ))
_ACTION_INVENTORY_TASKS = add_internal_fqcns(('add_host', 'group_by'))
_ACTION_META = add_internal_fqcns(('meta', ))
_ACTION_SET_FACT = add_internal_fqcns(('set_fact', ))
_ACTION_SETUP = add_internal_fqcns(('setup', ))
_ACTION_HAS_CMD = add_internal_fqcns(('command', 'shell', 'script'))
_ACTION_ALLOWS_RAW_ARGS = _ACTION_HAS_CMD + add_internal_fqcns(('raw', ))
_ACTION_ALL_INCLUDES = _ACTION_INCLUDE_TASKS + _ACTION_INCLUDE_ROLE
_ACTION_ALL_INCLUDE_IMPORT_TASKS = _ACTION_INCLUDE_TASKS + _ACTION_IMPORT_TASKS
_ACTION_ALL_PROPER_INCLUDE_IMPORT_ROLES = _ACTION_INCLUDE_ROLE + _ACTION_IMPORT_ROLE
_ACTION_ALL_PROPER_INCLUDE_IMPORT_TASKS = _ACTION_INCLUDE_TASKS + _ACTION_IMPORT_TASKS
_ACTION_ALL_INCLUDE_ROLE_TASKS = _ACTION_INCLUDE_ROLE + _ACTION_INCLUDE_TASKS
_ACTION_FACT_GATHERING = _ACTION_SETUP + add_internal_fqcns(('gather_facts', ))
_ACTION_WITH_CLEAN_FACTS = _ACTION_SET_FACT + _ACTION_INCLUDE_VARS

# http://nezzen.net/2008/06/23/colored-text-in-python-using-ansi-escape-sequences/
COLOR_CODES = {
    'black': u'0;30', 'bright gray': u'0;37',
    'blue': u'0;34', 'white': u'1;37',
    'green': u'0;32', 'bright blue': u'1;34',
    'cyan': u'0;36', 'bright green': u'1;32',
    'red': u'0;31', 'bright cyan': u'1;36',
    'purple': u'0;35', 'bright red': u'1;31',
    'yellow': u'0;33', 'bright purple': u'1;35',
    'dark gray': u'1;30', 'bright yellow': u'1;33',
    'magenta': u'0;35', 'bright magenta': u'1;35',
    'normal': u'0',
}
REJECT_EXTS = ['.pyc', '.pyo', '.swp', '.bak', '~', '.rpm', '.md', '.txt', '.rst']  # this is concatenated with other config settings as lists; cannot be tuple
BOOL_TRUE = BOOLEANS_TRUE
COLLECTION_PTYPE_COMPAT = {'module': 'modules'}

PYTHON_DOC_EXTENSIONS = ('.py',)
YAML_DOC_EXTENSIONS = ('.yml', '.yaml')
DOC_EXTENSIONS = PYTHON_DOC_EXTENSIONS + YAML_DOC_EXTENSIONS

DEFAULT_BECOME_PASS = None
DEFAULT_PASSWORD_CHARS = to_text(ascii_letters + digits + ".,:-_", errors='strict')  # characters included in auto-generated passwords
DEFAULT_REMOTE_PASS = None
DEFAULT_SUBSET = None
# FIXME: expand to other plugins, but never doc fragments
CONFIGURABLE_PLUGINS = ('become', 'cache', 'callback', 'cliconf', 'connection', 'httpapi', 'inventory', 'lookup', 'netconf', 'shell', 'vars')
# NOTE: always update the docs/docsite/Makefile to match
DOCUMENTABLE_PLUGINS = CONFIGURABLE_PLUGINS + ('module', 'strategy', 'test', 'filter')
IGNORE_FILES = ("COPYING", "CONTRIBUTING", "LICENSE", "README", "VERSION", "GUIDELINES", "MANIFEST", "Makefile")  # ignore during module search
INTERNAL_RESULT_KEYS = ('add_host', 'add_group')
INTERNAL_STATIC_VARS = frozenset(
    [
        "ansible_async_path",
        "ansible_collection_name",
        "ansible_config_file",
        "ansible_dependent_role_names",
        "ansible_diff_mode",
        "ansible_config_file",
        "ansible_facts",
        "ansible_forks",
        "ansible_inventory_sources",
        "ansible_limit",
        "ansible_play_batch",
        "ansible_play_hosts",
        "ansible_play_hosts_all",
        "ansible_play_role_names",
        "ansible_playbook_python",
        "ansible_role_name",
        "ansible_role_names",
        "ansible_run_tags",
        "ansible_skip_tags",
        "ansible_verbosity",
        "ansible_version",
        "inventory_dir",
        "inventory_file",
        "inventory_hostname",
        "inventory_hostname_short",
        "groups",
        "group_names",
        "hostvars",
        "playbook_dir",
        "play_hosts",
        "role_name",
        "role_names",
        "role_path",
        "role_uuid",
        "role_names",
    ]
)
LOCALHOST = ('127.0.0.1', 'localhost', '::1')
WIN_MOVED = ['ansible.windows.win_command', 'ansible.windows.win_shell']
MODULE_REQUIRE_ARGS_SIMPLE = ['command', 'raw', 'script', 'shell', 'win_command', 'win_shell']
MODULE_REQUIRE_ARGS = tuple(add_internal_fqcns(MODULE_REQUIRE_ARGS_SIMPLE) + WIN_MOVED)
MODULE_NO_JSON = tuple(add_internal_fqcns(('command', 'win_command', 'shell', 'win_shell', 'raw')) + WIN_MOVED)
RESTRICTED_RESULT_KEYS = ('ansible_rsync_path', 'ansible_playbook_python', 'ansible_facts')
SYNTHETIC_COLLECTIONS = ('ansible.builtin', 'ansible.legacy')
TREE_DIR = None
VAULT_VERSION_MIN = 1.0
VAULT_VERSION_MAX = 1.0

# This matches a string that cannot be used as a valid python variable name i.e 'not-valid', 'not!valid@either' '1_nor_This'
INVALID_VARIABLE_NAMES = re.compile(r'^[\d\W]|[^\w]')


# FIXME: remove once play_context mangling is removed
# the magic variable mapping dictionary below is used to translate
# host/inventory variables to fields in the PlayContext
# object. The dictionary values are tuples, to account for aliases
# in variable names.

COMMON_CONNECTION_VARS = frozenset(('ansible_connection', 'ansible_host', 'ansible_user', 'ansible_shell_executable',
                                    'ansible_port', 'ansible_pipelining', 'ansible_password', 'ansible_timeout',
                                    'ansible_shell_type', 'ansible_module_compression', 'ansible_private_key_file'))

MAGIC_VARIABLE_MAPPING = dict(

    # base
    connection=('ansible_connection', ),
    module_compression=('ansible_module_compression', ),
    shell=('ansible_shell_type', ),
    executable=('ansible_shell_executable', ),

    # connection common
    remote_addr=('ansible_ssh_host', 'ansible_host'),
    remote_user=('ansible_ssh_user', 'ansible_user'),
    password=('ansible_ssh_pass', 'ansible_password'),
    port=('ansible_ssh_port', 'ansible_port'),
    pipelining=('ansible_ssh_pipelining', 'ansible_pipelining'),
    timeout=('ansible_ssh_timeout', 'ansible_timeout'),
    private_key_file=('ansible_ssh_private_key_file', 'ansible_private_key_file'),

    # networking modules
    network_os=('ansible_network_os', ),
    connection_user=('ansible_connection_user',),

    # ssh TODO: remove
    ssh_executable=('ansible_ssh_executable', ),
    ssh_common_args=('ansible_ssh_common_args', ),
    sftp_extra_args=('ansible_sftp_extra_args', ),
    scp_extra_args=('ansible_scp_extra_args', ),
    ssh_extra_args=('ansible_ssh_extra_args', ),
    ssh_transfer_method=('ansible_ssh_transfer_method', ),

    # docker TODO: remove
    docker_extra_args=('ansible_docker_extra_args', ),

    # become
    become=('ansible_become', ),
    become_method=('ansible_become_method', ),
    become_user=('ansible_become_user', ),
    become_pass=('ansible_become_password', 'ansible_become_pass'),
    become_exe=('ansible_become_exe', ),
    become_flags=('ansible_become_flags', ),
)

# POPULATE SETTINGS FROM CONFIG ###
for setting in config.get_configuration_definitions():
    set_constant(setting, config.get_config_value(setting, variables=vars()))
