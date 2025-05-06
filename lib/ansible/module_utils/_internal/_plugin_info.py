from __future__ import annotations

import typing as t

from ..common import messages as _messages


class HasPluginInfo(t.Protocol):
    """Protocol to type-annotate and expose PluginLoader-set values."""

    @property
    def ansible_name(self) -> str | None:
        """Fully resolved plugin name."""

    @property
    def plugin_type(self) -> str:
        """Plugin type name."""


def get_plugin_info(value: HasPluginInfo) -> _messages.PluginInfo:
    """Utility method that returns a `PluginInfo` from an object implementing the `HasPluginInfo` protocol."""
    return _messages.PluginInfo(
        resolved_name=value.ansible_name,
        type=value.plugin_type,
    )
