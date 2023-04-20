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

load_vars_plugins = None
has_stage_cache = {}


def _load_vars_plugins():
    global load_vars_plugins
    load_vars_plugins = []

    for legacy_plugin in vars_loader.all():
        needs_enabled = False
        if hasattr(legacy_plugin, 'REQUIRES_ENABLED'):
            needs_enabled = legacy_plugin.REQUIRES_ENABLED
        elif hasattr(legacy_plugin, 'REQUIRES_WHITELIST'):
            display.deprecated("The VarsModule class variable 'REQUIRES_WHITELIST' is deprecated. "
                               "Use 'REQUIRES_ENABLED' instead.", version=2.18)
            needs_enabled = legacy_plugin.REQUIRES_WHITELIST
        if needs_enabled:
            continue
        load_vars_plugins.append((legacy_plugin.ansible_name, legacy_plugin._original_path))

    for plugin_name in C.VARIABLE_PLUGINS_ENABLED:
        plugin = vars_loader.get(plugin_name)
        if not plugin:
            continue
        load_vars_plugins.append((plugin_name, plugin._original_path))


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

    if load_vars_plugins is None:
        _load_vars_plugins()

    for plugin_name, plugin_path in load_vars_plugins:
        plugin, found_in_cache = vars_loader.get_from_cached_load_context(plugin_name, plugin_path)
        if plugin is None:
            continue

        # Warn if a collection plugin has REQUIRES_ENABLED because it has no effect.
        builtin_or_legacy = plugin.ansible_name.startswith('ansible.builtin.') or '.' not in plugin.ansible_name
        if not builtin_or_legacy and (hasattr(plugin, 'REQUIRES_ENABLED') or hasattr(plugin, 'REQUIRES_WHITELIST')):
            display.warning(
                "Vars plugins in collections must be enabled to be loaded, REQUIRES_ENABLED is not supported. "
                "This should be removed from the plugin %s." % plugin.ansible_name
            )

        if (plugin_name, plugin_path) not in has_stage_cache or not found_in_cache:
            has_stage_cache[(plugin_name, plugin_path)] = hasattr(plugin, 'get_option') and plugin.has_option('stage')

        has_stage = has_stage_cache[(plugin_name, plugin_path)]
        allow_stage = None if not has_stage else plugin.get_option('stage')

        # if a plugin-specific setting has not been provided, use the global setting
        # older/non shipped plugins that don't support the plugin-specific setting should also use the global setting
        use_global = (has_stage and allow_stage is None) or not has_stage

        if use_global:
            if C.RUN_VARS_PLUGINS == 'demand' and stage == 'inventory':
                continue
            elif C.RUN_VARS_PLUGINS == 'start' and stage == 'task':
                continue
        elif has_stage and allow_stage not in ('all', stage):
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
