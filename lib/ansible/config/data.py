# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


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
            settings = [self._global_settings[k] for k in self._global_settings]
        elif plugin.type in self._plugins and plugin.name in self._plugins[plugin.type]:
            settings = [self._plugins[plugin.type][plugin.name][k] for k in self._plugins[plugin.type][plugin.name]]

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
