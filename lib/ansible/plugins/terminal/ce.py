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

import re

from ansible.plugins.terminal import TerminalBase
from ansible.errors import AnsibleConnectionFailure


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br'[\r\n]?<.+>(?:\s*)$'),
        re.compile(br'[\r\n]?\[.+\](?:\s*)$'),
    ]
    #: terminal initial prompt
    #: The password needs to be changed. Change now? [Y/N]:
    terminal_initial_prompt = br'Change\s*now\s*\?\s*\[Y\/N\]\s*:'

    #: terminal initial answer
    #: do not change password when it is asked to change with initial connection.
    terminal_initial_answer = b'N'
    terminal_stderr_re = [
        re.compile(br"% ?Error: "),
        re.compile(br"^% \w+", re.M),
        re.compile(br"% ?Bad secret"),
        re.compile(br"invalid input", re.I),
        re.compile(br"(?:incomplete|ambiguous) command", re.I),
        re.compile(br"connection timed out", re.I),
        re.compile(br"[^\r\n]+ not found", re.I),
        re.compile(br"'[^']' +returned error code: ?\d+"),
        re.compile(br"syntax error"),
        re.compile(br"unknown command"),
        re.compile(br"Error\[\d+\]: ", re.I),
        re.compile(br"Error:", re.I)
    ]

    def on_open_shell(self):
        try:
            self._exec_cli_command('screen-length 0 temporary')
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')
