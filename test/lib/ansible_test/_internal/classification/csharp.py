"""Analyze C# import statements."""
from __future__ import annotations

import os
import re

from ..io import (
    open_text_file,
)

from ..util import (
    display,
)

from .common import (
    resolve_csharp_ps_util,
)

from ..data import (
    data_context,
)

from ..target import (
    TestTarget,
)


def get_csharp_module_utils_imports(powershell_targets: list[TestTarget], csharp_targets: list[TestTarget]) -> dict[str, set[str]]:
    """Return a dictionary of module_utils names mapped to sets of powershell file paths."""
    module_utils = enumerate_module_utils()

    imports_by_target_path = {}

    for target in powershell_targets:
        imports_by_target_path[target.path] = extract_csharp_module_utils_imports(target.path, module_utils, False)

    for target in csharp_targets:
        imports_by_target_path[target.path] = extract_csharp_module_utils_imports(target.path, module_utils, True)

    imports: dict[str, set[str]] = {module_util: set() for module_util in module_utils}

    for target_path, modules in imports_by_target_path.items():
        for module_util in modules:
            imports[module_util].add(target_path)

    for module_util in sorted(imports):
        if not imports[module_util]:
            display.warning('No imports found which use the "%s" module_util.' % module_util)

    return imports


def get_csharp_module_utils_name(path: str) -> str:
    """Return a namespace and name from the given module_utils path."""
    base_path = data_context().content.module_utils_csharp_path

    if data_context().content.collection:
        prefix = 'ansible_collections.' + data_context().content.collection.prefix + 'plugins.module_utils.'
    else:
        prefix = ''

    name = prefix + os.path.splitext(os.path.relpath(path, base_path))[0].replace(os.path.sep, '.')

    return name


def enumerate_module_utils() -> set[str]:
    """Return a set of available module_utils imports."""
    return set(get_csharp_module_utils_name(p)
               for p in data_context().content.walk_files(data_context().content.module_utils_csharp_path)
               if os.path.splitext(p)[1] == '.cs')


def extract_csharp_module_utils_imports(path: str, module_utils: set[str], is_pure_csharp: bool) -> set[str]:
    """Return a set of module_utils imports found in the specified source file."""
    imports = set()
    if is_pure_csharp:
        pattern = re.compile(r'(?i)^using\s((?:Ansible|AnsibleCollections)\..+);$')
    else:
        pattern = re.compile(r'(?i)^#\s*ansiblerequires\s+-csharputil\s+((?:Ansible|ansible.collections|\.)\..+)')

    with open_text_file(path) as module_file:
        for line_number, line in enumerate(module_file, 1):
            match = re.search(pattern, line)

            if not match:
                continue

            import_name = resolve_csharp_ps_util(match.group(1), path)

            if import_name in module_utils:
                imports.add(import_name)
            elif data_context().content.is_ansible or \
                    import_name.startswith('ansible_collections.%s' % data_context().content.prefix):
                display.warning('%s:%d Invalid module_utils import: %s' % (path, line_number, import_name))

    return imports
