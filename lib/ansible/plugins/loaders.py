# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com> and others
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

import inspect
import os
import sys

from ansible import constants as C
from ansible.plugins import loader


def get_all_plugin_loaders():
    return [(name, obj) for (name, obj) in inspect.getmembers(sys.modules[__name__]) if isinstance(obj, loader.PluginLoader)]


class ActionLoader(loader.PluginLoader):
    class_name = 'ActionModule'
    package = 'ansible.plugins.action'
    default_config = C.DEFAULT_ACTION_PLUGIN_PATH
    subdir = 'action_plugins'
    required_base_class = 'ActionBase'


class CacheLoader(loader.PluginLoader):
    class_name = 'CacheModule'
    package = 'ansible.plugins.cache'
    default_config = C.DEFAULT_CACHE_PLUGIN_PATH
    subdir = 'cache_plugins'


class CallbackLoader(loader.PluginLoader):
    class_name = 'CallbackModule'
    package = 'ansible.plugins.callback'
    default_config = C.DEFAULT_CALLBACK_PLUGIN_PATH
    subdir = 'callback_plugins'


class ConnectionLoader(loader.PluginLoader):
    class_name = 'Connection'
    package = 'ansible.plugins.connection'
    default_config = C.DEFAULT_CONNECTION_PLUGIN_PATH
    subdir = 'connection_plugins'
    aliases = {'paramiko': 'paramiko_ssh'}
    required_base_class = 'ConnectionBase'


class ShellLoader(loader.PluginLoader):
    class_name = 'ShellModule'
    package = 'ansible.plugins.shell'
    # FIXME: why is config just shell_plugins?
    default_config = 'shell_plugins'
    subdir = 'shell_plugins'


class ModuleLoader(loader.PluginLoader):
    class_name = ''
    package = 'ansible.modules'
    default_config = C.DEFAULT_MODULE_PATH
    subdir = 'library'

#module_loader = loader.PluginLoader(
#    '',
#    'ansible.modules',
#    C.DEFAULT_MODULE_PATH,
#    'library',
#)


class LookupLoader(loader.PluginLoader):
    class_name = 'LookupModule'
    package = 'ansible.plugins.lookup'
    default_config = C.DEFAULT_LOOKUP_PLUGIN_PATH
    subdir = 'lookup_plugins'
    required_base_class = 'LookupBase'


class VarsLoader(loader.PluginLoader):
    class_name = 'VarsModule'
    package = 'ansible.plugins.vars'
    default_config = C.DEFAULT_VARS_PLUGIN_PATH
    subdir = 'vars_plugins'


class FilterLoader(loader.PluginLoader):
    class_name = 'FilterModule'
    package = 'ansible.plugins.filter'
    default_config = C.DEFAULT_FILTER_PLUGIN_PATH
    subdir = 'filter_plugins'


class TestLoader(loader.PluginLoader):
    class_name = 'TestModule'
    package = 'ansible.plugins.test'
    default_config = C.DEFAULT_TEST_PLUGIN_PATH
    subdir = 'test_plugins'


class FragmentLoader(loader.PluginLoader):
    class_name = 'ModuleDocFragment'
    package = 'ansible.utils.module_docs_fragments'
    default_config = os.path.join(os.path.dirname(__file__), 'module_docs_fragments')
    subdir = ''


class StrategyLoader(loader.PluginLoader):
    class_name = 'StrategyModule'
    package = 'ansible.plugins.strategy'
    default_config = C.DEFAULT_STRATEGY_PLUGIN_PATH
    subdir = 'strategy_plugins'
    required_base_class = 'StrategyBase'


class TerminalLoader(loader.PluginLoader):
    class_name = 'TerminalModule'
    package = 'ansible.plugins.terminal'
    default_config = 'terminal_plugins'
    subdir = 'terminal_plugins'
