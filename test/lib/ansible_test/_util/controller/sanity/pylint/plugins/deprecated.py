"""Ansible specific plyint plugin for checking deprecations."""
# (c) 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
import re
import typing as t

import astroid

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages

from ansible.module_utils.compat.version import LooseVersion
from ansible.module_utils.six import string_types
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
    """Funciton to get either ``attrname`` or ``name`` from ``node.func.expr``

    Created specifically for the case of ``display.deprecated`` or ``self._display.deprecated``
    """
    try:
        return node.func.expr.attrname
    except AttributeError:
        # If this fails too, we'll let it raise, the caller should catch it
        return node.func.expr.name


def parse_isodate(value):
    """Parse an ISO 8601 date string."""
    msg = 'Expected ISO 8601 date string (YYYY-MM-DD)'
    if not isinstance(value, string_types):
        raise ValueError(msg)
    # From Python 3.7 in, there is datetime.date.fromisoformat(). For older versions,
    # we have to do things manually.
    if not re.match('^[0-9]{4}-[0-9]{2}-[0-9]{2}$', value):
        raise ValueError(msg)
    try:
        return datetime.datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(msg)


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
        return self.config.collection_name

    @property
    def collection_version(self) -> t.Optional[SemanticVersion]:
        """Return the collection version, or None if ansible-core is being tested."""
        return SemanticVersion(self.config.collection_version) if self.config.collection_version is not None else None

    @check_messages(*(MSGS.keys()))
    def visit_call(self, node):
        """Visit a call node."""
        version = None
        date = None
        collection_name = None
        try:
            if (node.func.attrname == 'deprecated' and 'display' in _get_expr_name(node) or
                    node.func.attrname == 'deprecate' and _get_expr_name(node)):
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


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(AnsibleDeprecatedChecker(linter))
