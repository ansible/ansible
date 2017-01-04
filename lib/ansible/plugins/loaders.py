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
    config = C.DEFAULT_CACHE_PLUGIN_PATH
    subdir = 'cache_plugins'


class CallbackLoader(loader.PluginLoader):
    class_name = 'CallbackModule'
    package = 'ansible.plugins.callback'
    default_config = C.DEFAULT_CALLBACK_PLUGIN_PATH
    subdir = 'callback_plugins'


connection_loader = loader.PluginLoader(
    'Connection',
    'ansible.plugins.connection',
    C.DEFAULT_CONNECTION_PLUGIN_PATH,
    'connection_plugins',
    aliases={'paramiko': 'paramiko_ssh'},
    required_base_class='ConnectionBase',
)


class ShellLoader(loader.PluginLoader):
    class_name = 'ShellModule'
    package = 'ansible.plugins.shell'
    # FIXME: why is config just shell_plugins?
    config = 'shell_plugins'
    subdir = 'shell_plugins'


module_loader = loader.PluginLoader(
    '',
    'ansible.modules',
    C.DEFAULT_MODULE_PATH,
    'library',
)


class LookupLoader(loader.PluginLoader):
    class_name = 'LookupModule'
    package = 'ansible.plugins.lookup'
    config = C.DEFAULT_LOOKUP_PLUGIN_PATH
    subdir = 'lookup_plugins'
    required_base_class = 'LookupBase'


class VarsLoader(loader.PluginLoader):
    class_name = 'VarsModule'
    package = 'ansible.plugins.vars'
    config = C.DEFAULT_VARS_PLUGIN_PATH
    subdir = 'vars_plugins'


class FilterLoader(loader.PluginLoader):
    class_name = 'FilterModule'
    package = 'ansible.plugins.filter'
    config = C.DEFAULT_FILTER_PLUGIN_PATH
    subdir = 'filter_plugins'


class TestLoader(loader.PluginLoader):
    class_name = 'TestModule'
    package = 'ansible.plugins.test'
    config = C.DEFAULT_TEST_PLUGIN_PATH
    subdir = 'test_plugins'


fragment_loader = loader.PluginLoader(
    'ModuleDocFragment',
    'ansible.utils.module_docs_fragments',
    os.path.join(os.path.dirname(__file__), 'module_docs_fragments'),
    '',
)

strategy_loader = loader.PluginLoader(
    'StrategyModule',
    'ansible.plugins.strategy',
    C.DEFAULT_STRATEGY_PLUGIN_PATH,
    'strategy_plugins',
    required_base_class='StrategyBase',
)


class TerminalLoader(loader.PluginLoader):
    class_name = 'TerminalModule'
    package = 'ansible.plugins.terminal'
    config = 'terminal_plugins'
    subdir = 'terminal_plugins'
