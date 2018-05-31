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
import json

from ansible.plugins.terminal import TerminalBase
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes, to_text


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br'[\r\n]?(?!\s*<)?(\x1b\S+)*[a-zA-Z_0-9]{1}[a-zA-Z0-9-_.]*[>|#](?:\s*)*(\x1b\S+)*$'),
        re.compile(br'[\r\n]?[a-zA-Z0-9]{1}[a-zA-Z0-9-_.]*\(.+\)#(?:\s*)$')
    ]

    terminal_stderr_re = [
        re.compile(br"% ?Error"),
        re.compile(br"^error:(.*)", re.I),
        re.compile(br"^% \w+", re.M),
        re.compile(br"% ?Bad secret"),
        re.compile(br"invalid input", re.I),
        re.compile(br"(?:incomplete|ambiguous) command", re.I),
        re.compile(br"connection timed out", re.I),
        re.compile(br"[^\r\n]+ not found", re.I),
        re.compile(br"'[^']' +returned error code: ?\d+"),
        re.compile(br"syntax error"),
        re.compile(br"unknown command"),
        re.compile(br"user not present"),
        re.compile(br"invalid (.+?)at '\^' marker", re.I)
    ]

    def on_become(self, passwd=None):
        if self._get_prompt().endswith(b'enable#'):
            return

        out = self._exec_cli_command('show privilege')
        out = to_text(out, errors='surrogate_then_replace').strip()
        if 'Disabled' in out:
            raise AnsibleConnectionFailure('Feature privilege is not enabled')

        # if already at privilege level 15 return
        if '15' in out:
            return

        cmd = {u'command': u'enable'}
        if passwd:
            cmd[u'prompt'] = to_text(r"(?i)[\r\n]?Password: $", errors='surrogate_or_strict')
            cmd[u'answer'] = passwd
            cmd[u'prompt_retry_check'] = True

        try:
            self._exec_cli_command(to_bytes(json.dumps(cmd), errors='surrogate_or_strict'))
            prompt = self._get_prompt()
            if prompt is None or not prompt.strip().endswith(b'enable#'):
                raise AnsibleConnectionFailure('failed to elevate privilege to enable mode still at prompt [%s]' % prompt)
        except AnsibleConnectionFailure as e:
            prompt = self._get_prompt()
            raise AnsibleConnectionFailure('unable to elevate privilege to enable mode, at prompt [%s] with error: %s' % (prompt, e.message))

    def on_unbecome(self):
        prompt = self._get_prompt()
        if prompt is None:
            # if prompt is None most likely the terminal is hung up at a prompt
            return

        if b'(config' in prompt:
            self._exec_cli_command('end')
            self._exec_cli_command('exit')

        elif prompt.endswith(b'enable#'):
            self._exec_cli_command('exit')

    def on_open_shell(self):
        try:
            for cmd in ('terminal length 0', 'terminal width 511'):
                self._exec_cli_command(cmd)
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')
