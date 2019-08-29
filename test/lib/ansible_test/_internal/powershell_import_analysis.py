"""Analyze powershell import statements."""
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


def get_powershell_module_utils_imports(powershell_targets):
    """Return a dictionary of module_utils names mapped to sets of powershell file paths.
    :type powershell_targets: list[TestTarget]
    :rtype: dict[str, set[str]]
    """

    module_utils = enumerate_module_utils()

    imports_by_target_path = {}

    for target in powershell_targets:
        imports_by_target_path[target.path] = extract_powershell_module_utils_imports(target.path, module_utils)

    imports = dict([(module_util, set()) for module_util in module_utils])

    for target_path in imports_by_target_path:
        for module_util in imports_by_target_path[target_path]:
            imports[module_util].add(target_path)

    for module_util in sorted(imports):
        if not imports[module_util]:
            display.warning('No imports found which use the "%s" module_util.' % module_util)

    return imports


def get_powershell_module_utils_name(path):  # type: (str) -> str
    """Return a namespace and name from the given module_utils path."""
    base_path = data_context().content.module_utils_powershell_path

    if data_context().content.collection:
        prefix = 'ansible_collections.' + data_context().content.collection.prefix + '.plugins.module_utils.'
    else:
        prefix = ''

    name = prefix + os.path.splitext(os.path.relpath(path, base_path))[0].replace(os.sep, '.')

    return name


def enumerate_module_utils():
    """Return a list of available module_utils imports.
    :rtype: set[str]
    """
    return set(get_powershell_module_utils_name(p)
               for p in data_context().content.walk_files(data_context().content.module_utils_powershell_path)
               if os.path.splitext(p)[1] == '.psm1')


def extract_powershell_module_utils_imports(path, module_utils):
    """Return a list of module_utils imports found in the specified source file.
    :type path: str
    :type module_utils: set[str]
    :rtype: set[str]
    """
    imports = set()

    with open(path, 'r') as module_fd:
        code = module_fd.read()

        if '# POWERSHELL_COMMON' in code:
            imports.add('Ansible.ModuleUtils.Legacy')

        lines = code.splitlines()
        line_number = 0

        for line in lines:
            line_number += 1
            match = re.search(r'(?i)^#\s*(?:requires\s+-module(?:s?)|ansiblerequires\s+-powershell)\s*((?:Ansible|ansible_collections)\..+)', line)

            if not match:
                continue

            import_name = match.group(1)

            if import_name in module_utils:
                imports.add(import_name)
            else:
                display.warning('%s:%d Invalid module_utils import: %s' % (path, line_number, import_name))

    return imports
