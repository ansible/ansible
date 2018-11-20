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
from ansible.utils.display import Display

display = Display()


class TerminalModule(TerminalBase):

    ansi_re = [
        # check ECMA-48 Section 5.4 (Control Sequences)
        re.compile(br'(\x1b\[\?1h\x1b=)'),
        re.compile(br'((?:\x9b|\x1b\x5b)[\x30-\x3f]*[\x20-\x2f]*[\x40-\x7e])'),
        re.compile(br'\x08.')
    ]

    terminal_initial_prompt = [
        br'\x1bZ',
    ]

    terminal_initial_answer = b'\x1b/Z'

    terminal_stdout_re = [
        re.compile(br"\x1b<"),
        re.compile(br"\[\w+\@[\w\-\.]+\] ?> ?$"),
        re.compile(br"Please press \"Enter\" to continue!"),
        re.compile(br"Do you want to see the software license\? \[Y\/n\]: ?"),
    ]

    terminal_stderr_re = [
        re.compile(br"\nbad command name"),
        re.compile(br"\nno such item"),
        re.compile(br"\ninvalid value for"),
    ]

    def on_open_shell(self):
        prompt = self._get_prompt()
        try:
            if prompt.strip().endswith(b':'):
                self._exec_cli_command(b' ')
            if prompt.strip().endswith(b'!'):
                self._exec_cli_command(b'\n')
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to bypass license prompt')
