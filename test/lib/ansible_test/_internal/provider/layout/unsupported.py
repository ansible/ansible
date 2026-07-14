"""Layout provider for an unsupported directory layout."""

from __future__ import annotations

from . import (
    ContentLayout,
    LayoutProvider,
)


class UnsupportedLayout(LayoutProvider):
    """Layout provider for an unsupported directory layout."""

    sequence = 0  # disable automatic detection

    @staticmethod
    def is_content_root(path: str) -> bool:
        """Return True if the given path is a content root for this provider."""
        return False

    def create(self, root: str, paths: list[str]) -> ContentLayout:
        """Create a Layout using the given root and paths."""
        plugin_paths = dict((p, p) for p in self.PLUGIN_TYPES)

        return ContentLayout(
            root,
            paths,
            plugin_paths=plugin_paths,
            collection=None,
            test_path='',
            results_path='',
            sanity_path='',
            sanity_messages=None,
            integration_path='',
            integration_targets_path='',
            integration_vars_path='',
            integration_messages=None,
            unit_path='',
            unit_module_path='',
            unit_module_utils_path='',
            unit_messages=None,
            unsupported=True,
        )
