"""Layout provider for Ansible source."""
from __future__ import annotations

import os
import pathlib

from . import (
    ContentLayout,
    LayoutProvider,
)

from ...util import (
    ANSIBLE_ROOT,
    ApplicationError,
)


class AnsibleLayout(LayoutProvider):
    """Layout provider for Ansible source."""

    @staticmethod
    def is_content_root(path: str) -> bool:
        """Return True if the given path is a content root for this provider."""
        expected_paths = (
            'setup.py',
            'bin/ansible-test',
        )

        if not all(pathlib.Path(path, expected_path).exists() for expected_path in expected_paths):
            return False

        if path != ANSIBLE_ROOT:
            raise ApplicationError(f'Cannot test Ansible source at "{path}" using ansible-test from "{ANSIBLE_ROOT}".\n\n'
                                   f'Did you intend to run "{path}/bin/ansible-test" instead?')

        return True

    def create(self, root: str, paths: list[str]) -> ContentLayout:
        """Create a Layout using the given root and paths."""
        plugin_paths = dict((p, os.path.join('lib/ansible/plugins', p)) for p in self.PLUGIN_TYPES)

        plugin_paths.update(
            modules='lib/ansible/modules',
            module_utils='lib/ansible/module_utils',
        )

        return ContentLayout(
            root,
            paths,
            plugin_paths=plugin_paths,
            collection=None,
            test_path='test',
            results_path='test/results',
            sanity_path='test/sanity',
            sanity_messages=None,
            integration_path='test/integration',
            integration_targets_path='test/integration/targets',
            integration_vars_path='test/integration/integration_config.yml',
            integration_messages=None,
            unit_path='test/units',
            unit_module_path='test/units/modules',
            unit_module_utils_path='test/units/module_utils',
            unit_messages=None,
        )
