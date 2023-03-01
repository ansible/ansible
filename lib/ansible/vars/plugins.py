# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.inventory.host import Host
from ansible.module_utils.common.text.converters import to_bytes
from ansible.plugins.loader import vars_loader
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars

display = Display()

cached_vars_plugin_order = None
cached_stateless_vars_plugins = {}


def initialize_vars_plugin_caches():
    auto = []
    enabled = []

    for auto_run_plugin in vars_loader.all(class_only=True):
        needs_enabled = False
        if hasattr(auto_run_plugin, 'REQUIRES_ENABLED'):
            needs_enabled = auto_run_plugin.REQUIRES_ENABLED
        elif hasattr(auto_run_plugin, 'REQUIRES_WHITELIST'):
            needs_enabled = auto_run_plugin.REQUIRES_WHITELIST
            display.deprecated("The VarsModule class variable 'REQUIRES_WHITELIST' is deprecated. "
                               "Use 'REQUIRES_ENABLED' instead.", version=2.18)
        if needs_enabled:
            continue
        # we can use _load_name here since we don't need to distinguish between builtin and legacy
        # (builtins should have REQUIRES_ENABLED=True)
        plugin_name = auto_run_plugin._load_name
        auto.append(plugin_name)
        if auto_run_plugin.is_stateless:
            cached_stateless_vars_plugins[plugin_name] = auto_run_plugin

    for enabled_plugin in C.VARIABLE_PLUGINS_ENABLED:
        plugin = vars_loader.get(enabled_plugin)
        enabled.append(enabled_plugin)
        if plugin.is_stateless:
            cached_stateless_vars_plugins[enabled_plugin] = plugin

    global cached_vars_plugin_order
    cached_vars_plugin_order = auto + enabled


def get_plugin_vars(loader, plugin, path, entities):

    data = {}
    try:
        data = plugin.get_vars(loader, path, entities)
    except AttributeError:
        try:
            for entity in entities:
                if isinstance(entity, Host):
                    data |= plugin.get_host_vars(entity.name)
                else:
                    data |= plugin.get_group_vars(entity.name)
        except AttributeError:
            if hasattr(plugin, 'run'):
                raise AnsibleError("Cannot use v1 type vars plugin %s from %s" % (plugin._load_name, plugin._original_path))
            else:
                raise AnsibleError("Invalid vars plugin %s from %s" % (plugin._load_name, plugin._original_path))
    return data


def get_vars_from_path(loader, path, entities, stage):

    data = {}

    if cached_vars_plugin_order is None:
        initialize_vars_plugin_caches()

    for plugin_name in cached_vars_plugin_order:
        if plugin_name in cached_stateless_vars_plugins:
            plugin = cached_stateless_vars_plugins[plugin_name]
        else:
            plugin = vars_loader.get(plugin_name)

        collection = '.' in plugin.ansible_name and not plugin.ansible_name.startswith('ansible.builtin.')
        # Warn if a collection plugin has REQUIRES_ENABLED because it has no effect.
        if collection and (hasattr(plugin, 'REQUIRES_ENABLED') or hasattr(plugin, 'REQUIRES_WHITELIST')):
            display.warning(
                "Vars plugins in collections must be enabled to be loaded, REQUIRES_ENABLED is not supported. "
                "This should be removed from the plugin %s." % plugin.ansible_name
            )

        has_stage = hasattr(plugin, 'get_option') and plugin.has_option('stage')

        # if a plugin-specific setting has not been provided, use the global setting
        # older/non shipped plugins that don't support the plugin-specific setting should also use the global setting
        use_global = (has_stage and plugin.get_option('stage') is None) or not has_stage

        if use_global:
            if C.RUN_VARS_PLUGINS == 'demand' and stage == 'inventory':
                continue
            elif C.RUN_VARS_PLUGINS == 'start' and stage == 'task':
                continue
        elif has_stage and plugin.get_option('stage') not in ('all', stage):
            continue

        data = combine_vars(data, get_plugin_vars(loader, plugin, path, entities))

    return data


def get_vars_from_inventory_sources(loader, sources, entities, stage):

    data = {}
    for path in sources:

        if path is None:
            continue
        if ',' in path and not os.path.exists(path):  # skip host lists
            continue
        elif not os.path.isdir(to_bytes(path)):
            # always pass the directory of the inventory source file
            path = os.path.dirname(path)

        data = combine_vars(data, get_vars_from_path(loader, path, entities, stage))

    return data
