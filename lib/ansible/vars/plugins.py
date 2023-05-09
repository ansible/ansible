# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.inventory.group import InventoryObjectType
from ansible.plugins import AnsiblePlugin
from ansible.plugins.loader import vars_loader
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars

display = Display()

cached_vars_plugin_order = None
has_stage_cache = {}  # type: dict[AnsiblePlugin, bool]


def _load_vars_plugins_order():
    # find 3rd party legacy vars plugins once, and look them up by name subsequently
    auto = []
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
        auto.append(auto_run_plugin._load_name)

    # find enabled plugins once so we can look them up by resolved fqcn subsequently
    enabled = []
    for plugin_name in C.VARIABLE_PLUGINS_ENABLED:
        if (plugin := vars_loader.get(plugin_name)) is None:
            enabled.append(plugin_name)
        else:
            collection = '.' in plugin.ansible_name and not plugin.ansible_name.startswith('ansible.builtin.')
            # Warn if a collection plugin has REQUIRES_ENABLED because it has no effect.
            if collection and (hasattr(plugin, 'REQUIRES_ENABLED') or hasattr(plugin, 'REQUIRES_WHITELIST')):
                display.warning(
                    "Vars plugins in collections must be enabled to be loaded, REQUIRES_ENABLED is not supported. "
                    "This should be removed from the plugin %s." % plugin.ansible_name
                )
            enabled.append(plugin.ansible_name)

    global cached_vars_plugin_order
    cached_vars_plugin_order = auto + enabled


def get_plugin_vars(loader, plugin, path, entities):

    data = {}
    try:
        data = plugin.get_vars(loader, path, entities)
    except AttributeError:
        if hasattr(plugin, 'get_host_vars') or hasattr(plugin, 'get_group_vars'):
            display.deprecated(
                f"The vars plugin {plugin.ansible_name} from {plugin._original_path} is relying "
                "on the deprecated entrypoints 'get_host_vars' and 'get_group_vars'. "
                "This plugin should be updated to inherit from BaseVarsPlugin and define "
                "a 'get_vars' method as the main entrypoint instead.",
                version="2.20",
            )
        try:
            for entity in entities:
                if entity.base_type is InventoryObjectType.HOST:
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
        _load_vars_plugins_order()

    for plugin_name in cached_vars_plugin_order:
        if (plugin := vars_loader.get(plugin_name)) is None:
            continue

        if not getattr(plugin, 'is_stateless', False):
            # avoid needlessly bloating has_stage_cache
            has_stage = hasattr(plugin, 'get_option') and plugin.has_option('stage')
        else:
            try:
                has_stage = has_stage_cache[plugin]
            except KeyError:
                has_stage = has_stage_cache[plugin] = hasattr(plugin, 'get_option') and plugin.has_option('stage')

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

        if (new_vars := get_plugin_vars(loader, plugin, path, entities)) != {}:
            data = combine_vars(data, new_vars)

    return data


def get_vars_from_inventory_sources(loader, sources, entities, stage):

    data = {}
    for path in sources:

        if path is None:
            continue
        if ',' in path and not os.path.exists(path):  # skip host lists
            continue
        elif not os.path.isdir(path):
            # always pass the directory of the inventory source file
            path = os.path.dirname(path)

        if (new_vars := get_vars_from_path(loader, path, entities, stage)) != {}:
            data = combine_vars(data, new_vars)

    return data
