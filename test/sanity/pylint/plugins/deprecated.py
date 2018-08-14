# (c) 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from distutils.version import StrictVersion

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages

from ansible.release import __version__ as ansible_version_raw

MSGS = {
    'E9999': ("Deprecated version found (%r)",
              "ansible-deprecated-version",
              "",
              {'minversion': (2, 6)}),
}


ANSIBLE_VERSION = StrictVersion('.'.join(ansible_version_raw.split('.')[:3]))


class AnsibleDeprecatedChecker(BaseChecker):
    """Checks string formatting operations to ensure that the format string
    is valid and the arguments match the format string.
    """

    __implements__ = (IAstroidChecker,)
    name = 'deprecated'
    msgs = MSGS

    @check_messages(*(MSGS.keys()))
    def visit_call(self, node):
        version = None
        try:
            if node.func.attrname == 'deprecated':
                if node.keywords:
                    for keyword in node.keywords:
                        if keyword.arg == 'version':
                            version = keyword.value.value
                if not version:
                    try:
                        version = node.args[1].value
                    except IndexError:
                        return
                if ANSIBLE_VERSION >= StrictVersion(str(version)):
                    self.add_message('ansible-deprecated-version', node=node, args=(version,))
        except AttributeError:
            pass


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(AnsibleDeprecatedChecker(linter))
