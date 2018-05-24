# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

from ansible.plugins.terminal import TerminalBase
from ansible.errors import AnsibleConnectionFailure


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(br"\@[\w\-\.]+:\S+?[>#\$] ?$")
    ]

    terminal_stderr_re = [
        re.compile(br"\n\s*command not found"),
        re.compile(br"\nInvalid command"),
        re.compile(br"\nCommit failed"),
        re.compile(br"\n\s*Set failed"),
    ]

    terminal_length = os.getenv('ANSIBLE_EDGEOS_TERMINAL_LENGTH', 10000)

    def on_open_shell(self):
        try:
            self._exec_cli_command('export VYATTA_PAGER=cat')
            self._exec_cli_command('stty rows %s' % self.terminal_length)
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')
