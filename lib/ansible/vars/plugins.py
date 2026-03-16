# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os

from functools import lru_cache

from ansible import constants as C
from ansible.plugins.loader import vars_loader
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars

display = Display()


def _prime_vars_loader():
    # find 3rd party legacy vars plugins once, and look them up by name subsequently
    list(vars_loader.all(class_only=True))
    for plugin_name in C.VARIABLE_PLUGINS_ENABLED:
        if not plugin_name:
            continue
        vars_loader.get(plugin_name)


# optimized for stateless plugins; non-stateless plugin instances will fall out quickly
@lru_cache(maxsize=10)
def _plugin_should_run(plugin, stage):
    # if a plugin-specific setting has not been provided, use the global setting
    # older/non shipped plugins that don't support the plugin-specific setting should also use the global setting
    allowed_stages = None

    try:
        allowed_stages = plugin.get_option('stage')
    except (AttributeError, KeyError):
        pass

    if allowed_stages:
        return allowed_stages in ('all', stage)

    # plugin didn't declare a preference; consult global config
    config_stage_override = C.RUN_VARS_PLUGINS
    if config_stage_override == 'demand' and stage == 'inventory':
        return False
    elif config_stage_override == 'start' and stage == 'task':
        return False
    return True


def get_vars_from_path(loader, path, entities, stage):
    data = {}
    if vars_loader._paths is None:
        # cache has been reset, reload all()
        _prime_vars_loader()

    for plugin_name in vars_loader._plugin_instance_cache:
        if (plugin := vars_loader.get(plugin_name)) is None:
            continue

        collection = '.' in plugin.ansible_name and not plugin.ansible_name.startswith('ansible.builtin.')
        # Warn if a collection plugin has REQUIRES_ENABLED because it has no effect.
        if collection and hasattr(plugin, 'REQUIRES_ENABLED'):
            display.warning(
                "Vars plugins in collections must be enabled to be loaded, REQUIRES_ENABLED is not supported. "
                "This should be removed from the plugin %s." % plugin.ansible_name
            )

        if not _plugin_should_run(plugin, stage):
            continue

        if (new_vars := plugin.get_vars(loader, path, entities)) != {}:
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
