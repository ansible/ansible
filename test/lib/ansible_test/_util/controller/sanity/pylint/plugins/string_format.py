"""Ansible specific pylint plugin for checking format string usage."""

# (c) 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# -*- coding: utf-8 -*-
from __future__ import annotations

import astroid.bases
import astroid.exceptions
import astroid.nodes

try:
    from pylint.checkers.utils import check_messages
except ImportError:
    from pylint.checkers.utils import only_required_for_messages as check_messages

from pylint.checkers import BaseChecker
from pylint.checkers import utils

MSGS = {
    'E9305': ("disabled",  # kept for backwards compatibility with inline ignores, remove after 2.14 is EOL
              "ansible-format-automatic-specification",
              "disabled"),
    'E9390': ("bytes object has no .format attribute",
              "ansible-no-format-on-bytestring",
              "Used when a bytestring was used as a PEP 3101 format string "
              "as Python3 bytestrings do not have a .format attribute",
              {'minversion': (3, 0)}),
}


class AnsibleStringFormatChecker(BaseChecker):
    """Checks string formatting operations to ensure that the format string
    is valid and the arguments match the format string.
    """

    name = 'string'
    msgs = MSGS

    @check_messages(*(MSGS.keys()))
    def visit_call(self, node):
        """Visit a call node."""
        func = utils.safe_infer(node.func)
        if (isinstance(func, astroid.bases.BoundMethod)
                and isinstance(func.bound, astroid.bases.Instance)
                and func.bound.name in ('str', 'unicode', 'bytes')):
            if func.name == 'format':
                self._check_new_format(node, func)

    def _check_new_format(self, node, func):
        """ Check the new string formatting """
        if (isinstance(node.func, astroid.nodes.Attribute)
                and not isinstance(node.func.expr, astroid.nodes.Const)):
            return
        try:
            strnode = next(func.bound.infer())
        except astroid.exceptions.InferenceError:
            return
        if not isinstance(strnode, astroid.nodes.Const):
            return

        if isinstance(strnode.value, bytes):
            self.add_message('ansible-no-format-on-bytestring', node=node)
            return


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(AnsibleStringFormatChecker(linter))
