"""Analyze python import statements."""

from __future__ import absolute_import, print_function

import ast
import os

from lib.util import (
    display,
    ApplicationError,
)

VIRTUAL_PACKAGES = set([
    'ansible.module_utils.six',
])


def get_python_module_utils_imports(compile_targets):
    """Return a dictionary of module_utils names mapped to sets of python file paths.
    :type compile_targets: list[TestTarget]
    :rtype: dict[str, set[str]]
    """

    module_utils = enumerate_module_utils()
    virtual_utils = set(m for m in module_utils if any(m.startswith('%s.' % v) for v in VIRTUAL_PACKAGES))
    module_utils -= virtual_utils

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

        # virtual packages depend on the modules they contain instead of the reverse
        if import_name in VIRTUAL_PACKAGES:
            for sub_import in sorted(virtual_utils):
                if sub_import.startswith('%s.' % import_name):
                    if sub_import in seen:
                        continue

                    seen.add(sub_import)

                    matches = sorted(recurse_import(sub_import, depth + 1, seen))

                    for result in matches:
                        results.add(result)

        import_path = os.path.join('lib/', '%s.py' % import_name.replace('.', '/'))

        if import_path not in imports_by_target_path:
            import_path = os.path.join('lib/', import_name.replace('.', '/'), '__init__.py')

            if import_path not in imports_by_target_path:
                raise ApplicationError('Cannot determine path for module_utils import: %s' % import_name)

        # process imports in reverse so the deepest imports come first
        for name in sorted(imports_by_target_path[import_path], reverse=True):
            if name in virtual_utils:
                continue

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

    imports = dict([(module_util, set()) for module_util in module_utils | virtual_utils])

    for target_path in imports_by_target_path:
        for module_util in imports_by_target_path[target_path]:
            imports[module_util].add(target_path)

    # for purposes of mapping module_utils to paths, treat imports of virtual utils the same as the parent package
    for virtual_util in virtual_utils:
        parent_package = '.'.join(virtual_util.split('.')[:-1])
        imports[virtual_util] = imports[parent_package]
        display.info('%s reports imports from parent package %s' % (virtual_util, parent_package), verbosity=6)

    for module_util in sorted(imports):
        if not imports[module_util]:
            display.warning('No imports found which use the "%s" module_util.' % module_util)

    return imports


def enumerate_module_utils():
    """Return a list of available module_utils imports.
    :rtype: set[str]
    """
    module_utils = []
    base_path = 'lib/ansible/module_utils'

    for root, _, file_names in os.walk(base_path):
        for file_name in file_names:
            path = os.path.join(root, file_name)
            name, ext = os.path.splitext(file_name)

            if path == 'lib/ansible/module_utils/__init__.py':
                continue

            if ext != '.py':
                continue

            if name == '__init__':
                module_util = root
            else:
                module_util = os.path.join(root, name)

            module_utils.append(module_util[4:].replace('/', '.'))

    return set(module_utils)


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
            # Treat this error as a warning so tests can be executed as best as possible.
            # The compile test will detect and report this syntax error.
            display.warning('%s:%s Syntax error extracting module_utils imports: %s' % (path, ex.lineno, ex.msg))
            return set()

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
        self.path = path
        self.module_utils = module_utils
        self.imports = set()

        # implicitly import parent package

        if path.endswith('/__init__.py'):
            path = os.path.split(path)[0]

        if path.startswith('lib/ansible/module_utils/'):
            package = os.path.split(path)[0].replace('/', '.')[4:]

            if package != 'ansible.module_utils' and package not in VIRTUAL_PACKAGES:
                self.add_import(package, 0)

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
                self.add_import(alias.name, node.lineno)

    # noinspection PyPep8Naming
    # pylint: disable=locally-disabled, invalid-name
    def visit_ImportFrom(self, node):
        """
        :type node: ast.ImportFrom
        """
        self.generic_visit(node)

        if not node.module:
            return

        if node.module == 'ansible.module_utils' or node.module.startswith('ansible.module_utils.'):
            for alias in node.names:
                # from ansible.module_utils import MODULE[, MODULE]
                # from ansible.module_utils.MODULE[.MODULE] import MODULE[, MODULE]
                self.add_import('%s.%s' % (node.module, alias.name), node.lineno)

    def add_import(self, name, line_number):
        """
        :type name: str
        :type line_number: int
        """
        import_name = name

        while len(name) > len('ansible.module_utils.'):
            if name in self.module_utils:
                if name not in self.imports:
                    display.info('%s:%d imports module_utils: %s' % (self.path, line_number, name), verbosity=5)
                    self.imports.add(name)

                return  # duplicate imports are ignored

            name = '.'.join(name.split('.')[:-1])

        if self.path.startswith('test/'):
            return  # invalid imports in tests are ignored

        # Treat this error as a warning so tests can be executed as best as possible.
        # This error should be detected by unit or integration tests.
        display.warning('%s:%d Invalid module_utils import: %s' % (self.path, line_number, import_name))
