"""A plugin for pylint to identify imports and functions which should not be used."""
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import astroid

from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker


class BlacklistEntry(object):
    """Defines a import blacklist entry."""
    def __init__(self, alternative, modules_only=False, names=None, ignore_paths=None):
        """
        :type alternative: str
        :type modules_only: bool
        :type names: tuple[str] | None
        :type ignore_paths: tuple[str] | None
        """
        self.alternative = alternative
        self.modules_only = modules_only
        self.names = set(names) if names else None
        self.ignore_paths = ignore_paths

    def applies_to(self, path, name=None):
        """
        :type path: str
        :type name: str | None
        :rtype: bool
        """
        if self.names:
            if not name:
                return False

            if name not in self.names:
                return False

        if self.ignore_paths and any(path.endswith(ignore_path) for ignore_path in self.ignore_paths):
            return False

        if self.modules_only:
            return is_module_path(path)

        return True


def is_module_path(path):
    """
    :type path: str
    :rtype: bool
    """
    return '/lib/ansible/modules/' in path or '/lib/ansible/module_utils/' in path


class AnsibleBlacklistChecker(BaseChecker):
    """Checker for blacklisted imports and functions."""
    __implements__ = (IAstroidChecker,)

    name = 'blacklist'

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

    blacklist_imports = dict(
        # Additional imports that we may want to start checking:
        # boto=BlacklistEntry('boto3', modules_only=True),
        # requests=BlacklistEntry('ansible.module_utils.urls', modules_only=True),
        # urllib=BlacklistEntry('ansible.module_utils.urls', modules_only=True),

        # see https://docs.python.org/2/library/urllib2.html
        urllib2=BlacklistEntry('ansible.module_utils.urls',
                               ignore_paths=(
                                   '/lib/ansible/module_utils/urls.py',
                               )),

        # see https://docs.python.org/3.7/library/collections.abc.html
        collections=BlacklistEntry('ansible.module_utils.common._collections_compat',
                                   ignore_paths=(
                                       '/lib/ansible/module_utils/common/_collections_compat.py',
                                   ),
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
                                   )),
    )

    blacklist_functions = {
        # see https://docs.python.org/2/library/tempfile.html#tempfile.mktemp
        'tempfile.mktemp': BlacklistEntry('tempfile.mkstemp'),

        'sys.exit': BlacklistEntry('exit_json or fail_json',
                                   ignore_paths=(
                                       '/lib/ansible/module_utils/basic.py',
                                       '/lib/ansible/modules/utilities/logic/async_wrapper.py',
                                       '/lib/ansible/module_utils/common/removed.py',
                                   ),
                                   modules_only=True),
    }

    def visit_import(self, node):
        """
        :type node: astroid.node_classes.Import
        """
        for name in node.names:
            self._check_import(node, name[0])

    def visit_importfrom(self, node):
        """
        :type node: astroid.node_classes.ImportFrom
        """
        self._check_importfrom(node, node.modname, node.names)

    def visit_attribute(self, node):
        """
        :type node: astroid.node_classes.Attribute
        """
        last_child = node.last_child()

        # this is faster than using type inference and will catch the most common cases
        if not isinstance(last_child, astroid.node_classes.Name):
            return

        module = last_child.name

        entry = self.blacklist_imports.get(module)

        if entry and entry.names:
            if entry.applies_to(self.linter.current_file, node.attrname):
                self.add_message(self.BAD_IMPORT_FROM, args=(node.attrname, entry.alternative, module), node=node)

    def visit_call(self, node):
        """
        :type node: astroid.node_classes.Call
        """
        try:
            for i in node.func.inferred():
                func = None

                if isinstance(i, astroid.scoped_nodes.FunctionDef) and isinstance(i.parent, astroid.scoped_nodes.Module):
                    func = '%s.%s' % (i.parent.name, i.name)

                if not func:
                    continue

                entry = self.blacklist_functions.get(func)

                if entry and entry.applies_to(self.linter.current_file):
                    self.add_message(self.BAD_FUNCTION, args=(entry.alternative, func), node=node)
        except astroid.exceptions.InferenceError:
            pass

    def _check_import(self, node, modname):
        """
        :type node: astroid.node_classes.Import
        :type modname: str
        """
        self._check_module_import(node, modname)

        entry = self.blacklist_imports.get(modname)

        if not entry:
            return

        if entry.applies_to(self.linter.current_file):
            self.add_message(self.BAD_IMPORT, args=(entry.alternative, modname), node=node)

    def _check_importfrom(self, node, modname, names):
        """
        :type node: astroid.node_classes.ImportFrom
        :type modname: str
        :type names:  list[str[
        """
        self._check_module_import(node, modname)

        entry = self.blacklist_imports.get(modname)

        if not entry:
            return

        for name in names:
            if entry.applies_to(self.linter.current_file, name[0]):
                self.add_message(self.BAD_IMPORT_FROM, args=(name[0], entry.alternative, modname), node=node)

    def _check_module_import(self, node, modname):
        """
        :type node: astroid.node_classes.Import | astroid.node_classes.ImportFrom
        :type modname: str
        """
        if not is_module_path(self.linter.current_file):
            return

        if modname == 'ansible.module_utils' or modname.startswith('ansible.module_utils.'):
            return

        if modname == 'ansible' or modname.startswith('ansible.'):
            self.add_message(self.BAD_MODULE_IMPORT, args=(modname,), node=node)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(AnsibleBlacklistChecker(linter))
