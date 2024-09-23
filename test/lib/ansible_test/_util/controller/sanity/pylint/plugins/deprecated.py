"""Ansible specific plyint plugin for checking deprecations."""
# (c) 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
import re
import shlex
import typing as t
from tokenize import COMMENT, TokenInfo

import astroid

# support pylint 2.x and 3.x -- remove when supporting only 3.x
try:
    from pylint.interfaces import IAstroidChecker, ITokenChecker
except ImportError:
    class IAstroidChecker:
        """Backwards compatibility for 2.x / 3.x support."""

    class ITokenChecker:
        """Backwards compatibility for 2.x / 3.x support."""

try:
    from pylint.checkers.utils import check_messages
except ImportError:
    from pylint.checkers.utils import only_required_for_messages as check_messages

from pylint.checkers import BaseChecker, BaseTokenChecker

from ansible.module_utils.compat.version import LooseVersion
from ansible.release import __version__ as ansible_version_raw
from ansible.utils.version import SemanticVersion

MSGS = {
    'E9501': ("Deprecated version (%r) found in call to Display.deprecated "
              "or AnsibleModule.deprecate",
              "ansible-deprecated-version",
              "Used when a call to Display.deprecated specifies a version "
              "less than or equal to the current version of Ansible",
              {'minversion': (2, 6)}),
    'E9502': ("Display.deprecated call without a version or date",
              "ansible-deprecated-no-version",
              "Used when a call to Display.deprecated does not specify a "
              "version or date",
              {'minversion': (2, 6)}),
    'E9503': ("Invalid deprecated version (%r) found in call to "
              "Display.deprecated or AnsibleModule.deprecate",
              "ansible-invalid-deprecated-version",
              "Used when a call to Display.deprecated specifies an invalid "
              "Ansible version number",
              {'minversion': (2, 6)}),
    'E9504': ("Deprecated version (%r) found in call to Display.deprecated "
              "or AnsibleModule.deprecate",
              "collection-deprecated-version",
              "Used when a call to Display.deprecated specifies a collection "
              "version less than or equal to the current version of this "
              "collection",
              {'minversion': (2, 6)}),
    'E9505': ("Invalid deprecated version (%r) found in call to "
              "Display.deprecated or AnsibleModule.deprecate",
              "collection-invalid-deprecated-version",
              "Used when a call to Display.deprecated specifies an invalid "
              "collection version number",
              {'minversion': (2, 6)}),
    'E9506': ("No collection name found in call to Display.deprecated or "
              "AnsibleModule.deprecate",
              "ansible-deprecated-no-collection-name",
              "The current collection name in format `namespace.name` must "
              "be provided as collection_name when calling Display.deprecated "
              "or AnsibleModule.deprecate (`ansible.builtin` for ansible-core)",
              {'minversion': (2, 6)}),
    'E9507': ("Wrong collection name (%r) found in call to "
              "Display.deprecated or AnsibleModule.deprecate",
              "wrong-collection-deprecated",
              "The name of the current collection must be passed to the "
              "Display.deprecated resp. AnsibleModule.deprecate calls "
              "(`ansible.builtin` for ansible-core)",
              {'minversion': (2, 6)}),
    'E9508': ("Expired date (%r) found in call to Display.deprecated "
              "or AnsibleModule.deprecate",
              "ansible-deprecated-date",
              "Used when a call to Display.deprecated specifies a date "
              "before today",
              {'minversion': (2, 6)}),
    'E9509': ("Invalid deprecated date (%r) found in call to "
              "Display.deprecated or AnsibleModule.deprecate",
              "ansible-invalid-deprecated-date",
              "Used when a call to Display.deprecated specifies an invalid "
              "date. It must be a string in format `YYYY-MM-DD` (ISO 8601)",
              {'minversion': (2, 6)}),
    'E9510': ("Both version and date found in call to "
              "Display.deprecated or AnsibleModule.deprecate",
              "ansible-deprecated-both-version-and-date",
              "Only one of version and date must be specified",
              {'minversion': (2, 6)}),
    'E9511': ("Removal version (%r) must be a major release, not a minor or "
              "patch release (see the specification at https://semver.org/)",
              "removal-version-must-be-major",
              "Used when a call to Display.deprecated or "
              "AnsibleModule.deprecate for a collection specifies a version "
              "which is not of the form x.0.0",
              {'minversion': (2, 6)}),
}


ANSIBLE_VERSION = LooseVersion('.'.join(ansible_version_raw.split('.')[:3]))


def _get_expr_name(node):
    """Function to get either ``attrname`` or ``name`` from ``node.func.expr``

    Created specifically for the case of ``display.deprecated`` or ``self._display.deprecated``
    """
    try:
        return node.func.expr.attrname
    except AttributeError:
        # If this fails too, we'll let it raise, the caller should catch it
        return node.func.expr.name


def _get_func_name(node):
    """Function to get either ``attrname`` or ``name`` from ``node.func``

    Created specifically for the case of ``from ansible.module_utils.common.warnings import deprecate``
    """
    try:
        return node.func.attrname
    except AttributeError:
        return node.func.name


def parse_isodate(value):
    """Parse an ISO 8601 date string."""
    msg = 'Expected ISO 8601 date string (YYYY-MM-DD)'
    if not isinstance(value, str):
        raise ValueError(msg)
    # From Python 3.7 in, there is datetime.date.fromisoformat(). For older versions,
    # we have to do things manually.
    if not re.match('^[0-9]{4}-[0-9]{2}-[0-9]{2}$', value):
        raise ValueError(msg)
    try:
        return datetime.datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(msg) from None


class AnsibleDeprecatedChecker(BaseChecker):
    """Checks for Display.deprecated calls to ensure that the ``version``
    has not passed or met the time for removal
    """

    __implements__ = (IAstroidChecker,)
    name = 'deprecated'
    msgs = MSGS

    options = (
        ('collection-name', {
            'default': None,
            'type': 'string',
            'metavar': '<name>',
            'help': 'The collection\'s name used to check collection names in deprecations.',
        }),
        ('collection-version', {
            'default': None,
            'type': 'string',
            'metavar': '<version>',
            'help': 'The collection\'s version number used to check deprecations.',
        }),
    )

    def _check_date(self, node, date):
        if not isinstance(date, str):
            self.add_message('ansible-invalid-deprecated-date', node=node, args=(date,))
            return

        try:
            date_parsed = parse_isodate(date)
        except ValueError:
            self.add_message('ansible-invalid-deprecated-date', node=node, args=(date,))
            return

        if date_parsed < datetime.date.today():
            self.add_message('ansible-deprecated-date', node=node, args=(date,))

    def _check_version(self, node, version, collection_name):
        if collection_name is None:
            collection_name = 'ansible.builtin'
        if not isinstance(version, (str, float)):
            if collection_name == 'ansible.builtin':
                symbol = 'ansible-invalid-deprecated-version'
            else:
                symbol = 'collection-invalid-deprecated-version'
            self.add_message(symbol, node=node, args=(version,))
            return

        version_no = str(version)

        if collection_name == 'ansible.builtin':
            # Ansible-base
            try:
                if not version_no:
                    raise ValueError('Version string should not be empty')
                loose_version = LooseVersion(str(version_no))
                if ANSIBLE_VERSION >= loose_version:
                    self.add_message('ansible-deprecated-version', node=node, args=(version,))
            except ValueError:
                self.add_message('ansible-invalid-deprecated-version', node=node, args=(version,))
        elif collection_name:
            # Collections
            try:
                if not version_no:
                    raise ValueError('Version string should not be empty')
                semantic_version = SemanticVersion(version_no)
                if collection_name == self.collection_name and self.collection_version is not None:
                    if self.collection_version >= semantic_version:
                        self.add_message('collection-deprecated-version', node=node, args=(version,))
                if semantic_version.major != 0 and (semantic_version.minor != 0 or semantic_version.patch != 0):
                    self.add_message('removal-version-must-be-major', node=node, args=(version,))
            except ValueError:
                self.add_message('collection-invalid-deprecated-version', node=node, args=(version,))

    @property
    def collection_name(self) -> t.Optional[str]:
        """Return the collection name, or None if ansible-core is being tested."""
        return self.linter.config.collection_name

    @property
    def collection_version(self) -> t.Optional[SemanticVersion]:
        """Return the collection version, or None if ansible-core is being tested."""
        if self.linter.config.collection_version is None:
            return None
        sem_ver = SemanticVersion(self.linter.config.collection_version)
        # Ignore pre-release for version comparison to catch issues before the final release is cut.
        sem_ver.prerelease = ()
        return sem_ver

    @check_messages(*(MSGS.keys()))
    def visit_call(self, node):
        """Visit a call node."""
        version = None
        date = None
        collection_name = None
        try:
            funcname = _get_func_name(node)
            if (funcname == 'deprecated' and 'display' in _get_expr_name(node) or
                    funcname == 'deprecate'):
                if node.keywords:
                    for keyword in node.keywords:
                        if len(node.keywords) == 1 and keyword.arg is None:
                            # This is likely a **kwargs splat
                            return
                        if keyword.arg == 'version':
                            if isinstance(keyword.value.value, astroid.Name):
                                # This is likely a variable
                                return
                            version = keyword.value.value
                        if keyword.arg == 'date':
                            if isinstance(keyword.value.value, astroid.Name):
                                # This is likely a variable
                                return
                            date = keyword.value.value
                        if keyword.arg == 'collection_name':
                            if isinstance(keyword.value.value, astroid.Name):
                                # This is likely a variable
                                return
                            collection_name = keyword.value.value
                if not version and not date:
                    try:
                        version = node.args[1].value
                    except IndexError:
                        self.add_message('ansible-deprecated-no-version', node=node)
                        return
                if version and date:
                    self.add_message('ansible-deprecated-both-version-and-date', node=node)

                if collection_name:
                    this_collection = collection_name == (self.collection_name or 'ansible.builtin')
                    if not this_collection:
                        self.add_message('wrong-collection-deprecated', node=node, args=(collection_name,))
                elif self.collection_name is not None:
                    self.add_message('ansible-deprecated-no-collection-name', node=node)

                if date:
                    self._check_date(node, date)
                elif version:
                    self._check_version(node, version, collection_name)
        except AttributeError:
            # Not the type of node we are interested in
            pass


class AnsibleDeprecatedCommentChecker(BaseTokenChecker):
    """Checks for ``# deprecated:`` comments to ensure that the ``version``
    has not passed or met the time for removal
    """

    __implements__ = (ITokenChecker,)

    name = 'deprecated-comment'
    msgs = {
        'E9601': ("Deprecated core version (%r) found: %s",
                  "ansible-deprecated-version-comment",
                  "Used when a '# deprecated:' comment specifies a version "
                  "less than or equal to the current version of Ansible",
                  {'minversion': (2, 6)}),
        'E9602': ("Deprecated comment contains invalid keys %r",
                  "ansible-deprecated-version-comment-invalid-key",
                  "Used when a '#deprecated:' comment specifies invalid data",
                  {'minversion': (2, 6)}),
        'E9603': ("Deprecated comment missing version",
                  "ansible-deprecated-version-comment-missing-version",
                  "Used when a '#deprecated:' comment specifies invalid data",
                  {'minversion': (2, 6)}),
        'E9604': ("Deprecated python version (%r) found: %s",
                  "ansible-deprecated-python-version-comment",
                  "Used when a '#deprecated:' comment specifies a python version "
                  "less than or equal to the minimum python version",
                  {'minversion': (2, 6)}),
        'E9605': ("Deprecated comment contains invalid version %r: %s",
                  "ansible-deprecated-version-comment-invalid-version",
                  "Used when a '#deprecated:' comment specifies an invalid version",
                  {'minversion': (2, 6)}),
    }

    def process_tokens(self, tokens: list[TokenInfo]) -> None:
        for token in tokens:
            if token.type == COMMENT:
                self._process_comment(token)

    def _deprecated_string_to_dict(self, token: TokenInfo, string: str) -> dict[str, str]:
        valid_keys = {'description', 'core_version', 'python_version'}
        data = dict.fromkeys(valid_keys)
        for opt in shlex.split(string):
            if '=' not in opt:
                data[opt] = None
                continue
            key, _sep, value = opt.partition('=')
            data[key] = value
        if not any((data['core_version'], data['python_version'])):
            self.add_message(
                'ansible-deprecated-version-comment-missing-version',
                line=token.start[0],
                col_offset=token.start[1],
            )
        bad = set(data).difference(valid_keys)
        if bad:
            self.add_message(
                'ansible-deprecated-version-comment-invalid-key',
                line=token.start[0],
                col_offset=token.start[1],
                args=(','.join(bad),)
            )
        return data

    def _process_python_version(self, token: TokenInfo, data: dict[str, str]) -> None:
        check_version = '.'.join(map(str, self.linter.config.py_version))

        try:
            if LooseVersion(data['python_version']) < LooseVersion(check_version):
                self.add_message(
                    'ansible-deprecated-python-version-comment',
                    line=token.start[0],
                    col_offset=token.start[1],
                    args=(
                        data['python_version'],
                        data['description'] or 'description not provided',
                    ),
                )
        except (ValueError, TypeError) as exc:
            self.add_message(
                'ansible-deprecated-version-comment-invalid-version',
                line=token.start[0],
                col_offset=token.start[1],
                args=(data['python_version'], exc)
            )

    def _process_core_version(self, token: TokenInfo, data: dict[str, str]) -> None:
        try:
            if ANSIBLE_VERSION >= LooseVersion(data['core_version']):
                self.add_message(
                    'ansible-deprecated-version-comment',
                    line=token.start[0],
                    col_offset=token.start[1],
                    args=(
                        data['core_version'],
                        data['description'] or 'description not provided',
                    )
                )
        except (ValueError, TypeError) as exc:
            self.add_message(
                'ansible-deprecated-version-comment-invalid-version',
                line=token.start[0],
                col_offset=token.start[1],
                args=(data['core_version'], exc)
            )

    def _process_comment(self, token: TokenInfo) -> None:
        if token.string.startswith('# deprecated:'):
            data = self._deprecated_string_to_dict(token, token.string[13:].strip())
            if data['core_version']:
                self._process_core_version(token, data)
            if data['python_version']:
                self._process_python_version(token, data)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(AnsibleDeprecatedChecker(linter))
    linter.register_checker(AnsibleDeprecatedCommentChecker(linter))
