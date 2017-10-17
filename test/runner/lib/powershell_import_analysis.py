"""Analyze powershell import statements."""

from __future__ import absolute_import, print_function

import os
import re

from lib.util import (
    display,
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


def enumerate_module_utils():
    """Return a list of available module_utils imports.
    :rtype: set[str]
    """
    return set(os.path.splitext(p)[0] for p in os.listdir('lib/ansible/module_utils/powershell') if os.path.splitext(p)[1] == '.psm1')


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
            match = re.search(r'(?i)^#\s*requires\s+-module(?:s?)\s*(Ansible\.ModuleUtils\..+)', line)

            if not match:
                continue

            import_name = match.group(1)

            if import_name in module_utils:
                imports.add(import_name)
            else:
                display.warning('%s:%d Invalid module_utils import: %s' % (path, line_number, import_name))

    return imports
