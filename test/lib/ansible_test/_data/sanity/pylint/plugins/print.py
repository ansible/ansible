# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import astroid
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker
from pylint.checkers import utils
from pylint.checkers.utils import check_messages


MSGS = {
    'E9391': ('Do not use the print function in modules.',
              'print-function-used',
              'Used when the print function is used.',
              {'minversion': (2, 6)}),
}


def is_module_path(path):
    """
    :type path: str
    :rtype: bool
    """
    return '/lib/ansible/modules/' in path or '/lib/ansible/module_utils/' in path


class AnsiblePrintFunctionChecker(BaseChecker):
    """Checks function calls to avoid that the print function is used in modules.
    """

    __implements__ = (IAstroidChecker,)
    name = 'print'
    msgs = MSGS

    @check_messages(*(MSGS.keys()))
    def visit_call(self, node):
        func = utils.safe_infer(node.func)
        if isinstance(func, astroid.scoped_nodes.FunctionDef) and func.name == 'print':
            if is_module_path(self.linter.current_file):
                self.add_message('print-function-used', node=node)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(AnsiblePrintFunctionChecker(linter))
