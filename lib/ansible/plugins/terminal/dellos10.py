#
# (c) 2016 Red Hat Inc.
#
# This file is part of Ansible
#
# Copyright (c) 2017 Dell Inc.
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
import json

from ansible.plugins.terminal import TerminalBase
from ansible.errors import AnsibleConnectionFailure


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:#) ?$"),
        re.compile(r"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$")
    ]

    terminal_stderr_re = [
        re.compile(r"% ?Error"),
        re.compile(r"% ?Bad secret"),
        re.compile(r"Syntax error:"),
        re.compile(r"invalid input", re.I),
        re.compile(r"(?:incomplete|ambiguous) command", re.I),
        re.compile(r"connection timed out", re.I),
        re.compile(r"[^\r\n]+ not found", re.I),
        re.compile(r"'[^']' +returned error code: ?\d+"),
    ]

    def on_open_shell(self):
        try:
            self._exec_cli_command('terminal length 0')
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')

    def on_authorize(self, passwd=None):
        if self._get_prompt().endswith('#'):
            return

        cmd = {'command': 'enable'}
        if passwd:
            cmd['prompt'] = r"[\r\n]?password: $"
            cmd['answer'] = passwd

        try:
            self._exec_cli_command(json.dumps(cmd))
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to elevate privilege to enable mode')

    def on_deauthorize(self):
        prompt = self._get_prompt()
        if prompt is None:
            # if prompt is None most likely the terminal is hung up at a prompt
            return

        if prompt.strip().endswith(')#'):
            self._exec_cli_command('end')
            self._exec_cli_command('disable')

        elif prompt.endswith('#'):
            self._exec_cli_command('disable')
