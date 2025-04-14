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


class AnsibleTemplatePluginNotFoundError(AnsibleTemplatePluginError, KeyError):
    """
    The specified template plugin (lookup/filter/test) was not found.
    This exception extends KeyError since Jinja filter/test resolution requires a KeyError to detect missing plugins.
    Jinja compilation fails if a non-KeyError is raised for a missing filter/test, even if the plugin will not be invoked (inconsistent with stock Jinja).
    """

    def __init__(self, plugin_type: str, plugin_name: str) -> None:
        super().__init__(f'The {plugin_type} plugin {plugin_name!r} was not found.')
