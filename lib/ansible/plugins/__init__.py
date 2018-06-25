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

    # allow extra passthrough parameters
    allow_extras = False

    def __init__(self):
        self._options = {}

    def get_option(self, option, hostvars=None):
        if option not in self._options:
            option_value = C.config.get_config_value(option, plugin_type=get_plugin_class(self), plugin_name=self._load_name, variables=hostvars)
            self.set_option(option, option_value)
        return self._options.get(option)

    def set_option(self, option, value):
        self._options[option] = value

    def set_options(self, task_keys=None, var_options=None, direct=None):
        '''
        Sets the _options attribute with the configuration/keyword information for this plugin

        :arg task_keys: Dict with playbook keywords that affect this option
        :arg var_options: Dict with either 'connection variables'
        :arg direct: Dict with 'direct assignment'
        '''
        self._options = C.config.get_plugin_options(get_plugin_class(self), self._load_name, keys=task_keys, variables=var_options, direct=direct)

        # allow extras/wildcards from vars that are not directly consumed in configuration
        # this is needed to support things like winrm that can have extended protocol options we don't direclty handle
        if self.allow_extras and var_options and '_extras' in var_options:
            self.set_option('_extras', var_options['_extras'])

    def _check_required(self):
        # FIXME: standarize required check based on config
        pass
