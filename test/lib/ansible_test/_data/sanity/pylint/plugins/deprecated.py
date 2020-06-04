# (c) 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import re

from distutils.version import LooseVersion

import astroid

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages

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
              "tagged Ansible version number",
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
              "tagged collection version number",
              {'minversion': (2, 6)}),
    'E9506': ("Invalid tagged version (%r) found in call to "
              "Display.deprecated or AnsibleModule.deprecate",
              "invalid-tagged-version",
              "Used when a call to Display.deprecated specifies a version "
              "number which has no collection name tag, for example "
              "`community.general:1.2.3` or `ansible.builtin:2.10`",
              {'minversion': (2, 6)}),
    'E9507': ("Version tag for wrong collection (%r) found in call to "
              "Display.deprecated or AnsibleModule.deprecate",
              "wrong-collection-deprecated-version-tag",
              "Deprecation versions must be prefixed with the name of this "
              "collection (`ansible.builtin:` for Ansible-base)",
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
              "date. It must be a string in format `namespace.name:YYYY-MM-DD` "
              "(collection identifier followed by ISO 8601)",
              {'minversion': (2, 6)}),
    'E9510': ("Both version and date found in call to "
              "Display.deprecated or AnsibleModule.deprecate",
              "ansible-deprecated-both-version-and-date",
              "Only one of version and date must be specified",
              {'minversion': (2, 6)}),
    'E9511': ("Invalid tagged date (%r) found in call to "
              "Display.deprecated or AnsibleModule.deprecate",
              "invalid-tagged-date",
              "Used when a call to Display.deprecated specifies a date "
              "which has no collection name tag, for example "
              "`community.general:2020-01-01` or `ansible.builtin:2020-12-31`",
              {'minversion': (2, 6)}),
    'E9512': ("Date tag for wrong collection (%r) found in call to "
              "Display.deprecated or AnsibleModule.deprecate",
              "wrong-collection-deprecated-date-tag",
              "Deprecation dates must be prefixed with the name of this "
              "collection (`ansible.builtin:` for Ansible-base)",
              {'minversion': (2, 6)}),
}


ANSIBLE_VERSION = LooseVersion('.'.join(ansible_version_raw.split('.')[:3]))

TAGGED_VERSION_RE = re.compile('^([^.]+.[^.]+):(.*)$')


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
            'help': 'The collection\'s name used to check tagged version numbers in deprecations.',
        }),
        ('collection-version', {
            'default': None,
            'type': 'string',
            'metavar': '<version>',
            'help': 'The collection\'s version number used to check deprecations.',
        }),
    )

    def __init__(self, *args, **kwargs):
        self.collection_version = None
        self.collection_name = None
        super(AnsibleDeprecatedChecker, self).__init__(*args, **kwargs)

    def set_option(self, optname, value, action=None, optdict=None):
        super(AnsibleDeprecatedChecker, self).set_option(optname, value, action, optdict)
        if optname == 'collection-version' and value is not None:
            self.collection_version = SemanticVersion(self.config.collection_version)
        if optname == 'collection-name' and value is not None:
            self.collection_name = self.config.collection_name

    def _check_date(self, node, date):
        if not isinstance(date, str):
            self.add_message('invalid-tagged-date', node=node, args=(date,))
            return

        matcher = TAGGED_VERSION_RE.match(date)
        if not matcher:
            self.add_message('invalid-tagged-date', node=node, args=(date,))
            return

        collection = matcher.group(1)
        date_str = matcher.group(2)

        if collection != (self.collection_name or 'ansible.builtin'):
            self.add_message('wrong-collection-deprecated-date-tag', node=node, args=(date,))

        try:
            if parse_isodate(date_str) < datetime.date.today():
                self.add_message('ansible-deprecated-date', node=node, args=(date,))
        except ValueError:
            self.add_message('ansible-invalid-deprecated-date', node=node, args=(date,))

    def _check_version(self, node, version):
        if not isinstance(version, str):
            self.add_message('invalid-tagged-version', node=node, args=(version,))
            return

        matcher = TAGGED_VERSION_RE.match(version)
        if not matcher:
            self.add_message('invalid-tagged-version', node=node, args=(version,))
            return

        collection = matcher.group(1)
        version_no = matcher.group(2)

        if collection != (self.collection_name or 'ansible.builtin'):
            self.add_message('wrong-collection-deprecated-version-tag', node=node, args=(version,))

        if collection == 'ansible.builtin':
            # Ansible-base
            try:
                if not version_no:
                    raise ValueError('Version string should not be empty')
                loose_version = LooseVersion(str(version_no))
                if ANSIBLE_VERSION >= loose_version:
                    self.add_message('ansible-deprecated-version', node=node, args=(version,))
            except ValueError:
                self.add_message('ansible-invalid-deprecated-version', node=node, args=(version,))
        else:
            # Collections
            try:
                if not version_no:
                    raise ValueError('Version string should not be empty')
                semantic_version = SemanticVersion(version_no)
                if collection == self.collection_name and self.collection_version is not None:
                    if self.collection_version >= semantic_version:
                        self.add_message('collection-deprecated-version', node=node, args=(version,))
            except ValueError:
                self.add_message('collection-invalid-deprecated-version', node=node, args=(version,))

    @check_messages(*(MSGS.keys()))
    def visit_call(self, node):
        version = None
        date = None
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
                if not version and not date:
                    try:
                        version = node.args[1].value
                    except IndexError:
                        self.add_message('ansible-deprecated-no-version', node=node)
                        return
                if version and date:
                    self.add_message('ansible-deprecated-both-version-and-date', node=node)
                    return

                if date:
                    self._check_date(node, date)

                if version:
                    self._check_version(node, version)
        except AttributeError:
            # Not the type of node we are interested in
            pass


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(AnsibleDeprecatedChecker(linter))
