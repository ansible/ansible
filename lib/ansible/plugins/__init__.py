# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com> and others
# (c) 2017, Toshio Kuratomi <tkuratomi@ansible.com>
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

from abc import ABCMeta

from ansible import constants as C
from ansible.module_utils.six import with_metaclass, string_types

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

# Global so that all instances of a PluginLoader will share the caches
MODULE_CACHE = {}
PATH_CACHE = {}
PLUGIN_PATH_CACHE = {}


def get_plugin_class(obj):
    if isinstance(obj, string_types):
        return obj.lower().replace('module', '')
    else:
        return obj.__class__.__name__.lower().replace('module', '')


class AnsiblePlugin(with_metaclass(ABCMeta, object)):

    def __init__(self):
        self._options = {}

    def get_option(self, option, hostvars=None):
        if option not in self._options:
            option_value = C.config.get_config_value(option, plugin_type=get_plugin_class(self), plugin_name=self.name, variables=hostvars)
            self.set_option(option, option_value)
        return self._options.get(option)

    def set_option(self, option, value):
        self._options[option] = value

    def set_options(self, options):
        self._options = options

    def _check_required(self):
        # FIXME: standarize required check based on config
        pass
