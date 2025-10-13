"""Ansible-specific pylint plugin for checking deprecation calls."""

# (c) 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import dataclasses
import datetime
import functools
import pathlib
import re

import astroid.bases
import astroid.exceptions
import astroid.nodes
import astroid.typing
import astroid.util

import pylint.lint
import pylint.checkers
import pylint.checkers.utils

import ansible.release

from ansible.module_utils._internal._deprecator import INDETERMINATE_DEPRECATOR, _path_as_collection_plugininfo
from ansible.module_utils.compat.version import StrictVersion
from ansible.utils.version import SemanticVersion


@dataclasses.dataclass(frozen=True, kw_only=True)
class DeprecationCallArgs:
    """Arguments passed to a deprecation function."""

    msg: object = None
    version: object = None
    date: object = None
    collection_name: object = None
    deprecator: object = None
    help_text: object = None  # only on Display.deprecated, warnings.deprecate and deprecate_value
    obj: object = None  # only on Display.deprecated and warnings.deprecate
    removed: object = None  # only on Display.deprecated
    value: object = None  # only on deprecate_value

    def all_args_dynamic(self) -> bool:
        """True if all args are dynamic or None, otherwise False."""
        return all(arg is None or isinstance(arg, astroid.nodes.NodeNG) for arg in dataclasses.asdict(self).values())


class AnsibleDeprecatedChecker(pylint.checkers.BaseChecker):
    """Checks for deprecated calls to ensure proper usage."""

    name = 'deprecated-calls'
    msgs = {
        'E9501': (
            "Deprecated version %r found in call to %r",
            "ansible-deprecated-version",
            None,
        ),
        'E9502': (
            "Found %r call without a version or date",
            "ansible-deprecated-no-version",
            None,
        ),
        'E9503': (
            "Invalid deprecated version %r found in call to %r",
            "ansible-invalid-deprecated-version",
            None,
        ),
        'E9504': (
            "Deprecated version %r found in call to %r",
            "collection-deprecated-version",
            None,
        ),
        'E9505': (
            "Invalid deprecated version %r found in call to %r",
            "collection-invalid-deprecated-version",
            None,
        ),
        'E9506': (
            "No collection_name or deprecator found in call to %r",
            "ansible-deprecated-no-collection-name",
            None,
        ),
        'E9507': (
            "Wrong collection_name %r found in call to %r",
            "wrong-collection-deprecated",
            None,
        ),
        'E9508': (
            "Expired date %r found in call to %r",
            "ansible-expired-deprecated-date",
            None,
        ),
        'E9509': (
            "Invalid date %r found in call to %r",
            "ansible-invalid-deprecated-date",
            None,
        ),
        'E9510': (
            "Both version and date found in call to %r",
            "ansible-deprecated-both-version-and-date",
            None,
        ),
        'E9511': (
            "Removal version %r must be a major release, not a minor or patch release, see https://semver.org/",
            "removal-version-must-be-major",
            None,
        ),
        'E9512': (
            "Passing date is not permitted in call to %r for ansible-core, use a version instead",
            "ansible-deprecated-date-not-permitted",
            None,
        ),
        'E9513': (
            "Unnecessary %r found in call to %r",
            "ansible-deprecated-unnecessary-collection-name",
            None,
        ),
        'E9514': (
            "Passing collection_name not permitted in call to %r for ansible-core, use deprecator instead",
            "ansible-deprecated-collection-name-not-permitted",
            None,
        ),
        'E9515': (
            "Both collection_name and deprecator found in call to %r",
            "ansible-deprecated-both-collection-name-and-deprecator",
            None,
        ),
    }

    options = (
        (
            'collection-name',
            dict(
                default=None,
                type='string',
                metavar='<name>',
                help="The name of the collection to check.",
            ),
        ),
        (
            'collection-version',
            dict(
                default=None,
                type='string',
                metavar='<version>',
                help="The version of the collection to check.",
            ),
        ),
        (
            'collection-path',
            dict(
                default=None,
                type='string',
                metavar='<path>',
                help="The path of the collection to check.",
            ),
        ),
    )

    ANSIBLE_VERSION = StrictVersion(re.match('[0-9.]*[0-9]', ansible.release.__version__)[0])
    """The current ansible-core X.Y.Z version."""

    DEPRECATION_MODULE_FUNCTIONS: dict[tuple[str, str], tuple[str, ...]] = {
        ('ansible.module_utils.common.warnings', 'deprecate'): ('msg', 'version', 'date', 'collection_name'),
        ('ansible.module_utils.datatag', 'deprecate_value'): ('value', 'msg'),
        ('ansible.module_utils.basic', 'AnsibleModule.deprecate'): ('msg', 'version', 'date', 'collection_name'),
        ('ansible.utils.display', 'Display.deprecated'): ('msg', 'version', 'removed', 'date', 'collection_name'),
    }
    """Mapping of deprecation module+function and their positional arguments."""

    DEPRECATION_MODULES = frozenset(key[0] for key in DEPRECATION_MODULE_FUNCTIONS)
    """Modules which contain deprecation functions."""

    DEPRECATION_FUNCTIONS = {'.'.join(key): value for key, value in DEPRECATION_MODULE_FUNCTIONS.items()}
    """Mapping of deprecation functions and their positional arguments."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.module_cache: dict[str, astroid.nodes.Module] = {}

    @functools.cached_property
    def collection_name(self) -> str | None:
        """Return the collection name, or None if ansible-core is being tested."""
        return self.linter.config.collection_name or None

    @functools.cached_property
    def collection_path(self) -> pathlib.Path:
        """Return the collection path. Not valid when ansible-core is being tested."""
        return pathlib.Path(self.linter.config.collection_path)

    @functools.cached_property
    def collection_version(self) -> SemanticVersion | None:
        """Return the collection version, or None if ansible-core is being tested."""
        if not self.linter.config.collection_version:
            return None

        sem_ver = SemanticVersion(self.linter.config.collection_version)
        sem_ver.prerelease = ()  # ignore pre-release for version comparison to catch issues before the final release is cut

        return sem_ver

    @functools.cached_property
    def is_ansible_core(self) -> bool:
        """True if ansible-core is being tested."""
        return not self.collection_name

    @functools.cached_property
    def today_utc(self) -> datetime.date:
        """Today's date in UTC."""
        return datetime.datetime.now(tz=datetime.timezone.utc).date()

    def is_deprecator_required(self) -> bool | None:
        """Determine is a `collection_name` or `deprecator` is required (True), unnecessary (False) or optional (None)."""
        if self.is_ansible_core:
            return False  # in ansible-core, never provide the deprecator -- if it really is needed, disable the sanity test inline for that line of code

        plugin_info = _path_as_collection_plugininfo(self.linter.current_file)

        if plugin_info is INDETERMINATE_DEPRECATOR:
            return True  # deprecator cannot be detected, caller must provide deprecator

        # deprecation: description='deprecate collection_name/deprecator now that detection is widely available' core_version='2.23'
        # When this deprecation triggers, change the return type here to False.
        # At that point, callers should be able to omit the collection_name/deprecator in all but a few cases (inline ignores can be used for those cases)
        return None

    @pylint.checkers.utils.only_required_for_messages(*(msgs.keys()))
    def visit_call(self, node: astroid.nodes.Call) -> None:
        """Visit a call node."""
        if inferred := self.infer(node.func):
            name = self.get_fully_qualified_name(inferred)

            if args := self.DEPRECATION_FUNCTIONS.get(name):
                self.check_call(node, name, args)

    def infer(self, node: astroid.nodes.NodeNG) -> astroid.nodes.NodeNG | None:
        """Return the inferred node from the given node, or `None` if it cannot be unambiguously inferred."""
        names: list[str] = []
        target: astroid.nodes.NodeNG | None = node
        inferred: astroid.typing.InferenceResult | None = None

        while target:
            if inferred := astroid.util.safe_infer(target):
                break

            if isinstance(target, astroid.nodes.Call):
                inferred = self.infer(target.func)
                break

            if isinstance(target, astroid.nodes.FunctionDef):
                inferred = target
                break

            if isinstance(target, astroid.nodes.Name):
                target = self.infer_name(target)
            elif isinstance(target, astroid.nodes.AssignName) and isinstance(target.parent, astroid.nodes.Assign):
                target = target.parent.value
            elif isinstance(target, astroid.nodes.Attribute):
                names.append(target.attrname)
                target = target.expr
            else:
                break

        for name in reversed(names):
            if isinstance(inferred, astroid.bases.Instance):
                try:
                    attr = next(iter(inferred.getattr(name)), None)
                except astroid.exceptions.AttributeInferenceError:
                    break

                if isinstance(attr, astroid.nodes.AssignAttr):
                    inferred = self.get_ansible_module(attr)
                    continue

                if isinstance(attr, astroid.nodes.FunctionDef):
                    inferred = attr
                    continue

            if not isinstance(inferred, (astroid.nodes.Module, astroid.nodes.ClassDef)):
                inferred = None
                break

            try:
                inferred = inferred[name]
            except KeyError:
                inferred = None
            else:
                inferred = self.infer(inferred)

        if isinstance(inferred, astroid.nodes.FunctionDef) and isinstance(inferred.parent, astroid.nodes.ClassDef):
            inferred = astroid.bases.BoundMethod(inferred, inferred.parent)

        return inferred

    def infer_name(self, node: astroid.nodes.Name) -> astroid.nodes.NodeNG | None:
        """Infer the node referenced by the given name, or `None` if it cannot be unambiguously inferred."""
        scope = node.scope()
        inferred: astroid.nodes.NodeNG | None = None
        name = node.name

        while scope:
            try:
                assignment = scope[name]
            except KeyError:
                scope = scope.parent.scope() if scope.parent else None
                continue

            if isinstance(assignment, astroid.nodes.AssignName) and isinstance(assignment.parent, astroid.nodes.Assign):
                inferred = assignment.parent.value
            elif (
                isinstance(scope, astroid.nodes.FunctionDef)
                and isinstance(assignment, astroid.nodes.AssignName)
                and isinstance(assignment.parent, astroid.nodes.Arguments)
                and assignment.parent.annotations
            ):
                idx, _node = assignment.parent.find_argname(name)

                if idx is not None:
                    try:
                        annotation = assignment.parent.annotations[idx]
                    except IndexError:
                        pass
                    else:
                        if isinstance(annotation, astroid.nodes.Name):
                            name = annotation.name
                            continue
            elif isinstance(assignment, astroid.nodes.ClassDef):
                inferred = assignment
            elif isinstance(assignment, astroid.nodes.ImportFrom):
                if module := self.get_module(assignment):
                    name = assignment.real_name(name)
                    scope = module.scope()
                    continue

            break

        return inferred

    def get_module(self, node: astroid.nodes.ImportFrom) -> astroid.nodes.Module | None:
        """Import the requested module if possible and cache the result."""
        module_name = pylint.checkers.utils.get_import_name(node, node.modname)

        if module_name not in self.DEPRECATION_MODULES:
            return None  # avoid unnecessary import overhead

        if module := self.module_cache.get(module_name):
            return module

        module = node.do_import_module()

        if module.name != module_name:
            raise RuntimeError(f'Attempted to import {module_name!r} but found {module.name!r} instead.')

        self.module_cache[module_name] = module

        return module

    @staticmethod
    def get_fully_qualified_name(node: astroid.nodes.NodeNG) -> str | None:
        """Return the fully qualified name of the given inferred node."""
        parent = node.parent
        parts: tuple[str, ...] | None

        if isinstance(node, astroid.nodes.FunctionDef) and isinstance(parent, astroid.nodes.Module):
            parts = (parent.name, node.name)
        elif isinstance(node, astroid.bases.BoundMethod) and isinstance(parent, astroid.nodes.ClassDef) and isinstance(parent.parent, astroid.nodes.Module):
            parts = (parent.parent.name, parent.name, node.name)
        else:
            parts = None

        return '.'.join(parts) if parts else None

    def check_call(self, node: astroid.nodes.Call, name: str, args: tuple[str, ...]) -> None:
        """Check the given deprecation call node for valid arguments."""
        call_args = self.get_deprecation_call_args(node, args)

        self.check_collection_name(node, name, call_args)

        if not call_args.version and not call_args.date:
            self.add_message('ansible-deprecated-no-version', node=node, args=(name,))
            return

        if call_args.date and self.is_ansible_core:
            self.add_message('ansible-deprecated-date-not-permitted', node=node, args=(name,))
            return

        if call_args.all_args_dynamic():
            # assume collection maintainers know what they're doing if all args are dynamic
            return

        if call_args.version and call_args.date:
            self.add_message('ansible-deprecated-both-version-and-date', node=node, args=(name,))
            return

        if call_args.date:
            self.check_date(node, name, call_args)

        if call_args.version:
            self.check_version(node, name, call_args)

    @staticmethod
    def get_deprecation_call_args(node: astroid.nodes.Call, args: tuple[str, ...]) -> DeprecationCallArgs:
        """Get the deprecation call arguments from the given node."""
        fields: dict[str, object] = {}

        for idx, arg in enumerate(node.args):
            field = args[idx]
            fields[field] = arg

        for keyword in node.keywords:
            if keyword.arg is not None:
                fields[keyword.arg] = keyword.value

        for key, value in fields.items():
            if isinstance(value, astroid.nodes.Const):
                fields[key] = value.value

        return DeprecationCallArgs(**fields)

    def check_collection_name(self, node: astroid.nodes.Call, name: str, args: DeprecationCallArgs) -> None:
        """Check the collection name provided to the given call node."""
        deprecator_requirement = self.is_deprecator_required()

        if self.is_ansible_core and args.collection_name:
            self.add_message('ansible-deprecated-collection-name-not-permitted', node=node, args=(name,))
            return

        if args.collection_name and args.deprecator:
            self.add_message('ansible-deprecated-both-collection-name-and-deprecator', node=node, args=(name,))

        if deprecator_requirement is True:
            if not args.collection_name and not args.deprecator:
                self.add_message('ansible-deprecated-no-collection-name', node=node, args=(name,))
                return
        elif deprecator_requirement is False:
            if args.collection_name:
                self.add_message('ansible-deprecated-unnecessary-collection-name', node=node, args=('collection_name', name,))
                return

            if args.deprecator:
                self.add_message('ansible-deprecated-unnecessary-collection-name', node=node, args=('deprecator', name,))
                return
        else:
            # collection_name may be needed for backward compat with 2.18 and earlier, since it is only detected in 2.19 and later

            if args.deprecator:
                # Unlike collection_name, which is needed for backward compat, deprecator is generally not needed by collections.
                # For the very rare cases where this is needed by collections, an inline pylint ignore can be used to silence it.
                self.add_message('ansible-deprecated-unnecessary-collection-name', node=node, args=('deprecator', name,))
                return

        if args.all_args_dynamic():
            # assume collection maintainers know what they're doing if all args are dynamic
            return

        expected_collection_name = 'ansible.builtin' if self.is_ansible_core else self.collection_name

        if args.collection_name and args.collection_name != expected_collection_name:
            self.add_message('wrong-collection-deprecated', node=node, args=(args.collection_name, name))

    def check_version(self, node: astroid.nodes.Call, name: str, args: DeprecationCallArgs) -> None:
        """Check the version provided to the given call node."""
        if self.collection_name:
            self.check_collection_version(node, name, args)
        else:
            self.check_core_version(node, name, args)

    def check_core_version(self, node: astroid.nodes.Call, name: str, args: DeprecationCallArgs) -> None:
        """Check the core version provided to the given call node."""
        try:
            if not isinstance(args.version, str) or not args.version:
                raise ValueError()

            strict_version = StrictVersion(args.version)
        except ValueError:
            self.add_message('ansible-invalid-deprecated-version', node=node, args=(args.version, name))
            return

        if self.ANSIBLE_VERSION >= strict_version:
            self.add_message('ansible-deprecated-version', node=node, args=(args.version, name))

    def check_collection_version(self, node: astroid.nodes.Call, name: str, args: DeprecationCallArgs) -> None:
        """Check the collection version provided to the given call node."""
        try:
            if not isinstance(args.version, str) or not args.version:
                raise ValueError()

            semantic_version = SemanticVersion(args.version)
        except ValueError:
            self.add_message('collection-invalid-deprecated-version', node=node, args=(args.version, name))
            return

        if self.collection_version >= semantic_version:
            self.add_message('collection-deprecated-version', node=node, args=(args.version, name))

        if semantic_version.major != 0 and (semantic_version.minor != 0 or semantic_version.patch != 0):
            self.add_message('removal-version-must-be-major', node=node, args=(args.version,))

    def check_date(self, node: astroid.nodes.Call, name: str, args: DeprecationCallArgs) -> None:
        """Check the date provided to the given call node."""
        try:
            date_parsed = self.parse_isodate(args.date)
        except (ValueError, TypeError):
            self.add_message('ansible-invalid-deprecated-date', node=node, args=(args.date, name))
        else:
            if date_parsed < self.today_utc:
                self.add_message('ansible-expired-deprecated-date', node=node, args=(args.date, name))

    @staticmethod
    def parse_isodate(value: object) -> datetime.date:
        """Parse an ISO 8601 date string."""
        if isinstance(value, str):
            return datetime.date.fromisoformat(value)

        raise TypeError(type(value))

    def get_ansible_module(self, node: astroid.nodes.AssignAttr) -> astroid.bases.Instance | None:
        """Infer an AnsibleModule instance node from the given assignment."""
        if isinstance(node.parent, astroid.nodes.Assign) and isinstance(node.parent.type_annotation, astroid.nodes.Name):
            inferred = self.infer_name(node.parent.type_annotation)
        elif (isinstance(node.parent, astroid.nodes.Assign) and isinstance(node.parent.parent, astroid.nodes.FunctionDef) and
              isinstance(node.parent.value, astroid.nodes.Name)):
            inferred = self.infer_name(node.parent.value)
        elif isinstance(node.parent, astroid.nodes.AnnAssign) and isinstance(node.parent.annotation, astroid.nodes.Name):
            inferred = self.infer_name(node.parent.annotation)
        else:
            inferred = None

        if isinstance(inferred, astroid.nodes.ClassDef) and inferred.name == 'AnsibleModule':
            return inferred.instantiate_class()

        return None

    def register(self) -> None:
        """Register this plugin."""
        self.linter.register_checker(self)


def register(linter: pylint.lint.PyLinter) -> None:
    """Required method to auto-register this checker."""
    AnsibleDeprecatedChecker(linter).register()
