# -*- coding: utf-8 -*-
#
# Copyright: (c) 2020, A10 Networks Inc.
# GNU General Public License v3.0
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import re

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes
from ansible.plugins.terminal import TerminalBase


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
        re.compile(br"Duplicate ?[\s]+"),
        re.compile(br"Object specified does not exist ?[\s]+"),
        re.compile(br"This field cannot be modified at runtime?[\s]+"),
        re.compile(br"There exists an open[\s]+")
    ]

    def on_become(self, passwd=None):
        if self._get_prompt().endswith(b'#'):
            return

        cmd = {u'command': u'enable'}
        if passwd == "" or passwd:
            cmd[u'prompt'] = "Password:"
            cmd[u'answer'] = passwd
        else:
            msg = ("ansible_become_password is required for switching to"
                   " privilege mode.")
            raise AnsibleConnectionFailure(msg)

        try:
            self._exec_cli_command(to_bytes(json.dumps(cmd),
                                            errors='surrogate_or_strict'))
            prompt = self._get_prompt()
            if prompt is None or not prompt.endswith(b'#'):
                raise AnsibleConnectionFailure('failed to elevate privilege')
            else:
                self._exec_cli_command(b'terminal length 0')
        except AnsibleConnectionFailure:
            msg = ("Unable to elevate privilege to enable mode,"
                   " check credentials.")
            raise AnsibleConnectionFailure(msg)

    def on_unbecome(self):
        prompt = self._get_prompt()
        if prompt is None:
            return

        if b'(config' in prompt:
            self._exec_cli_command(b'end')
            self._exec_cli_command(b'disable')

        elif prompt.endswith(b'#'):
            self._exec_cli_command(b'disable')
