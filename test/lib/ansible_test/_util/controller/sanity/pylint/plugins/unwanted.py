"""A plugin for pylint to identify imports and functions which should not be used."""

from __future__ import annotations

import functools
import os
import typing as t

import astroid.exceptions
import astroid.nodes

from pylint.checkers import BaseChecker

ANSIBLE_TEST_MODULES_PATH = os.environ['ANSIBLE_TEST_MODULES_PATH']
ANSIBLE_TEST_MODULE_UTILS_PATH = os.environ['ANSIBLE_TEST_MODULE_UTILS_PATH']


class UnwantedEntry:
    """Defines an unwanted import."""
    def __init__(
            self,
            alternative,  # type: str
            modules_only=False,  # type: bool
            names=None,  # type: t.Optional[t.Tuple[str, ...]]
            ignore_paths=None,  # type: t.Optional[t.Tuple[str, ...]]
            ansible_test_only=False,  # type: bool
    ):  # type: (...) -> None
        self.alternative = alternative
        self.modules_only = modules_only
        self.names = set(names) if names else set()
        self.ignore_paths = ignore_paths
        self.ansible_test_only = ansible_test_only

    def applies_to(self, path, name=None):  # type: (str, t.Optional[str]) -> bool
        """Return True if this entry applies to the given path, otherwise return False."""
        if self.names:
            if not name:
                return False

            if name not in self.names:
                return False

        if self.ignore_paths and any(path.endswith(ignore_path) for ignore_path in self.ignore_paths):
            return False

        if self.ansible_test_only and '/test/lib/ansible_test/_internal/' not in path:
            return False

        if self.modules_only:
            return is_module_path(path)

        return True


def is_module_path(path):  # type: (str) -> bool
    """Return True if the given path is a module or module_utils path, otherwise return False."""
    return path.startswith(ANSIBLE_TEST_MODULES_PATH) or path.startswith(ANSIBLE_TEST_MODULE_UTILS_PATH)


class AnsibleUnwantedChecker(BaseChecker):
    """Checker for unwanted imports and functions."""

    name = 'unwanted'

    BAD_IMPORT = 'ansible-bad-import'
    BAD_IMPORT_FROM = 'ansible-bad-import-from'
    BAD_FUNCTION = 'ansible-bad-function'
    BAD_MODULE_IMPORT = 'ansible-bad-module-import'

    msgs = dict(
        E5101=('Import %s instead of %s',
               BAD_IMPORT,
               'Identifies imports which should not be used.'),
        E5102=('Import %s from %s instead of %s',
               BAD_IMPORT_FROM,
               'Identifies imports which should not be used.'),
        E5103=('Call %s instead of %s',
               BAD_FUNCTION,
               'Identifies functions which should not be used.'),
        E5104=('Import external package or ansible.module_utils not %s',
               BAD_MODULE_IMPORT,
               'Identifies imports which should not be used.'),
    )

    unwanted_imports = {
        # see https://docs.python.org/2/library/urllib2.html
        'urllib2': UnwantedEntry(
            'ansible.module_utils.urls',
            ignore_paths=(
                '/lib/ansible/module_utils/urls.py',
            )
        ),

        # see https://docs.python.org/3/library/collections.abc.html
        'collections': UnwantedEntry(
            'collections.abc',
            names=(
                'MappingView',
                'ItemsView',
                'KeysView',
                'ValuesView',
                'Mapping', 'MutableMapping',
                'Sequence', 'MutableSequence',
                'Set', 'MutableSet',
                'Container',
                'Hashable',
                'Sized',
                'Callable',
                'Iterable',
                'Iterator',
            )
        ),
    }

    unwanted_functions = {
        # see https://docs.python.org/3/library/tempfile.html#tempfile.mktemp
        'tempfile.mktemp': UnwantedEntry('tempfile.mkstemp'),

        # os.chmod resolves as posix.chmod
        'posix.chmod': UnwantedEntry('verified_chmod',
                                     ansible_test_only=True),

        'sys.exit': UnwantedEntry('exit_json or fail_json',
                                  ignore_paths=(
                                      '/lib/ansible/module_utils/basic.py',
                                      '/lib/ansible/modules/async_wrapper.py',
                                  ),
                                  modules_only=True),

        'builtins.print': UnwantedEntry('module.log or module.debug',
                                        ignore_paths=(
                                            '/lib/ansible/module_utils/basic.py',
                                        ),
                                        modules_only=True),
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # ansible.module_utils.six is deprecated and collections can still use it until it is removed
        if self.is_ansible_core:
            self.unwanted_imports['ansible.module_utils.six'] = UnwantedEntry(
                'the Python standard library equivalent'
            )

    @functools.cached_property
    def is_ansible_core(self) -> bool:
        """True if ansible-core is being tested."""
        return not self.linter.config.collection_name

    def visit_import(self, node: astroid.nodes.Import) -> None:
        """Visit an import node."""
        for name in node.names:
            self._check_import(node, name[0])

    def visit_importfrom(self, node: astroid.nodes.ImportFrom) -> None:
        """Visit an import from node."""
        self._check_importfrom(node, node.modname, node.names)

    def visit_attribute(self, node: astroid.nodes.Attribute) -> None:
        """Visit an attribute node."""
        last_child = node.last_child()

        # this is faster than using type inference and will catch the most common cases
        if not isinstance(last_child, astroid.nodes.Name):
            return

        module = last_child.name

        entry = self.unwanted_imports.get(module)

        if entry and entry.names:
            if entry.applies_to(self.linter.current_file, node.attrname):
                self.add_message(self.BAD_IMPORT_FROM, args=(node.attrname, entry.alternative, module), node=node)

    def visit_call(self, node: astroid.nodes.Call) -> None:
        """Visit a call node."""
        try:
            for i in node.func.inferred():
                func = None

                if isinstance(i, astroid.nodes.FunctionDef) and isinstance(i.parent, astroid.nodes.Module):
                    func = '%s.%s' % (i.parent.name, i.name)

                if not func:
                    continue

                entry = self.unwanted_functions.get(func)

                if entry and entry.applies_to(self.linter.current_file):
                    self.add_message(self.BAD_FUNCTION, args=(entry.alternative, func), node=node)
        except astroid.exceptions.InferenceError:
            pass

    def _check_import(self, node: astroid.nodes.Import, modname: str) -> None:
        """Check the imports on the specified import node."""
        self._check_module_import(node, modname)

        entry = self.unwanted_imports.get(modname)

        if not entry:
            return

        if entry.applies_to(self.linter.current_file):
            self.add_message(self.BAD_IMPORT, args=(entry.alternative, modname), node=node)

    def _check_importfrom(self, node: astroid.nodes.ImportFrom, modname: str, names: list[tuple[str, str | None]]) -> None:
        """Check the imports on the specified import from node."""
        self._check_module_import(node, modname)

        entry = self.unwanted_imports.get(modname)

        if not entry:
            return

        for name in names:
            if entry.applies_to(self.linter.current_file, name[0]):
                self.add_message(self.BAD_IMPORT_FROM, args=(name[0], entry.alternative, modname), node=node)

    def _check_module_import(self, node: astroid.nodes.Import | astroid.nodes.ImportFrom, modname: str) -> None:
        """Check the module import on the given import or import from node."""
        if not is_module_path(self.linter.current_file):
            return

        if modname == 'ansible.module_utils' or modname.startswith('ansible.module_utils.'):
            return

        if modname == 'ansible' or modname.startswith('ansible.'):
            self.add_message(self.BAD_MODULE_IMPORT, args=(modname,), node=node)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(AnsibleUnwantedChecker(linter))
