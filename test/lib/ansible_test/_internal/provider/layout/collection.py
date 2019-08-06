"""Layout provider for Ansible collections."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

from ... import types as t

from . import (
    ContentLayout,
    LayoutProvider,
    CollectionDetail,
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

        collection_prefix = '%s.%s.' % (collection_namespace, collection_name)
        collection_root = os.path.dirname(collection_root)

        return ContentLayout(root,
                             paths,
                             plugin_paths=plugin_paths,
                             collection=CollectionDetail(
                                 name=collection_name,
                                 namespace=collection_namespace,
                                 root=collection_root,
                                 prefix=collection_prefix,
                             ),
                             unit_path='test/unit',
                             unit_module_path='test/unit/plugins/modules',
                             unit_module_utils_path='test/unit/plugins/module_utils',
                             )
