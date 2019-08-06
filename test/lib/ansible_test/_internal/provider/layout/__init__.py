"""Code for finding content."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import abc
import collections
import os

from ... import types as t

from ...util import (
    ANSIBLE_ROOT,
)

from .. import (
    PathProvider,
)


class Layout:
    """Description of content locations and helper methods to access content."""
    def __init__(self,
                 root,  # type: str
                 paths,  # type: t.List[str]
                 ):  # type: (...) -> None
        self.root = root

        self.__paths = paths
        self.__tree = paths_to_tree(paths)

    def all_files(self):  # type: () -> t.List[str]
        """Return a list of all file paths."""
        return self.__paths

    def walk_files(self, directory):  # type: (str) -> t.List[str]
        """Return a list of file paths found recursively under the given directory."""
        parts = directory.rstrip(os.sep).split(os.sep)
        item = get_tree_item(self.__tree, parts)

        if not item:
            return []

        directories = collections.deque(item[0].values())

        files = list(item[1])

        while directories:
            item = directories.pop()
            directories.extend(item[0].values())
            files.extend(item[1])

        return files

    def get_dirs(self, directory):  # type: (str) -> t.List[str]
        """Return a list directory paths found directly under the given directory."""
        parts = directory.rstrip(os.sep).split(os.sep)
        item = get_tree_item(self.__tree, parts)
        return [os.path.join(directory, key) for key in item[0].keys()] if item else []

    def get_files(self, directory):  # type: (str) -> t.List[str]
        """Return a list of file paths found directly under the given directory."""
        parts = directory.rstrip(os.sep).split(os.sep)
        item = get_tree_item(self.__tree, parts)
        return item[1] if item else []


class InstallLayout(Layout):
    """Information about the current Ansible install."""


class ContentLayout(Layout):
    """Information about the current Ansible content being tested."""
    def __init__(self,
                 root,  # type: str
                 paths,  # type: t.List[str]
                 plugin_paths,  # type: t.Dict[str, str]
                 collection=None,  # type: t.Optional[CollectionDetail]
                 unit_path=None,  # type: t.Optional[str]
                 unit_module_path=None,  # type: t.Optional[str]
                 unit_module_utils_path=None,  # type: t.Optional[str]
                 ):  # type: (...) -> None
        super(ContentLayout, self).__init__(root, paths)

        self.plugin_paths = plugin_paths
        self.collection = collection
        self.unit_path = unit_path
        self.unit_module_path = unit_module_path
        self.unit_module_utils_path = unit_module_utils_path
        self.is_ansible = root == ANSIBLE_ROOT

    @property
    def prefix(self):  # type: () -> str
        """Return the collection prefix or an empty string if not a collection."""
        if self.collection:
            return self.collection.prefix

        return ''

    @property
    def module_path(self):  # type: () -> t.Optional[str]
        """Return the path where modules are found, if any."""
        return self.plugin_paths.get('modules')

    @property
    def module_utils_path(self):  # type: () -> t.Optional[str]
        """Return the path where module_utils are found, if any."""
        return self.plugin_paths.get('module_utils')

    @property
    def module_utils_powershell_path(self):  # type: () -> t.Optional[str]
        """Return the path where powershell module_utils are found, if any."""
        if self.is_ansible:
            return os.path.join(self.plugin_paths['module_utils'], 'powershell')

        return self.plugin_paths.get('module_utils')

    @property
    def module_utils_csharp_path(self):  # type: () -> t.Optional[str]
        """Return the path where csharp module_utils are found, if any."""
        if self.is_ansible:
            return os.path.join(self.plugin_paths['module_utils'], 'csharp')

        return self.plugin_paths.get('module_utils')


class CollectionDetail:
    """Details about the layout of the current collection."""
    def __init__(self,
                 name,  # type: str
                 namespace,  # type: str
                 root,  # type: str
                 prefix,  # type: str
                 ):  # type: (...) -> None
        self.name = name
        self.namespace = namespace
        self.root = root
        self.prefix = prefix
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
    )

    @abc.abstractmethod
    def create(self, root, paths):  # type: (str, t.List[str]) -> ContentLayout
        """Create a layout using the given root and paths."""


def paths_to_tree(paths):  # type: (t.List[str]) -> t.Tuple(t.Dict[str, t.Any], t.List[str])
    """Return a filesystem tree from the given list of paths."""
    tree = {}, []

    for path in paths:
        parts = path.split(os.sep)
        root = tree

        for part in parts[:-1]:
            if part not in root[0]:
                root[0][part] = {}, []

            root = root[0][part]

        root[1].append(path)

    return tree


def get_tree_item(tree, parts):  # type: (t.Tuple(t.Dict[str, t.Any], t.List[str]), t.List[str]) -> t.Optional[t.Tuple(t.Dict[str, t.Any], t.List[str])]
    """Return the portion of the tree found under the path given by parts, or None if it does not exist."""
    root = tree

    for part in parts:
        root = root[0].get(part)

        if not root:
            return None

    return root
