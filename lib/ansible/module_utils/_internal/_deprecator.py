from __future__ import annotations

import re
import pathlib
import sys
import typing as t

from ansible.module_utils._internal import _stack, _messages, _validation, _plugin_info


def deprecator_from_collection_name(collection_name: str | None) -> _messages.PluginInfo | None:
    """Returns an instance with the special `collection` type to refer to a non-plugin or ambiguous caller within a collection."""
    # CAUTION: This function is exposed in public API as ansible.module_utils.datatag.deprecator_from_collection_name.

    if not collection_name:
        return None

    _validation.validate_collection_name(collection_name)

    return _messages.PluginInfo(
        resolved_name=collection_name,
        type=None,
    )


def get_best_deprecator(*, deprecator: _messages.PluginInfo | None = None, collection_name: str | None = None) -> _messages.PluginInfo:
    """Return the best-available `PluginInfo` for the caller of this method."""
    _skip_stackwalk = True

    if deprecator and collection_name:
        raise ValueError('Specify only one of `deprecator` or `collection_name`.')

    return deprecator or deprecator_from_collection_name(collection_name) or get_caller_plugin_info() or INDETERMINATE_DEPRECATOR


def get_caller_plugin_info() -> _messages.PluginInfo | None:
    """Try to get `PluginInfo` for the caller of this method, ignoring marked infrastructure stack frames."""
    _skip_stackwalk = True

    if frame_info := _stack.caller_frame():
        return _path_as_plugininfo(frame_info.filename)

    return None  # pragma: nocover


def _path_as_plugininfo(path: str) -> _messages.PluginInfo | None:
    """Return a `PluginInfo` instance if the provided `path` refers to a plugin."""
    return _path_as_core_plugininfo(path) or _path_as_collection_plugininfo(path)


def _path_as_core_plugininfo(path: str) -> _messages.PluginInfo | None:
    """Return a `PluginInfo` instance if the provided `path` refers to a core plugin."""
    try:
        relpath = str(pathlib.Path(path).relative_to(_ANSIBLE_MODULE_BASE_PATH))
    except ValueError:
        return None  # not ansible-core

    namespace = 'ansible.builtin'

    if match := re.match(r'plugins/(?P<plugin_type>\w+)/(?P<plugin_name>\w+)', relpath):
        plugin_name = match.group("plugin_name")
        plugin_type = _plugin_info.normalize_plugin_type(match.group("plugin_type"))

        if plugin_type not in _DEPRECATOR_PLUGIN_TYPES:
            # The plugin type isn't a known deprecator type, so we have to assume the caller is intermediate code.
            # We have no way of knowing if the intermediate code is deprecating its own feature, or acting on behalf of another plugin.
            # Callers in this case need to identify the deprecating plugin name, otherwise only ansible-core will be reported.
            # Reporting ansible-core is never wrong, it just may be missing an additional detail (plugin name) in the "on behalf of" case.
            return ANSIBLE_CORE_DEPRECATOR

        if plugin_name == '__init__':
            # The plugin type is known, but the caller isn't a specific plugin -- instead, it's core plugin infrastructure (the base class).
            return _messages.PluginInfo(resolved_name=namespace, type=plugin_type)
    elif match := re.match(r'modules/(?P<module_name>\w+)', relpath):
        # AnsiballZ Python package for core modules
        plugin_name = match.group("module_name")
        plugin_type = _messages.PluginType.MODULE
    elif match := re.match(r'legacy/(?P<module_name>\w+)', relpath):
        # AnsiballZ Python package for non-core library/role modules
        namespace = 'ansible.legacy'

        plugin_name = match.group("module_name")
        plugin_type = _messages.PluginType.MODULE
    else:
        return ANSIBLE_CORE_DEPRECATOR  # non-plugin core path, safe to use ansible-core for the same reason as the non-deprecator plugin type case above

    name = f'{namespace}.{plugin_name}'

    return _messages.PluginInfo(resolved_name=name, type=plugin_type)


def _path_as_collection_plugininfo(path: str) -> _messages.PluginInfo | None:
    """Return a `PluginInfo` instance if the provided `path` refers to a collection plugin."""
    if not (match := re.search(r'/ansible_collections/(?P<ns>\w+)/(?P<coll>\w+)/plugins/(?P<plugin_type>\w+)/(?P<plugin_name>\w+)', path)):
        return None

    plugin_type = _plugin_info.normalize_plugin_type(match.group('plugin_type'))

    if plugin_type in _AMBIGUOUS_DEPRECATOR_PLUGIN_TYPES:
        # We're able to detect the namespace, collection and plugin type -- but we have no way to identify the plugin name currently.
        # To keep things simple we'll fall back to just identifying the namespace and collection.
        # In the future we could improve the detection and/or make it easier for a caller to identify the plugin name.
        return deprecator_from_collection_name('.'.join((match.group('ns'), match.group('coll'))))

    if plugin_type not in _DEPRECATOR_PLUGIN_TYPES:
        # The plugin type isn't a known deprecator type, so we have to assume the caller is intermediate code.
        # We have no way of knowing if the intermediate code is deprecating its own feature, or acting on behalf of another plugin.
        # Callers in this case need to identify the deprecator to avoid ambiguity, since it could be the same collection or another collection.
        return INDETERMINATE_DEPRECATOR

    name = '.'.join((match.group('ns'), match.group('coll'), match.group('plugin_name')))

    # DTFIX-FUTURE: deprecations from __init__ will be incorrectly attributed to a plugin of that name

    return _messages.PluginInfo(resolved_name=name, type=plugin_type)


_ANSIBLE_MODULE_BASE_PATH: t.Final = pathlib.Path(sys.modules['ansible'].__file__).parent
"""Runtime-detected base path of the `ansible` Python package to distinguish between Ansible-owned and external code."""

ANSIBLE_CORE_DEPRECATOR: t.Final = deprecator_from_collection_name('ansible.builtin')
"""Singleton `PluginInfo` instance for ansible-core callers where the plugin can/should not be identified in messages."""

INDETERMINATE_DEPRECATOR: t.Final = _messages.PluginInfo(resolved_name=None, type=None)
"""Singleton `PluginInfo` instance for indeterminate deprecator."""

_DEPRECATOR_PLUGIN_TYPES: t.Final = frozenset(
    {
        _messages.PluginType.ACTION,
        _messages.PluginType.BECOME,
        _messages.PluginType.CACHE,
        _messages.PluginType.CALLBACK,
        _messages.PluginType.CLICONF,
        _messages.PluginType.CONNECTION,
        # DOC_FRAGMENTS - no code execution
        # FILTER - basename inadequate to identify plugin
        _messages.PluginType.HTTPAPI,
        _messages.PluginType.INVENTORY,
        _messages.PluginType.LOOKUP,
        _messages.PluginType.MODULE,  # only for collections
        _messages.PluginType.NETCONF,
        _messages.PluginType.SHELL,
        _messages.PluginType.STRATEGY,
        _messages.PluginType.TERMINAL,
        # TEST - basename inadequate to identify plugin
        _messages.PluginType.VARS,
    }
)
"""Plugin types which are valid for identifying a deprecator for deprecation purposes."""

_AMBIGUOUS_DEPRECATOR_PLUGIN_TYPES: t.Final = frozenset(
    {
        _messages.PluginType.FILTER,
        _messages.PluginType.TEST,
    }
)
"""Plugin types for which basename cannot be used to identify the plugin name."""
