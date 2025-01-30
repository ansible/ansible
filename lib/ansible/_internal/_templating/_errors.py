from __future__ import annotations

from ansible.errors import AnsibleTemplatePluginError


class AnsibleTemplatePluginRuntimeError(AnsibleTemplatePluginError):
    """The specified template plugin (lookup/filter/test) raised an exception during execution."""

    def __init__(self, plugin_type: str, plugin_name: str) -> None:
        super().__init__(f'The {plugin_type} plugin {plugin_name!r} failed.')


class AnsibleTemplatePluginLoadError(AnsibleTemplatePluginError):
    """The specified template plugin (lookup/filter/test) failed to load."""

    def __init__(self, plugin_type: str, plugin_name: str) -> None:
        super().__init__(f'The {plugin_type} plugin {plugin_name!r} failed to load.')


class AnsibleTemplatePluginNotFoundError(AnsibleTemplatePluginError):
    """The specified template plugin (lookup/filter/test) was not found."""

    def __init__(self, plugin_type: str, plugin_name: str) -> None:
        super().__init__(f'The {plugin_type} plugin {plugin_name!r} was not found.')
