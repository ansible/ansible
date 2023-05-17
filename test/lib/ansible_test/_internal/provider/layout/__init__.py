"""Code for finding content."""
from __future__ import annotations

import abc
import collections
import os
import typing as t

from ...util import (
    ANSIBLE_SOURCE_ROOT,
)

from .. import (
    PathProvider,
)


class Layout:
    """Description of content locations and helper methods to access content."""

    def __init__(
        self,
        root: str,
        paths: list[str],
    ) -> None:
        self.root = root

        self.__paths = paths  # contains both file paths and symlinked directory paths (ending with os.path.sep)
        self.__files = [path for path in paths if not path.endswith(os.path.sep)]  # contains only file paths
        self.__paths_tree = paths_to_tree(self.__paths)
        self.__files_tree = paths_to_tree(self.__files)

    def all_files(self, include_symlinked_directories: bool = False) -> list[str]:
        """Return a list of all file paths."""
        if include_symlinked_directories:
            return self.__paths

        return self.__files

    def walk_files(self, directory: str, include_symlinked_directories: bool = False) -> list[str]:
        """Return a list of file paths found recursively under the given directory."""
        if include_symlinked_directories:
            tree = self.__paths_tree
        else:
            tree = self.__files_tree

        parts = directory.rstrip(os.path.sep).split(os.path.sep)
        item = get_tree_item(tree, parts)

        if not item:
            return []

        directories = collections.deque(item[0].values())

        files = list(item[1])

        while directories:
            item = directories.pop()
            directories.extend(item[0].values())
            files.extend(item[1])

        return files

    def get_dirs(self, directory: str) -> list[str]:
        """Return a list directory paths found directly under the given directory."""
        parts = directory.rstrip(os.path.sep).split(os.path.sep)
        item = get_tree_item(self.__files_tree, parts)
        return [os.path.join(directory, key) for key in item[0].keys()] if item else []

    def get_files(self, directory: str) -> list[str]:
        """Return a list of file paths found directly under the given directory."""
        parts = directory.rstrip(os.path.sep).split(os.path.sep)
        item = get_tree_item(self.__files_tree, parts)
        return item[1] if item else []


class ContentLayout(Layout):
    """Information about the current Ansible content being tested."""

    def __init__(
        self,
        root: str,
        paths: list[str],
        plugin_paths: dict[str, str],
        collection: t.Optional[CollectionDetail],
        test_path: str,
        results_path: str,
        sanity_path: str,
        sanity_messages: t.Optional[LayoutMessages],
        integration_path: str,
        integration_targets_path: str,
        integration_vars_path: str,
        integration_messages: t.Optional[LayoutMessages],
        unit_path: str,
        unit_module_path: str,
        unit_module_utils_path: str,
        unit_messages: t.Optional[LayoutMessages],
        unsupported: bool | list[str] = False,
    ) -> None:
        super().__init__(root, paths)

        self.plugin_paths = plugin_paths
        self.collection = collection
        self.test_path = test_path
        self.results_path = results_path
        self.sanity_path = sanity_path
        self.sanity_messages = sanity_messages
        self.integration_path = integration_path
        self.integration_targets_path = integration_targets_path
        self.integration_vars_path = integration_vars_path
        self.integration_messages = integration_messages
        self.unit_path = unit_path
        self.unit_module_path = unit_module_path
        self.unit_module_utils_path = unit_module_utils_path
        self.unit_messages = unit_messages
        self.unsupported = unsupported

        self.is_ansible = root == ANSIBLE_SOURCE_ROOT

    @property
    def prefix(self) -> str:
        """Return the collection prefix or an empty string if not a collection."""
        if self.collection:
            return self.collection.prefix

        return ''

    @property
    def module_path(self) -> t.Optional[str]:
        """Return the path where modules are found, if any."""
        return self.plugin_paths.get('modules')

    @property
    def module_utils_path(self) -> t.Optional[str]:
        """Return the path where module_utils are found, if any."""
        return self.plugin_paths.get('module_utils')

    @property
    def module_utils_powershell_path(self) -> t.Optional[str]:
        """Return the path where powershell module_utils are found, if any."""
        if self.is_ansible:
            return os.path.join(self.plugin_paths['module_utils'], 'powershell')

        return self.plugin_paths.get('module_utils')

    @property
    def module_utils_csharp_path(self) -> t.Optional[str]:
        """Return the path where csharp module_utils are found, if any."""
        if self.is_ansible:
            return os.path.join(self.plugin_paths['module_utils'], 'csharp')

        return self.plugin_paths.get('module_utils')


class LayoutMessages:
    """Messages generated during layout creation that should be deferred for later display."""

    def __init__(self) -> None:
        self.info: list[str] = []
        self.warning: list[str] = []
        self.error: list[str] = []


class CollectionDetail:
    """Details about the layout of the current collection."""

    def __init__(
        self,
        name: str,
        namespace: str,
        root: str,
    ) -> None:
        self.name = name
        self.namespace = namespace
        self.root = root
        self.full_name = '%s.%s' % (namespace, name)
        self.prefix = '%s.' % self.full_name
        self.directory = os.path.join('ansible_collections', namespace, name)


class LayoutProvider(PathProvider):
    """Base class for layout providers."""

    PLUGIN_TYPES = (
        'action',
        'become',
        'cache',
        'callback',
        'cliconf',
        'connection',
        'doc_fragments',
        'filter',
        'httpapi',
        'inventory',
        'lookup',
        'module_utils',
        'modules',
        'netconf',
        'shell',
        'strategy',
        'terminal',
        'test',
        'vars',
        # The following are plugin directories not directly supported by ansible-core, but used in collections
        # (https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst#modules--plugins)
        'plugin_utils',
        'sub_plugins',
    )

    @abc.abstractmethod
    def create(self, root: str, paths: list[str]) -> ContentLayout:
        """Create a layout using the given root and paths."""


def paths_to_tree(paths: list[str]) -> tuple[dict[str, t.Any], list[str]]:
    """Return a filesystem tree from the given list of paths."""
    tree: tuple[dict[str, t.Any], list[str]] = {}, []

    for path in paths:
        parts = path.split(os.path.sep)
        root = tree

        for part in parts[:-1]:
            if part not in root[0]:
                root[0][part] = {}, []

            root = root[0][part]

        root[1].append(path)

    return tree


def get_tree_item(tree: tuple[dict[str, t.Any], list[str]], parts: list[str]) -> t.Optional[tuple[dict[str, t.Any], list[str]]]:
    """Return the portion of the tree found under the path given by parts, or None if it does not exist."""
    root = tree

    for part in parts:
        root = root[0].get(part)

        if not root:
            return None

    return root
