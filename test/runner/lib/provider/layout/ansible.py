"""Layout provider for Ansible source."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

import lib.types as t

from . import (
    ContentLayout,
    LayoutProvider,
)


class AnsibleLayout(LayoutProvider):
    """Layout provider for Ansible source."""
    @staticmethod
    def is_content_root(path):  # type: (str) -> bool
        """Return True if the given path is a content root for this provider."""
        return os.path.exists(os.path.join(path, 'setup.py')) and os.path.exists(os.path.join(path, 'bin/ansible-test'))

    def create(self, root, paths):  # type: (str, t.List[str]) -> ContentLayout
        """Create a Layout using the given root and paths."""
        plugin_types = sorted(set(p.split('/')[3] for p in paths if re.search(r'^lib/ansible/plugins/[^/]+/', p)))
        provider_types = sorted(set(p.split('/')[4] for p in paths if re.search(r'^test/runner/lib/provider/[^/]+/', p)))

        plugin_paths = dict((p, os.path.join('lib/ansible/plugins', p)) for p in plugin_types)
        provider_paths = dict((p, os.path.join('test/runner/lib/provider', p)) for p in provider_types)

        plugin_paths.update(dict(
            modules='lib/ansible/modules',
            module_utils='lib/ansible/module_utils',
        ))

        return ContentLayout(root,
                             paths,
                             plugin_paths=plugin_paths,
                             provider_paths=provider_paths,
                             code_path='lib/ansible',
                             util_path='test/utils',
                             unit_path='test/units',
                             unit_module_path='test/units/modules',
                             unit_module_utils_path='test/units/module_utils',
                             integration_path='test/integration',
                             )
