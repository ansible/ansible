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

from __future__ import annotations

from abc import ABC

import types
import typing as t

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.six import string_types
from ansible.utils.display import Display

display = Display()

if t.TYPE_CHECKING:
    from .loader import PluginPathContext

# Global so that all instances of a PluginLoader will share the caches
MODULE_CACHE = {}  # type: dict[str, dict[str, types.ModuleType]]
PATH_CACHE = {}  # type: dict[str, list[PluginPathContext] | None]
PLUGIN_PATH_CACHE = {}  # type: dict[str, dict[str, dict[str, PluginPathContext]]]


def get_plugin_class(obj):
    if isinstance(obj, string_types):
        return obj.lower().replace('module', '')
    else:
        return obj.__class__.__name__.lower().replace('module', '')


class AnsiblePlugin(ABC):

    # Set by plugin loader
    _load_name: str

    # allow extra passthrough parameters
    allow_extras: bool = False
    _extras_prefix: str | None = None

    def __init__(self):
        self._options = {}
        self._defs = None

    @property
    def extras_prefix(self):
        if not self._extras_prefix:
            self._extras_prefix = self._load_name.split('.')[-1]
        return self._extras_prefix

    def matches_name(self, possible_names):
        possible_fqcns = set()
        for name in possible_names:
            if '.' not in name:
                possible_fqcns.add(f"ansible.builtin.{name}")
            elif name.startswith("ansible.legacy."):
                possible_fqcns.add(name.removeprefix("ansible.legacy."))
            possible_fqcns.add(name)
        return bool(possible_fqcns.intersection(set(self.ansible_aliases)))

    def get_option_and_origin(self, option, hostvars=None):
        try:
            option_value, origin = C.config.get_config_value_and_origin(option, plugin_type=self.plugin_type, plugin_name=self._load_name, variables=hostvars)
        except AnsibleError as e:
            raise KeyError(to_native(e))
        return option_value, origin

    def get_option(self, option, hostvars=None):

        if option not in self._options:
            option_value, dummy = self.get_option_and_origin(option, hostvars=hostvars)
            self.set_option(option, option_value)
        return self._options.get(option)

    def get_options(self, hostvars=None):
        options = {}
        for option in self.option_definitions.keys():
            options[option] = self.get_option(option, hostvars=hostvars)
        return options

    def set_option(self, option, value):
        self._options[option] = C.config.get_config_value(option, plugin_type=self.plugin_type, plugin_name=self._load_name, direct={option: value})
        C.handle_config_noise(display)

    def set_options(self, task_keys=None, var_options=None, direct=None):
        '''
        Sets the _options attribute with the configuration/keyword information for this plugin

        :arg task_keys: Dict with playbook keywords that affect this option
        :arg var_options: Dict with either 'connection variables'
        :arg direct: Dict with 'direct assignment'
        '''
        self._options = C.config.get_plugin_options(self.plugin_type, self._load_name, keys=task_keys, variables=var_options, direct=direct)

        # allow extras/wildcards from vars that are not directly consumed in configuration
        # this is needed to support things like winrm that can have extended protocol options we don't directly handle
        if self.allow_extras and var_options and '_extras' in var_options:
            # these are largely unvalidated passthroughs, either plugin or underlying API will validate
            self._options['_extras'] = var_options['_extras']
        C.handle_config_noise(display)

    def has_option(self, option):
        if not self._options:
            self.set_options()
        return option in self._options

    @property
    def plugin_type(self):
        return self.__class__.__name__.lower().replace('module', '')

    @property
    def option_definitions(self):
        if self._defs is None:
            self._defs = C.config.get_configuration_definitions(plugin_type=self.plugin_type, name=self._load_name)
        return self._defs

    def _check_required(self):
        # FIXME: standardize required check based on config
        pass


class AnsibleJinja2Plugin(AnsiblePlugin):

    def __init__(self, function):

        super(AnsibleJinja2Plugin, self).__init__()
        self._function = function

    @property
    def plugin_type(self):
        return self.__class__.__name__.lower().replace('ansiblejinja2', '')

    def _no_options(self, *args, **kwargs):
        raise NotImplementedError()

    has_option = get_option = get_options = option_definitions = set_option = set_options = _no_options

    @property
    def j2_function(self):
        return self._function
