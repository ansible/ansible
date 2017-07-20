# (c) 2017, Ansible by Red Hat, inc
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

from collections import namedtuple

Setting = namedtuple('Setting','name value origin')

class ConfigData(object):

    def __init__(self):
        self._global_settings = {}
        self._plugins = {}

    def get_setting(self, name, plugin=None):

        setting = None
        if plugin is None:
            setting = self._global_settings.get(name)
        elif plugin.type in self._plugins and plugin.name in self._plugins[plugin.type]:
            setting = self._plugins[plugin.type][plugin.name].get(name)

        return setting

    def get_settings(self, plugin=None):

        settings = []
        if plugin is None:
            settings = [ self._global_settings[k] for k in self._global_settings ]
        elif plugin.type in self._plugins and plugin.name in self._plugins[plugin.type]:
            settings = [ self._plugins[plugin.type][plugin.name][k] for k in self._plugins[plugin.type][plugin.name] ]

        return settings

    def update_setting(self, setting, plugin=None):

        if plugin is None:
            self._global_settings[setting.name] = setting
        else:
            if plugin.type not in self._plugins:
                self._plugins[plugin.type] = {}
            if plugin.name not in self._plugins[plugin.type]:
                self._plugins[plugin.type][plugin.name] = {}
            self._plugins[plugin.type][plugin.name][setting.name] = setting
