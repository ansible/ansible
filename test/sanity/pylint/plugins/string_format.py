# (c) 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

import six

import astroid
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker
from pylint.checkers import utils
from pylint.checkers.utils import check_messages
try:
    from pylint.checkers.utils import parse_format_method_string
except ImportError:
    from pylint.checkers.strings import parse_format_method_string

_PY3K = sys.version_info[:2] >= (3, 0)

MSGS = {
    'E9305': ("Format string contains automatic field numbering "
              "specification",
              "ansible-format-automatic-specification",
              "Used when a PEP 3101 format string contains automatic "
              "field numbering (e.g. '{}').",
              {'minversion': (2, 6)}),
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

    __implements__ = (IAstroidChecker,)
    name = 'string'
    msgs = MSGS

    @check_messages(*(MSGS.keys()))
    def visit_call(self, node):
        func = utils.safe_infer(node.func)
        if (isinstance(func, astroid.BoundMethod)
                and isinstance(func.bound, astroid.Instance)
                and func.bound.name in ('str', 'unicode', 'bytes')):
            if func.name == 'format':
                self._check_new_format(node, func)

    def _check_new_format(self, node, func):
        """ Check the new string formatting """
        if (isinstance(node.func, astroid.Attribute)
                and not isinstance(node.func.expr, astroid.Const)):
            return
        try:
            strnode = next(func.bound.infer())
        except astroid.InferenceError:
            return
        if not isinstance(strnode, astroid.Const):
            return

        if _PY3K and isinstance(strnode.value, six.binary_type):
            self.add_message('ansible-no-format-on-bytestring', node=node)
            return
        if not isinstance(strnode.value, six.string_types):
            return

        if node.starargs or node.kwargs:
            return
        try:
            fields, num_args, manual_pos = parse_format_method_string(strnode.value)
        except utils.IncompleteFormatString:
            return

        if num_args:
            self.add_message('ansible-format-automatic-specification',
                             node=node)
            return


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(AnsibleStringFormatChecker(linter))
