# Copyright (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os  # used to set lang and for backwards compat get_config
from string import ascii_letters, digits

from ansible.module_utils._text import to_text
from ansible.module_utils.parsing.convert_bool import boolean, BOOLEANS_TRUE
from ansible.module_utils.six import string_types
from ansible.config.manager import ConfigManager, ensure_type

def _deprecated(msg):
    ''' display is not guaranteed here, nor it being the full class, but try anyways, fallback to sys.stderr.write '''
    try:
        from __main__ import display
        display.deprecated(msg, version='2.8')
    except:
        import sys
        sys.stderr.write('[DEPRECATED] %s, to be removed in 2.8' % msg)

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
            value = config.get_ini_config(parser, [{'key': key, 'section': section}])
        except:
            pass
    if value is None:
        value = default_value
    try:
        value = config.ensure_type(value, value_type)
    except:
        pass

    return value

def set_constant(name, value, export=vars()):
    ''' sets constants and returns resolved options dict '''
    export[name] = value

### CONSTANTS ### yes, actual ones
BLACKLIST_EXTS = ('.pyc', '.pyo', '.swp', '.bak', '~', '.rpm', '.md', '.txt')
BECOME_METHODS = ['sudo', 'su', 'pbrun', 'pfexec', 'doas', 'dzdo', 'ksu', 'runas', 'pmrun']
BECOME_ERROR_STRINGS = {
    'sudo': 'Sorry, try again.',
    'su': 'Authentication failure',
    'pbrun': '',
    'pfexec': '',
    'doas': 'Permission denied',
    'dzdo': '',
    'ksu': 'Password incorrect',
    'pmrun': 'You are not permitted to run this command'
}  # FIXME: deal with i18n
BECOME_MISSING_STRINGS = {
    'sudo': 'sorry, a password is required to run sudo',
    'su': '',
    'pbrun': '',
    'pfexec': '',
    'doas': 'Authorization required',
    'dzdo': '',
    'ksu': 'No password given',
    'pmrun': ''
}  # FIXME: deal with i18n
BOOL_TRUE = BOOLEANS_TRUE
DEFAULT_BECOME_PASS = None
DEFAULT_PASSWORD_CHARS = to_text(ascii_letters + digits + ".,:-_", errors='strict')  # characters included in auto-generated passwords
DEFAULT_SUDO_PASS = None
DEFAULT_REMOTE_PASS = None
DEFAULT_SUBSET = None
DEFAULT_SU_PASS = None
IGNORE_FILES = ["COPYING", "CONTRIBUTING", "LICENSE", "README", "VERSION", "GUIDELINES"]  # ignore during module search
INTERNAL_RESULT_KEYS = ['add_host', 'add_group']
LOCALHOST = frozenset(['127.0.0.1', 'localhost', '::1'])
MODULE_REQUIRE_ARGS = ['command', 'win_command', 'shell', 'win_shell', 'raw', 'script']
MODULE_NO_JSON = ['command', 'win_command', 'shell', 'win_shell', 'raw']
RESTRICTED_RESULT_KEYS = ['ansible_rsync_path', 'ansible_playbook_python']
TREE_DIR = None
VAULT_VERSION_MIN = 1.0
VAULT_VERSION_MAX = 1.0

### POPULATE SETTINGS FROM CONFIG ###
config = ConfigManager()

# Generate constants from config
for setting in config.data.get_settings():

    value = None
    if isinstance(setting.value, string_types) and (setting.value.startswith('eval(') and setting.value.endswith(')')):
        try:
            # FIXME: find better way to do in manager class and/or ensure types
            eval_string = setting.value.replace('eval(', '', 1)[:-1]
            value = ensure_type(eval(eval_string), setting.type)  # FIXME: safe eval?
        except:
            value = setting.value

    set_constant(setting.name, setting.value)


