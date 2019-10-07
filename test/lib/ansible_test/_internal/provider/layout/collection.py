"""Layout provider for Ansible collections."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ... import types as t

from . import (
    ContentLayout,
    LayoutProvider,
    CollectionDetail,
    LayoutMessages,
)


class CollectionLayout(LayoutProvider):
    """Layout provider for Ansible collections."""
    __module_path = 'plugins/modules'
    __unit_path = 'test/unit'

    @staticmethod
    def is_content_root(path):  # type: (str) -> bool
        """Return True if the given path is a content root for this provider."""
        if os.path.basename(os.path.dirname(os.path.dirname(path))) == 'ansible_collections':
            return True

        return False

    def create(self, root, paths):  # type: (str, t.List[str]) -> ContentLayout
        """Create a Layout using the given root and paths."""
        plugin_paths = dict((p, os.path.join('plugins', p)) for p in self.PLUGIN_TYPES)

        collection_root = os.path.dirname(os.path.dirname(root))
        collection_dir = os.path.relpath(root, collection_root)
        collection_namespace, collection_name = collection_dir.split(os.sep)

        collection_root = os.path.dirname(collection_root)

        sanity_messages = LayoutMessages()
        integration_messages = LayoutMessages()
        unit_messages = LayoutMessages()

        # these apply to all test commands
        self.__check_test_path(paths, sanity_messages)
        self.__check_test_path(paths, integration_messages)
        self.__check_test_path(paths, unit_messages)

        # these apply to specific test commands
        integration_targets_path = self.__check_integration_path(paths, integration_messages)
        self.__check_unit_path(paths, unit_messages)

        return ContentLayout(root,
                             paths,
                             plugin_paths=plugin_paths,
                             collection=CollectionDetail(
                                 name=collection_name,
                                 namespace=collection_namespace,
                                 root=collection_root,
                             ),
                             test_path='tests',
                             results_path='tests/output',
                             sanity_path='tests/sanity',
                             sanity_messages=sanity_messages,
                             integration_path='tests/integration',
                             integration_targets_path=integration_targets_path.rstrip(os.path.sep),
                             integration_vars_path='tests/integration/integration_config.yml',
                             integration_messages=integration_messages,
                             unit_path='tests/unit',
                             unit_module_path='tests/unit/plugins/modules',
                             unit_module_utils_path='tests/unit/plugins/module_utils',
                             unit_messages=unit_messages,
                             )

    @staticmethod
    def __check_test_path(paths, messages):  # type: (t.List[str], LayoutMessages) -> None
        modern_test_path = 'tests/'
        modern_test_path_found = any(path.startswith(modern_test_path) for path in paths)
        legacy_test_path = 'test/'
        legacy_test_path_found = any(path.startswith(legacy_test_path) for path in paths)

        if modern_test_path_found and legacy_test_path_found:
            messages.warning.append('Ignoring tests in "%s" in favor of "%s".' % (legacy_test_path, modern_test_path))
        elif legacy_test_path_found:
            messages.warning.append('Ignoring tests in "%s" that should be in "%s".' % (legacy_test_path, modern_test_path))

    @staticmethod
    def __check_integration_path(paths, messages):  # type: (t.List[str], LayoutMessages) -> str
        modern_integration_path = 'roles/test/'
        modern_integration_path_found = any(path.startswith(modern_integration_path) for path in paths)
        legacy_integration_path = 'tests/integration/targets/'
        legacy_integration_path_found = any(path.startswith(legacy_integration_path) for path in paths)

        if modern_integration_path_found and legacy_integration_path_found:
            messages.warning.append('Ignoring tests in "%s" in favor of "%s".' % (legacy_integration_path, modern_integration_path))
            integration_targets_path = modern_integration_path
        elif legacy_integration_path_found:
            messages.info.append('Falling back to tests in "%s" because "%s" was not found.' % (legacy_integration_path, modern_integration_path))
            integration_targets_path = legacy_integration_path
        elif modern_integration_path_found:
            messages.info.append('Loading tests from "%s".' % modern_integration_path)
            integration_targets_path = modern_integration_path
        else:
            messages.error.append('Cannot run integration tests without "%s" or "%s".' % (modern_integration_path, legacy_integration_path))
            integration_targets_path = modern_integration_path

        return integration_targets_path

    @staticmethod
    def __check_unit_path(paths, messages):  # type: (t.List[str], LayoutMessages) -> None
        modern_unit_path = 'tests/unit/'
        modern_unit_path_found = any(path.startswith(modern_unit_path) for path in paths)
        legacy_unit_path = 'tests/units/'  # test/units/ will be covered by the warnings for test/ vs tests/
        legacy_unit_path_found = any(path.startswith(legacy_unit_path) for path in paths)

        if modern_unit_path_found and legacy_unit_path_found:
            messages.warning.append('Ignoring tests in "%s" in favor of "%s".' % (legacy_unit_path, modern_unit_path))
        elif legacy_unit_path_found:
            messages.warning.append('Rename "%s" to "%s" to run unit tests.' % (legacy_unit_path, modern_unit_path))
        elif modern_unit_path_found:
            pass  # unit tests only run from one directory so no message is needed
        else:
            messages.error.append('Cannot run unit tests without "%s".' % modern_unit_path)
