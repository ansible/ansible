#
# (c) 2016 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

from ansible.plugins.terminal import TerminalBase
from ansible.errors import AnsibleConnectionFailure


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\@[\w\-\.]+:\S+?[>#\$] ?$")
    ]

    terminal_stderr_re = [
        re.compile(r"\n\s*Invalid command:"),
        re.compile(r"\nCommit failed"),
        re.compile(r"\n\s+Set failed"),
    ]

    terminal_length = os.getenv('ANSIBLE_VYOS_TERMINAL_LENGTH', 10000)

    def on_open_shell(self):
        try:
            for cmd in ['set terminal length 0', 'set terminal width 512']:
                self._exec_cli_command(cmd)
            self._exec_cli_command('set terminal length %s' % self.terminal_length)
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')

