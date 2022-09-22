# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.inventory.host import Host
from ansible.module_utils._text import to_bytes
from ansible.plugins.loader import vars_loader
from ansible.utils.collection_loader import AnsibleCollectionRef
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars

display = Display()


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

    enabled_vars_plugins = []
    enabled_canonical_names = []
    for plugin_name in C.VARIABLE_PLUGINS_ENABLED:
        vars_plugin = vars_loader.get(plugin_name)
        if vars_plugin is None:
            # Error if there's no play directory or the name is wrong?
            continue
        enabled_canonical_names.append(vars_plugin.ansible_name)
        if '.' not in vars_plugin.ansible_name:
            # Legacy plugin will be loaded below with all()
            continue

        invalid_collection_option = hasattr(vars_plugin, 'REQUIRES_ENABLED') or hasattr(vars_plugin, 'REQUIRES_WHITELIST')
        if not vars_plugin.ansible_name.startswith('ansible.builtin.') and invalid_collection_option:
            display.warning(
                "Vars plugins in collections must be enabled to be loaded, REQUIRES_ENABLED is not supported. "
                "This should be removed from the plugin %s." % vars_plugin.ansible_name
            )
        enabled_vars_plugins.append(vars_plugin)

    legacy_vars_plugins = []
    for plugin in vars_loader.all():
        if plugin.ansible_name.startswith('ansible.builtin.'):
            continue
        if hasattr(plugin, 'REQUIRES_WHITELIST'):
            display.deprecated("The VarsModule class variable 'REQUIRES_WHITELIST' is deprecated. "
                               "Use 'REQUIRES_ENABLED' instead.", version=2.18)
        if getattr(plugin, 'REQUIRES_ENABLED', getattr(plugin, 'REQUIRES_WHITELIST', False)):
            if not plugin.ansible_name in enabled_canonical_names:
                continue
        legacy_vars_plugins.append(plugin)

    for plugin in legacy_vars_plugins + enabled_vars_plugins:
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
