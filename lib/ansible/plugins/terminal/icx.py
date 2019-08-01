# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from ansible.plugins.terminal import TerminalBase
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text, to_bytes
import json


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br"[\r\n]?[\w\+\-\.:\/\[\]]+(?:\([^\)]+\)){0,3}(?:[>#]) ?$")
    ]

    terminal_stderr_re = [
        re.compile(br"% ?Error"),
        re.compile(br"% ?Bad secret"),
        re.compile(br"[\r\n%] Bad passwords"),
        re.compile(br"invalid input", re.I),
        re.compile(br"(?:incomplete|ambiguous) command", re.I),
        re.compile(br"connection timed out", re.I),
        re.compile(br"[^\r\n]+ not found"),
        re.compile(br"'[^']' +returned error code: ?\d+"),
        re.compile(br"Bad mask", re.I),
        re.compile(br"% ?(\S+) ?overlaps with ?(\S+)", re.I),
        re.compile(br"[%\S] ?Error: ?[\s]+", re.I),
        re.compile(br"[%\S] ?Informational: ?[\s]+", re.I),
        re.compile(br"Command authorization failed"),
        re.compile(br"Error - *"),
        re.compile(br"Error - Incorrect username or password."),
        re.compile(br"Invalid input"),
        re.compile(br"Already a http operation is in progress"),
        re.compile(br"Flash access in progress. Please try later"),
        re.compile(br"Error: .*"),
        re.compile(br"^Error: .*", re.I),
        re.compile(br"^Ambiguous input"),
        re.compile(br"Errno")
    ]

    def on_open_shell(self):
        pass

    def __del__(self):
        try:
            self.close()
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')

    def on_become(self, passwd=None):
        if self._get_prompt().endswith(b'#'):
            return

        cmd = {u'command': u'enable'}
        cmd[u'prompt'] = to_text(r"[\r\n](?:Local_)?[Pp]assword: ?$", errors='surrogate_or_strict')
        cmd[u'answer'] = passwd
        cmd[u'prompt_retry_check'] = True
        try:
            self._exec_cli_command(to_bytes(json.dumps(cmd), errors='surrogate_or_strict'))
            prompt = self._get_prompt()
            if prompt is None or not prompt.endswith(b'#'):
                raise AnsibleConnectionFailure('failed to elevate privilege to enable mode still at prompt [%s]' % prompt)
        except AnsibleConnectionFailure as e:
            prompt = self._get_prompt()
            raise AnsibleConnectionFailure('unable to elevate privilege to enable mode, at prompt [%s] with error: %s' % (prompt, e.message))

    def on_unbecome(self):
        prompt = self._get_prompt()
        if prompt is None:
            return

        if b'(config' in prompt:
            self._exec_cli_command(b'exit')

        elif prompt.endswith(b'#'):
            self._exec_cli_command(b'exit')
