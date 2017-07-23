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

from string import ascii_letters, digits

from ansible.module_utils._text import to_text
from ansible.module_utils.parsing.convert_bool import boolean, BOOLEANS_TRUE
from ansible.config.manager import ConfigManager

_config = ConfigManager()

# Generate constants from config
for setting in _config.data.get_settings():
    vars()[setting.name] = setting.value


def mk_boolean(value):
    ''' moved to module_utils'''
    # We don't have a display here so we can't call deprecated
    # display.deprecated('ansible.constants.mk_boolean() is deprecated.  Use ansible.module_utils.parsing.convert_bool.boolean() instead', version='2.8')
    return boolean(value, strict=False)


# ### CONSTANTS ### yes, actual ones

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
