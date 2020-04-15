"""Context information for the current invocation of ansible-test."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from . import types as t

from .util import (
    ApplicationError,
    import_plugins,
    is_subdir,
    ANSIBLE_LIB_ROOT,
    ANSIBLE_TEST_ROOT,
    ANSIBLE_SOURCE_ROOT,
    display,
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

from .provider.layout import (
    ContentLayout,
    LayoutProvider,
)


class DataContext:
    """Data context providing details about the current execution environment for ansible-test."""
    def __init__(self):
        content_path = os.environ.get('ANSIBLE_TEST_CONTENT_ROOT')
        current_path = os.getcwd()

        layout_providers = get_path_provider_classes(LayoutProvider)
        source_providers = get_path_provider_classes(SourceProvider)

        self.__layout_providers = layout_providers
        self.__source_providers = source_providers
        self.__ansible_source = None  # type: t.Optional[t.Tuple[t.Tuple[str, str], ...]]

        self.payload_callbacks = []  # type: t.List[t.Callable[t.List[t.Tuple[str, str]], None]]

        if content_path:
            content = self.__create_content_layout(layout_providers, source_providers, content_path, False)
        elif ANSIBLE_SOURCE_ROOT and is_subdir(current_path, ANSIBLE_SOURCE_ROOT):
            content = self.__create_content_layout(layout_providers, source_providers, ANSIBLE_SOURCE_ROOT, False)
        else:
            content = self.__create_content_layout(layout_providers, source_providers, current_path, True)

        self.content = content  # type: ContentLayout

    def create_collection_layouts(self):  # type: () -> t.List[ContentLayout]
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
                    collection_layout = self.__create_content_layout(self.__layout_providers, self.__source_providers, collection_path, False)

                file_count = len(collection_layout.all_files())

                if not file_count:
                    continue

                display.info('Including collection: %s (%d files)' % (collection_layout.collection.full_name, file_count), verbosity=1)
                collections.append(collection_layout)

        return collections

    @staticmethod
    def __create_content_layout(layout_providers,  # type: t.List[t.Type[LayoutProvider]]
                                source_providers,  # type: t.List[t.Type[SourceProvider]]
                                root,  # type: str
                                walk,  # type: bool
                                ):  # type: (...) -> ContentLayout
        """Create a content layout using the given providers and root path."""
        layout_provider = find_path_provider(LayoutProvider, layout_providers, root, walk)

        try:
            # Begin the search for the source provider at the layout provider root.
            # This intentionally ignores version control within subdirectories of the layout root, a condition which was previously an error.
            # Doing so allows support for older git versions for which it is difficult to distinguish between a super project and a sub project.
            # It also provides a better user experience, since the solution for the user would effectively be the same -- to remove the nested version control.
            source_provider = find_path_provider(SourceProvider, source_providers, layout_provider.root, walk)
        except ProviderNotFoundForPath:
            source_provider = UnversionedSource(layout_provider.root)

        layout = layout_provider.create(layout_provider.root, source_provider.get_paths(layout_provider.root))

        return layout

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
    def ansible_source(self):  # type: () -> t.Tuple[t.Tuple[str, str], ...]
        """Return a tuple of Ansible source files with both absolute and relative paths."""
        if not self.__ansible_source:
            self.__ansible_source = self.__create_ansible_source()

        return self.__ansible_source

    def register_payload_callback(self, callback):  # type: (t.Callable[t.List[t.Tuple[str, str]], None]) -> None
        """Register the given payload callback."""
        self.payload_callbacks.append(callback)


def data_init():  # type: () -> DataContext
    """Initialize provider plugins."""
    provider_types = (
        'layout',
        'source',
    )

    for provider_type in provider_types:
        import_plugins('provider/%s' % provider_type)

    try:
        context = DataContext()
    except ProviderNotFoundForPath:
        options = [
            ' - an Ansible collection: {...}/ansible_collections/{namespace}/{collection}/',
        ]

        if ANSIBLE_SOURCE_ROOT:
            options.insert(0, ' - the Ansible source: %s/' % ANSIBLE_SOURCE_ROOT)

        raise ApplicationError('''The current working directory must be at or below:

%s

Current working directory: %s''' % ('\n'.join(options), os.getcwd()))

    return context


def data_context():  # type: () -> DataContext
    """Return the current data context."""
    try:
        return data_context.instance
    except AttributeError:
        data_context.instance = data_init()
        return data_context.instance
