from __future__ import annotations

import inspect
import re
import pathlib
import sys
import typing as t

from ansible.module_utils.common.messages import PluginInfo

_ansible_module_base_path: t.Final = pathlib.Path(sys.modules['ansible'].__file__).parent
"""Runtime-detected base path of the `ansible` Python package to distinguish between Ansible-owned and external code."""

ANSIBLE_CORE_DEPRECATOR: t.Final = PluginInfo._from_collection_name('ansible.builtin')
"""Singleton `PluginInfo` instance for ansible-core callers where the plugin can/should not be identified in messages."""

INDETERMINATE_DEPRECATOR: t.Final = PluginInfo(resolved_name='indeterminate', type='indeterminate')
"""Singleton `PluginInfo` instance for indeterminate deprecator."""

_DEPRECATOR_PLUGIN_TYPES = frozenset(
    {
        'action',
        'become',
        'cache',
        'callback',
        'cliconf',
        'connection',
        # doc_fragments - no code execution
        # filter - basename inadequate to identify plugin
        'httpapi',
        'inventory',
        'lookup',
        'module',  # only for collections
        'netconf',
        'shell',
        'strategy',
        'terminal',
        # test - basename inadequate to identify plugin
        'vars',
    }
)
"""Plugin types which are valid for identifying a deprecator for deprecation purposes."""

_AMBIGUOUS_DEPRECATOR_PLUGIN_TYPES = frozenset(
    {
        'filter',
        'test',
    }
)
"""Plugin types for which basename cannot be used to identify the plugin name."""


def get_best_deprecator(*, deprecator: PluginInfo | None = None, collection_name: str | None = None) -> PluginInfo:
    """Return the best-available `PluginInfo` for the caller of this method."""
    _skip_stackwalk = True

    if deprecator and collection_name:
        raise ValueError('Specify only one of `deprecator` or `collection_name`.')

    return deprecator or PluginInfo._from_collection_name(collection_name) or get_caller_plugin_info() or INDETERMINATE_DEPRECATOR


def get_caller_plugin_info() -> PluginInfo | None:
    """Try to get `PluginInfo` for the caller of this method, ignoring marked infrastructure stack frames."""
    _skip_stackwalk = True

    if frame_info := next((frame_info for frame_info in inspect.stack() if '_skip_stackwalk' not in frame_info.frame.f_locals), None):
        return _path_as_core_plugininfo(frame_info.filename) or _path_as_collection_plugininfo(frame_info.filename)

    return None  # pragma: nocover


def _path_as_core_plugininfo(path: str) -> PluginInfo | None:
    """Return a `PluginInfo` instance if the provided `path` refers to a core plugin."""
    try:
        relpath = str(pathlib.Path(path).relative_to(_ansible_module_base_path))
    except ValueError:
        return None  # not ansible-core

    namespace = 'ansible.builtin'

    if match := re.match(r'plugins/(?P<plugin_type>\w+)/(?P<plugin_name>\w+)', relpath):
        plugin_name = match.group("plugin_name")
        plugin_type = match.group("plugin_type")

        if plugin_type not in _DEPRECATOR_PLUGIN_TYPES:
            # The plugin type isn't a known deprecator type, so we have to assume the caller is intermediate code.
            # We have no way of knowing if the intermediate code is deprecating its own feature, or acting on behalf of another plugin.
            # Callers in this case need to identify the deprecating plugin name, otherwise only ansible-core will be reported.
            # Reporting ansible-core is never wrong, it just may be missing an additional detail (plugin name) in the "on behalf of" case.
            return ANSIBLE_CORE_DEPRECATOR
    elif match := re.match(r'modules/(?P<module_name>\w+)', relpath):
        # AnsiballZ Python package for core modules
        plugin_name = match.group("module_name")
        plugin_type = "module"
    elif match := re.match(r'legacy/(?P<module_name>\w+)', relpath):
        # AnsiballZ Python package for non-core library/role modules
        namespace = 'ansible.legacy'

        plugin_name = match.group("module_name")
        plugin_type = "module"
    else:
        return ANSIBLE_CORE_DEPRECATOR  # non-plugin core path, safe to use ansible-core for the same reason as the non-deprecator plugin type case above

    name = f'{namespace}.{plugin_name}'

    return PluginInfo(resolved_name=name, type=plugin_type)


def _path_as_collection_plugininfo(path: str) -> PluginInfo | None:
    """Return a `PluginInfo` instance if the provided `path` refers to a collection plugin."""
    if not (match := re.search(r'/ansible_collections/(?P<ns>\w+)/(?P<coll>\w+)/plugins/(?P<plugin_type>\w+)/(?P<plugin_name>\w+)', path)):
        return None

    plugin_type = match.group('plugin_type')

    if plugin_type in _AMBIGUOUS_DEPRECATOR_PLUGIN_TYPES:
        # We're able to detect the namespace, collection and plugin type -- but we have no way to identify the plugin name currently.
        # To keep things simple we'll fall back to just identifying the namespace and collection.
        # In the future we could improve the detection and/or make it easier for a caller to identify the plugin name.
        return PluginInfo._from_collection_name('.'.join((match.group('ns'), match.group('coll'))))

    if plugin_type == 'modules':
        plugin_type = 'module'

    if plugin_type not in _DEPRECATOR_PLUGIN_TYPES:
        # The plugin type isn't a known deprecator type, so we have to assume the caller is intermediate code.
        # We have no way of knowing if the intermediate code is deprecating its own feature, or acting on behalf of another plugin.
        # Callers in this case need to identify the deprecator to avoid ambiguity, since it could be the same collection or another collection.
        return INDETERMINATE_DEPRECATOR

    name = '.'.join((match.group('ns'), match.group('coll'), match.group('plugin_name')))

    return PluginInfo(resolved_name=name, type=plugin_type)
