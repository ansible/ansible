"""Context information for the current invocation of ansible-test."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from . import types as t

from .util import (
    ApplicationError,
    import_plugins,
    ANSIBLE_ROOT,
    is_subdir,
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

from .provider.layout import (
    ContentLayout,
    InstallLayout,
    LayoutProvider,
)


class UnexpectedSourceRoot(ApplicationError):
    """Exception generated when a source root is found below a layout root."""
    def __init__(self, source_root, layout_root):  # type: (str, str) -> None
        super(UnexpectedSourceRoot, self).__init__('Source root "%s" cannot be below layout root "%s".' % (source_root, layout_root))

        self.source_root = source_root
        self.layout_root = layout_root


class DataContext:
    """Data context providing details about the current execution environment for ansible-test."""
    def __init__(self):
        content_path = os.environ.get('ANSIBLE_TEST_CONTENT_ROOT')
        current_path = os.getcwd()

        self.__layout_providers = get_path_provider_classes(LayoutProvider)
        self.__source_providers = get_path_provider_classes(SourceProvider)
        self.payload_callbacks = []  # type: t.List[t.Callable[t.List[t.Tuple[str, str]], None]]

        if content_path:
            content = self.create_content_layout(self.__layout_providers, self.__source_providers, content_path, False)

            if content.is_ansible:
                install = content
            else:
                install = None
        elif is_subdir(current_path, ANSIBLE_ROOT):
            content = self.create_content_layout(self.__layout_providers, self.__source_providers, ANSIBLE_ROOT, False)
            install = InstallLayout(ANSIBLE_ROOT, content.all_files())
        else:
            content = self.create_content_layout(self.__layout_providers, self.__source_providers, current_path, True)
            install = None

        self.__install = install  # type: t.Optional[InstallLayout]
        self.content = content  # type: ContentLayout

    @staticmethod
    def create_content_layout(layout_providers,  # type: t.List[t.Type[LayoutProvider]]
                              source_providers,  # type: t.List[t.Type[SourceProvider]]
                              root,  # type: str
                              walk,  # type: bool
                              ):  # type: (...) -> ContentLayout
        """Create a content layout using the given providers and root path."""
        layout_provider = find_path_provider(LayoutProvider, layout_providers, root, walk)

        try:
            source_provider = find_path_provider(SourceProvider, source_providers, root, walk)
        except ProviderNotFoundForPath:
            source_provider = UnversionedSource(layout_provider.root)

        if source_provider.root != layout_provider.root and is_subdir(source_provider.root, layout_provider.root):
            raise UnexpectedSourceRoot(source_provider.root, layout_provider.root)

        layout = layout_provider.create(layout_provider.root, source_provider.get_paths(layout_provider.root))

        return layout

    @staticmethod
    def create_install_layout(source_providers):  # type: (t.List[t.Type[SourceProvider]]) -> InstallLayout
        """Create an install layout using the given source provider."""
        try:
            source_provider = find_path_provider(SourceProvider, source_providers, ANSIBLE_ROOT, False)
        except ProviderNotFoundForPath:
            source_provider = UnversionedSource(ANSIBLE_ROOT)

        paths = source_provider.get_paths(ANSIBLE_ROOT)

        return InstallLayout(ANSIBLE_ROOT, paths)

    @property
    def install(self):  # type: () -> InstallLayout
        """Return the install context, loaded on demand."""
        if not self.__install:
            self.__install = self.create_install_layout(self.__source_providers)

        return self.__install

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
        raise ApplicationError('''The current working directory must be at or below one of:

 - Ansible source: %s/
 - Ansible collection: {...}/ansible_collections/{namespace}/{collection}/

Current working directory: %s''' % (ANSIBLE_ROOT, os.getcwd()))

    return context


def data_context():  # type: () -> DataContext
    """Return the current data context."""
    try:
        return data_context.instance
    except AttributeError:
        data_context.instance = data_init()
        return data_context.instance
