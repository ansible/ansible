"""Analyze C# import statements."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

from .util import (
    display,
)

from .data import (
    data_context,
)


def get_csharp_module_utils_imports(powershell_targets, csharp_targets):
    """Return a dictionary of module_utils names mapped to sets of powershell file paths.
    :type powershell_targets: list[TestTarget] - C# files
    :type csharp_targets: list[TestTarget] - PS files
    :rtype: dict[str, set[str]]
    """

    module_utils = enumerate_module_utils()

    imports_by_target_path = {}

    for target in powershell_targets:
        imports_by_target_path[target.path] = extract_csharp_module_utils_imports(target.path, module_utils, False)

    for target in csharp_targets:
        imports_by_target_path[target.path] = extract_csharp_module_utils_imports(target.path, module_utils, True)

    imports = dict([(module_util, set()) for module_util in module_utils])

    for target_path in imports_by_target_path:
        for module_util in imports_by_target_path[target_path]:
            imports[module_util].add(target_path)

    for module_util in sorted(imports):
        if not imports[module_util]:
            display.warning('No imports found which use the "%s" module_util.' % module_util)

    return imports


def get_csharp_module_utils_name(path):  # type: (str) -> str
    """Return a namespace and name from the given module_utils path."""
    base_path = data_context().content.module_utils_csharp_path

    if data_context().content.collection:
        prefix = 'ansible_collections.' + data_context().content.collection.prefix + 'plugins.module_utils.'
    else:
        prefix = ''

    name = prefix + os.path.splitext(os.path.relpath(path, base_path))[0].replace(os.sep, '.')

    return name


def enumerate_module_utils():
    """Return a list of available module_utils imports.
    :rtype: set[str]
    """
    return set(get_csharp_module_utils_name(p)
               for p in data_context().content.walk_files(data_context().content.module_utils_csharp_path)
               if os.path.splitext(p)[1] == '.cs')


def extract_csharp_module_utils_imports(path, module_utils, is_pure_csharp):
    """Return a list of module_utils imports found in the specified source file.
    :type path: str
    :type module_utils: set[str]
    :type is_pure_csharp: bool
    :rtype: set[str]
    """
    imports = set()
    if is_pure_csharp:
        pattern = re.compile(r'(?i)^using\s((?:Ansible|AnsibleCollections)\..+);$')
    else:
        pattern = re.compile(r'(?i)^#\s*ansiblerequires\s+-csharputil\s+((?:Ansible|ansible.collections)\..+)')

    with open(path, 'r') as module_file:
        for line_number, line in enumerate(module_file, 1):
            match = re.search(pattern, line)

            if not match:
                continue

            import_name = match.group(1)
            if import_name not in module_utils:
                display.warning('%s:%d Invalid module_utils import: %s' % (path, line_number, import_name))
                continue

            imports.add(import_name)

    return imports
