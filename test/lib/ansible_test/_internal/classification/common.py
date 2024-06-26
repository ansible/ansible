"""Common classification code used by multiple languages."""
from __future__ import annotations

import os

from ..data import (
    data_context,
)


def resolve_csharp_ps_util(import_name: str, path: str) -> str:
    """Return the fully qualified name of the given import if possible, otherwise return the original import name."""
    if data_context().content.is_ansible or not import_name.startswith('.'):
        # We don't support relative paths for builtin utils, there's no point.
        return import_name

    packages = import_name.split('.')
    module_packages = path.split(os.path.sep)

    for package in packages:
        if not module_packages or package:
            break
        del module_packages[-1]

    return 'ansible_collections.%s%s' % (data_context().content.prefix,
                                         '.'.join(module_packages + [p for p in packages if p]))
