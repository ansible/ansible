from __future__ import annotations

import typing as t

from ._ambient_context import AmbientContextBase
from ..common.messages import PluginInfo


class HasPluginInfo(t.Protocol):
    """Protocol to type-annotate and expose PluginLoader-set values."""

    @property
    def _load_name(self) -> str:
        """The requested name used to load the plugin."""

    @property
    def ansible_name(self) -> str:
        """Fully resolved plugin name."""

    @property
    def plugin_type(self) -> str:
        """Plugin type name."""


class PluginExecContext(AmbientContextBase):
    """Execution context that wraps all plugin invocations to allow infrastructure introspection of the currently-executing plugin instance."""

    def __init__(self, executing_plugin: HasPluginInfo) -> None:
        self._executing_plugin = executing_plugin

    @property
    def executing_plugin(self) -> HasPluginInfo:
        return self._executing_plugin

    @property
    def plugin_info(self) -> PluginInfo:
        return PluginInfo(
            requested_name=self._executing_plugin._load_name,
            resolved_name=self._executing_plugin.ansible_name,
            type=self._executing_plugin.plugin_type,
        )

    @classmethod
    def get_current_plugin_info(cls) -> PluginInfo | None:
        """Utility method to extract a PluginInfo for the currently executing plugin (or None if no plugin is executing)."""
        if ctx := cls.current(optional=True):
            return ctx.plugin_info

        return None
