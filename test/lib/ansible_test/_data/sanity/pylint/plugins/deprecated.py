# (c) 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from distutils.version import LooseVersion

import astroid

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages

from ansible.release import __version__ as ansible_version_raw

MSGS = {
    'E9501': ("Deprecated version (%r) found in call to Display.deprecated "
              "or AnsibleModule.deprecate",
              "ansible-deprecated-version",
              "Used when a call to Display.deprecated specifies a version "
              "less than or equal to the current version of Ansible resp. "
              "this collection",
              {'minversion': (2, 6)}),
    'E9502': ("Display.deprecated call without a version",
              "ansible-deprecated-no-version",
              "Used when a call to Display.deprecated does not specify a "
              "version",
              {'minversion': (2, 6)}),
    'E9503': ("Invalid deprecated version (%r) found in call to "
              "Display.deprecated or AnsibleModule.deprecate",
              "ansible-invalid-deprecated-version",
              "Used when a call to Display.deprecated specifies an invalid "
              "version number",
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


class AnsibleDeprecatedChecker(BaseChecker):
    """Checks for Display.deprecated calls to ensure that the ``version``
    has not passed or met the time for removal
    """

    __implements__ = (IAstroidChecker,)
    name = 'deprecated'
    msgs = MSGS

    options = (
        ('collection-version', {
            'default': None,
            'type': 'string',
            'metavar': '<version>',
            'help': 'The collection\'s version number used to check deprecations.',
        }),
    )


    def __init__(self):
        self.collection_version = None
        self.version_to_check = ANSIBLE_VERSION


    def set_option(self, optname, value, action=None, optdict=None):
        if optname == 'collection-version' and value is not None:
            self.collection_version = LooseVersion(value)
            self.version_to_check = self.collection_version


    @check_messages(*(MSGS.keys()))
    def visit_call(self, node):
        version = None
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
                if not version:
                    try:
                        version = node.args[1].value
                    except IndexError:
                        self.add_message('ansible-deprecated-no-version', node=node)
                        return

                try:
                    if self.version_to_check >= LooseVersion(str(version)):
                        self.add_message('ansible-deprecated-version', node=node, args=(version,))
                except ValueError:
                    self.add_message('ansible-invalid-deprecated-version', node=node, args=(version,))
        except AttributeError:
            # Not the type of node we are interested in
            pass


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(AnsibleDeprecatedChecker(linter))
