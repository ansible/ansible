"""Analyze python import statements."""

from __future__ import absolute_import, print_function

import ast
import os
import uuid

from lib.util import (
    display,
    ApplicationError,
)


def get_python_module_utils_imports(compile_targets):
    """Return a dictionary of python file paths mapped to sets of module_utils names.
    :type compile_targets: list[TestTarget]
    :rtype: dict[str, set[str]]
    """
    module_utils_files = (os.path.splitext(filename) for filename in os.listdir('lib/ansible/module_utils'))
    module_utils = sorted(name[0] for name in module_utils_files if name[0] != '__init__' and name[1] == '.py')

    imports_by_target_path = {}

    for target in compile_targets:
        imports_by_target_path[target.path] = extract_python_module_utils_imports(target.path, module_utils)

    def recurse_import(import_name, depth=0, seen=None):
        """Recursively expand module_utils imports from module_utils files.
        :type import_name: str
        :type depth: int
        :type seen: set[str] | None
        :rtype set[str]
        """
        display.info('module_utils import: %s%s' % ('  ' * depth, import_name), verbosity=4)

        if seen is None:
            seen = set([import_name])

        results = set([import_name])

        import_path = os.path.join('lib/ansible/module_utils', '%s.py' % import_name)

        for name in sorted(imports_by_target_path.get(import_path, set())):
            if name in seen:
                continue

            seen.add(name)

            matches = sorted(recurse_import(name, depth + 1, seen))

            for result in matches:
                results.add(result)

        return results

    for module_util in module_utils:
        # recurse over module_utils imports while excluding self
        module_util_imports = recurse_import(module_util)
        module_util_imports.remove(module_util)

        # add recursive imports to all path entries which import this module_util
        for target_path in imports_by_target_path:
            if module_util in imports_by_target_path[target_path]:
                for module_util_import in sorted(module_util_imports):
                    if module_util_import not in imports_by_target_path[target_path]:
                        display.info('%s inherits import %s via %s' % (target_path, module_util_import, module_util), verbosity=6)
                        imports_by_target_path[target_path].add(module_util_import)

    imports = dict([(module_util, set()) for module_util in module_utils])

    for target_path in imports_by_target_path:
        for module_util in imports_by_target_path[target_path]:
            imports[module_util].add(target_path)

    for module_util in sorted(imports):
        if not len(imports[module_util]):
            display.warning('No imports found which use the "%s" module_util.' % module_util)

    return imports


def extract_python_module_utils_imports(path, module_utils):
    """Return a list of module_utils imports found in the specified source file.
    :type path: str
    :type module_utils: set[str]
    :rtype: set[str]
    """
    with open(path, 'r') as module_fd:
        code = module_fd.read()

        try:
            tree = ast.parse(code)
        except SyntaxError as ex:
            # Setting the full path to the filename results in only the filename being given for str(ex).
            # As a work-around, set the filename to a UUID and replace it in the final string output with the actual path.
            ex.filename = str(uuid.uuid4())
            error = str(ex).replace(ex.filename, path)
            raise ApplicationError('AST parse error: %s' % error)

        finder = ModuleUtilFinder(path, module_utils)
        finder.visit(tree)
        return finder.imports


class ModuleUtilFinder(ast.NodeVisitor):
    """AST visitor to find valid module_utils imports."""
    def __init__(self, path, module_utils):
        """Return a list of module_utils imports found in the specified source file.
        :type path: str
        :type module_utils: set[str]
        """
        super(ModuleUtilFinder, self).__init__()

        self.path = path
        self.module_utils = module_utils
        self.imports = set()

    # noinspection PyPep8Naming
    # pylint: disable=locally-disabled, invalid-name
    def visit_Import(self, node):
        """
        :type node: ast.Import
        """
        self.generic_visit(node)

        for alias in node.names:
            if alias.name.startswith('ansible.module_utils.'):
                # import ansible.module_utils.MODULE[.MODULE]
                self.add_import(alias.name.split('.')[2], node.lineno)

    # noinspection PyPep8Naming
    # pylint: disable=locally-disabled, invalid-name
    def visit_ImportFrom(self, node):
        """
        :type node: ast.ImportFrom
        """
        self.generic_visit(node)

        if not node.module:
            return

        if node.module == 'ansible.module_utils':
            for alias in node.names:
                # from ansible.module_utils import MODULE[, MODULE]
                self.add_import(alias.name, node.lineno)
        elif node.module.startswith('ansible.module_utils.'):
            # from ansible.module_utils.MODULE[.MODULE]
            self.add_import(node.module.split('.')[2], node.lineno)

    def add_import(self, name, line_number):
        """
        :type name: str
        :type line_number: int
        """
        if name in self.imports:
            return  # duplicate imports are ignored

        if name not in self.module_utils:
            if self.path.startswith('test/'):
                return  # invalid imports in tests are ignored

            raise Exception('%s:%d Invalid module_util import: %s' % (self.path, line_number, name))

        display.info('%s:%d imports module_utils: %s' % (self.path, line_number, name), verbosity=5)

        self.imports.add(name)
