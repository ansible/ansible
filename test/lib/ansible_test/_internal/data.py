"""Context information for the current invocation of ansible-test."""
from __future__ import annotations

import collections.abc as c
import dataclasses
import os
import typing as t

from .util import (
    ApplicationError,
    import_plugins,
    is_subdir,
    ANSIBLE_LIB_ROOT,
    ANSIBLE_TEST_ROOT,
    ANSIBLE_SOURCE_ROOT,
    display,
    cache,
)

from .provider import (
    find_path_provider,
    get_path_provider_classes,
    ProviderNotFoundForPath,
)

from .provider.source import (
    SourceProvider,
)

from .provider.source.unversioned import (
    UnversionedSource,
)

from .provider.source.installed import (
    InstalledSource,
)

from .provider.source.unsupported import (
    UnsupportedSource,
)

from .provider.layout import (
    ContentLayout,
    LayoutProvider,
)

from .provider.layout.unsupported import (
    UnsupportedLayout,
)


@dataclasses.dataclass(frozen=True)
class PayloadConfig:
    """Configuration required to build a source tree payload for delegation."""

    files: list[tuple[str, str]]
    permissions: dict[str, int]


class DataContext:
    """Data context providing details about the current execution environment for ansible-test."""

    def __init__(self) -> None:
        content_path = os.environ.get('ANSIBLE_TEST_CONTENT_ROOT')
        current_path = os.getcwd()

        layout_providers = get_path_provider_classes(LayoutProvider)
        source_providers = get_path_provider_classes(SourceProvider)

        self.__layout_providers = layout_providers
        self.__source_providers = source_providers
        self.__ansible_source: t.Optional[tuple[tuple[str, str], ...]] = None

        self.payload_callbacks: list[c.Callable[[PayloadConfig], None]] = []

        if content_path:
            content, source_provider = self.__create_content_layout(layout_providers, source_providers, content_path, False)
        elif ANSIBLE_SOURCE_ROOT and is_subdir(current_path, ANSIBLE_SOURCE_ROOT):
            content, source_provider = self.__create_content_layout(layout_providers, source_providers, ANSIBLE_SOURCE_ROOT, False)
        else:
            content, source_provider = self.__create_content_layout(layout_providers, source_providers, current_path, True)

        self.content: ContentLayout = content
        self.source_provider = source_provider

    def create_collection_layouts(self) -> list[ContentLayout]:
        """
        Return a list of collection layouts, one for each collection in the same collection root as the current collection layout.
        An empty list is returned if the current content layout is not a collection layout.
        """
        layout = self.content
        collection = layout.collection

        if not collection:
            return []

        root_path = os.path.join(collection.root, 'ansible_collections')
        display.info('Scanning collection root: %s' % root_path, verbosity=1)
        namespace_names = sorted(name for name in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, name)))
        collections = []

        for namespace_name in namespace_names:
            namespace_path = os.path.join(root_path, namespace_name)
            collection_names = sorted(name for name in os.listdir(namespace_path) if os.path.isdir(os.path.join(namespace_path, name)))

            for collection_name in collection_names:
                collection_path = os.path.join(namespace_path, collection_name)

                if collection_path == os.path.join(collection.root, collection.directory):
                    collection_layout = layout
                else:
                    collection_layout = self.__create_content_layout(self.__layout_providers, self.__source_providers, collection_path, False)[0]

                file_count = len(collection_layout.all_files())

                if not file_count:
                    continue

                display.info('Including collection: %s (%d files)' % (collection_layout.collection.full_name, file_count), verbosity=1)
                collections.append(collection_layout)

        return collections

    @staticmethod
    def __create_content_layout(
        layout_providers: list[t.Type[LayoutProvider]],
        source_providers: list[t.Type[SourceProvider]],
        root: str,
        walk: bool,
    ) -> t.Tuple[ContentLayout, SourceProvider]:
        """Create a content layout using the given providers and root path."""
        try:
            layout_provider = find_path_provider(LayoutProvider, layout_providers, root, walk)
        except ProviderNotFoundForPath:
            layout_provider = UnsupportedLayout(root)

        try:
            # Begin the search for the source provider at the layout provider root.
            # This intentionally ignores version control within subdirectories of the layout root, a condition which was previously an error.
            # Doing so allows support for older git versions for which it is difficult to distinguish between a super project and a sub project.
            # It also provides a better user experience, since the solution for the user would effectively be the same -- to remove the nested version control.
            if isinstance(layout_provider, UnsupportedLayout):
                source_provider: SourceProvider = UnsupportedSource(layout_provider.root)
            else:
                source_provider = find_path_provider(SourceProvider, source_providers, layout_provider.root, walk)
        except ProviderNotFoundForPath:
            source_provider = UnversionedSource(layout_provider.root)

        layout = layout_provider.create(layout_provider.root, source_provider.get_paths(layout_provider.root))

        return layout, source_provider

    def __create_ansible_source(self):
        """Return a tuple of Ansible source files with both absolute and relative paths."""
        if not ANSIBLE_SOURCE_ROOT:
            sources = []

            source_provider = InstalledSource(ANSIBLE_LIB_ROOT)
            sources.extend((os.path.join(source_provider.root, path), os.path.join('lib', 'ansible', path))
                           for path in source_provider.get_paths(source_provider.root))

            source_provider = InstalledSource(ANSIBLE_TEST_ROOT)
            sources.extend((os.path.join(source_provider.root, path), os.path.join('test', 'lib', 'ansible_test', path))
                           for path in source_provider.get_paths(source_provider.root))

            return tuple(sources)

        if self.content.is_ansible:
            return tuple((os.path.join(self.content.root, path), path) for path in self.content.all_files())

        try:
            source_provider = find_path_provider(SourceProvider, self.__source_providers, ANSIBLE_SOURCE_ROOT, False)
        except ProviderNotFoundForPath:
            source_provider = UnversionedSource(ANSIBLE_SOURCE_ROOT)

        return tuple((os.path.join(source_provider.root, path), path) for path in source_provider.get_paths(source_provider.root))

    @property
    def ansible_source(self) -> tuple[tuple[str, str], ...]:
        """Return a tuple of Ansible source files with both absolute and relative paths."""
        if not self.__ansible_source:
            self.__ansible_source = self.__create_ansible_source()

        return self.__ansible_source

    def register_payload_callback(self, callback: c.Callable[[PayloadConfig], None]) -> None:
        """Register the given payload callback."""
        self.payload_callbacks.append(callback)

    def check_layout(self) -> None:
        """Report an error if the layout is unsupported."""
        if self.content.unsupported:
            raise ApplicationError(self.explain_working_directory())

    def explain_working_directory(self) -> str:
        """Return a message explaining the working directory requirements."""
        blocks = [
            'The current working directory must be within the source tree being tested.',
            '',
        ]

        if ANSIBLE_SOURCE_ROOT:
            blocks.append(f'Testing Ansible: {ANSIBLE_SOURCE_ROOT}/')
            blocks.append('')

        cwd = os.getcwd()

        blocks.append('Testing an Ansible collection: {...}/ansible_collections/{namespace}/{collection}/')
        blocks.append('Example #1: community.general -> ~/code/ansible_collections/community/general/')
        blocks.append('Example #2: ansible.util -> ~/.ansible/collections/ansible_collections/ansible/util/')
        blocks.append('')
        blocks.append(f'Current working directory: {cwd}/')

        if os.path.basename(os.path.dirname(cwd)) == 'ansible_collections':
            blocks.append(f'Expected parent directory: {os.path.dirname(cwd)}/{{namespace}}/{{collection}}/')
        elif os.path.basename(cwd) == 'ansible_collections':
            blocks.append(f'Expected parent directory: {cwd}/{{namespace}}/{{collection}}/')
        elif 'ansible_collections' not in cwd.split(os.path.sep):
            blocks.append('No "ansible_collections" parent directory was found.')

        if isinstance(self.content.unsupported, list):
            blocks.extend(self.content.unsupported)

        message = '\n'.join(blocks)

        return message


@cache
def data_context() -> DataContext:
    """Initialize provider plugins."""
    provider_types = (
        'layout',
        'source',
    )

    for provider_type in provider_types:
        import_plugins('provider/%s' % provider_type)

    context = DataContext()

    return context


@dataclasses.dataclass(frozen=True)
class PluginInfo:
    """Information about an Ansible plugin."""

    plugin_type: str
    name: str
    paths: list[str]


@cache
def content_plugins() -> dict[str, dict[str, PluginInfo]]:
    """
    Analyze content.
    The primary purpose of this analysis is to facilitate mapping of integration tests to the plugin(s) they are intended to test.
    """
    plugins: dict[str, dict[str, PluginInfo]] = {}

    for plugin_type, plugin_directory in data_context().content.plugin_paths.items():
        plugin_paths = sorted(data_context().content.walk_files(plugin_directory))
        plugin_directory_offset = len(plugin_directory.split(os.path.sep))

        plugin_files: dict[str, list[str]] = {}

        for plugin_path in plugin_paths:
            plugin_filename = os.path.basename(plugin_path)
            plugin_parts = plugin_path.split(os.path.sep)[plugin_directory_offset:-1]

            if plugin_filename == '__init__.py':
                if plugin_type != 'module_utils':
                    continue
            else:
                plugin_name = os.path.splitext(plugin_filename)[0]

                if data_context().content.is_ansible and plugin_type == 'modules':
                    plugin_name = plugin_name.lstrip('_')

                plugin_parts.append(plugin_name)

            plugin_name = '.'.join(plugin_parts)

            plugin_files.setdefault(plugin_name, []).append(plugin_filename)

        plugins[plugin_type] = {plugin_name: PluginInfo(
            plugin_type=plugin_type,
            name=plugin_name,
            paths=paths,
        ) for plugin_name, paths in plugin_files.items()}

    return plugins
