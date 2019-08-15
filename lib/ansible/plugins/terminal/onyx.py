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

    terminal_stdout_re = [
        re.compile(br"(?P<prompt>(.*)( > | # )\Z)"),
    ]

    terminal_stderr_re = [
        re.compile(br"\A%|\r\n%|\n%"),
    ]

    init_commands = [b'no cli session paging enable', ]

    def on_open_shell(self):
        try:
            for cmd in self.init_commands:
                self._exec_cli_command(cmd)
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')

    def on_become(self, passwd=None):
        if self._get_prompt().endswith(b'#'):
            return

        cmd = {u'command': u'enable'}
        if passwd:
            # Note: python-3.5 cannot combine u"" and r"" together.  Thus make
            # an r string and use to_text to ensure it's text on both py2 and
            # py3.
            cmd[u'prompt'] = to_text(r"[\r\n]?password: $",
                                     errors='surrogate_or_strict')
            cmd[u'answer'] = passwd

        try:
            self._exec_cli_command(to_bytes(json.dumps(cmd),
                                            errors='surrogate_or_strict'))
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure(
                'unable to elevate privilege to enable mode')

    def on_unbecome(self):
        prompt = self._get_prompt()
        if prompt is None:
            # if prompt is None most likely the terminal is hung up at a prompt
            return

        if b'(config' in prompt:
            self._exec_cli_command(b'exit')
            self._exec_cli_command(b'disable')

        elif prompt.endswith(b'#'):
            self._exec_cli_command(b'disable')
