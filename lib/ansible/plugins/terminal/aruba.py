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

import json
import re

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text, to_bytes
from ansible.plugins.terminal import TerminalBase


class TerminalModule(TerminalBase):

    ansi_re = [
        # check ECMA-48 Section 5.4 (Control Sequences)
        re.compile(br'(\x1b\[\?1h\x1b=)'),
        re.compile(br'((?:\x9b|\x1b\x5b)[\x30-\x3f]*[\x20-\x2f]*[\x40-\x7e])'),
        re.compile(br'\x08.')
    ]

    terminal_stdout_re = [
        re.compile(br"[\r\n]?[\w]*\(.+\) ?#(?:\s*)$"),
        re.compile(br"[pP]assword:$"),
        re.compile(br"(?<=\s)[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\s*#\s*$"),
        re.compile(br"[\r\n]?[\w\+\-\.:\/\[\]]+(?:\([^\)]+\)){0,3}(?:[>#]) ?$"),
    ]

    terminal_stderr_re = [
        re.compile(br"% ?Error"),
        re.compile(br"Error:", re.M),
        re.compile(br"^% \w+", re.M),
        re.compile(br"% ?Bad secret"),
        re.compile(br"invalid input", re.I),
        re.compile(br"(?:incomplete|ambiguous) command", re.I),
        re.compile(br"connection timed out", re.I),
        re.compile(br"[^\r\n]+ not found", re.I),
        re.compile(br"'[^']' +returned error code: ?\d+"),
    ]

    terminal_initial_prompt = b'Press any key to continue'

    terminal_initial_answer = b'\r'

    terminal_inital_prompt_newline = False

    def on_open_shell(self):
        try:
            self._exec_cli_command(b'no pag')
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')
