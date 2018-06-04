# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ast import literal_eval
from jinja2 import Template
from string import ascii_letters, digits

from ansible.module_utils._text import to_text
from ansible.module_utils.parsing.convert_bool import boolean, BOOLEANS_TRUE
from ansible.module_utils.six import string_types
from ansible.config.manager import ConfigManager, ensure_type, get_ini_config_value


def _deprecated(msg, version='2.8'):
    ''' display is not guaranteed here, nor it being the full class, but try anyways, fallback to sys.stderr.write '''
    try:
        from __main__ import display
        display.deprecated(msg, version=version)
    except:
        import sys
        sys.stderr.write('[DEPRECATED] %s, to be removed in %s' % (msg, version))


def mk_boolean(value):
    ''' moved to module_utils'''
    _deprecated('ansible.constants.mk_boolean() is deprecated.  Use ansible.module_utils.parsing.convert_bool.boolean() instead')
    return boolean(value, strict=False)


def get_config(parser, section, key, env_var, default_value, value_type=None, expand_relative_paths=False):
    ''' kept for backwarsd compatibility, but deprecated '''
    _deprecated('ansible.constants.get_config() is deprecated. There is new config API, see porting docs.')

    value = None
    # small reconstruction of the old code env/ini/default
    value = os.environ.get(env_var, None)
    if value is None:
        try:
            value = get_ini_config_value(parser, {'key': key, 'section': section})
        except:
            pass
    if value is None:
        value = default_value

    value = ensure_type(value, value_type)

    return value


def set_constant(name, value, export=vars()):
    ''' sets constants and returns resolved options dict '''
    export[name] = value


# CONSTANTS ### yes, actual ones
BECOME_METHODS = ['sudo', 'su', 'pbrun', 'pfexec', 'doas', 'dzdo', 'ksu', 'runas', 'pmrun', 'enable', 'machinectl']
BECOME_ERROR_STRINGS = {
    'sudo': 'Sorry, try again.',
    'su': 'Authentication failure',
    'pbrun': '',
    'pfexec': '',
    'doas': 'Permission denied',
    'dzdo': '',
    'ksu': 'Password incorrect',
    'pmrun': 'You are not permitted to run this command',
    'enable': '',
    'machinectl': '',
}  # FIXME: deal with i18n
BECOME_MISSING_STRINGS = {
    'sudo': 'sorry, a password is required to run sudo',
    'su': '',
    'pbrun': '',
    'pfexec': '',
    'doas': 'Authorization required',
    'dzdo': '',
    'ksu': 'No password given',
    'pmrun': '',
    'enable': '',
    'machinectl': '',
}  # FIXME: deal with i18n
BLACKLIST_EXTS = ('.pyc', '.pyo', '.swp', '.bak', '~', '.rpm', '.md', '.txt')
BOOL_TRUE = BOOLEANS_TRUE
CONTROLER_LANG = os.getenv('LANG', 'en_US.UTF-8')
DEFAULT_BECOME_PASS = None
DEFAULT_PASSWORD_CHARS = to_text(ascii_letters + digits + ".,:-_", errors='strict')  # characters included in auto-generated passwords
DEFAULT_SUDO_PASS = None
DEFAULT_REMOTE_PASS = None
DEFAULT_SUBSET = None
DEFAULT_SU_PASS = None
# FIXME: expand to other plugins, but never doc fragments
CONFIGURABLE_PLUGINS = ('cache', 'callback', 'connection', 'inventory', 'lookup', 'shell')
# NOTE: always update the docs/docsite/Makefile to match
DOCUMENTABLE_PLUGINS = CONFIGURABLE_PLUGINS + ('module', 'strategy', 'vars')
IGNORE_FILES = ("COPYING", "CONTRIBUTING", "LICENSE", "README", "VERSION", "GUIDELINES")  # ignore during module search
INTERNAL_RESULT_KEYS = ('add_host', 'add_group')
LOCALHOST = ('127.0.0.1', 'localhost', '::1')
MODULE_REQUIRE_ARGS = ('command', 'win_command', 'shell', 'win_shell', 'raw', 'script')
MODULE_NO_JSON = ('command', 'win_command', 'shell', 'win_shell', 'raw')
RESTRICTED_RESULT_KEYS = ('ansible_rsync_path', 'ansible_playbook_python')
TREE_DIR = None
VAULT_VERSION_MIN = 1.0
VAULT_VERSION_MAX = 1.0

# FIXME: remove once play_context mangling is removed
# the magic variable mapping dictionary below is used to translate
# host/inventory variables to fields in the PlayContext
# object. The dictionary values are tuples, to account for aliases
# in variable names.

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

    # deprecated
    sudo=('ansible_sudo', ),
    sudo_user=('ansible_sudo_user', ),
    sudo_pass=('ansible_sudo_password', 'ansible_sudo_pass'),
    sudo_exe=('ansible_sudo_exe', ),
    sudo_flags=('ansible_sudo_flags', ),
    su=('ansible_su', ),
    su_user=('ansible_su_user', ),
    su_pass=('ansible_su_password', 'ansible_su_pass'),
    su_exe=('ansible_su_exe', ),
    su_flags=('ansible_su_flags', ),
)

# POPULATE SETTINGS FROM CONFIG ###
config = ConfigManager()

# Generate constants from config
for setting in config.data.get_settings():

    value = setting.value
    if setting.origin == 'default' and \
       isinstance(setting.value, string_types) and \
       (setting.value.startswith('{{') and setting.value.endswith('}}')):
        try:
            t = Template(setting.value)
            value = t.render(vars())
            try:
                value = literal_eval(value)
            except ValueError:
                pass  # not a python data structure
        except:
            pass  # not templatable

        value = ensure_type(value, setting.type)

    set_constant(setting.name, value)
