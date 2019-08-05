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

DOCUMENTATION = """
---
author: Ansible Networking Team
terminal: nxos
short_description: Use terminal plugin to configure nxos terminal options
description:
  - This nxos terminal plugin provides low level abstraction api's and options for
    setting the remote host terminal after initial login.
version_added: "2.9"
options:
  terminal_stdout_re:
    type: list
    description:
      - A single regex pattern or a sequence of patterns along with optional flags
        to match the command prompt from the received response chunk.
    default:
      - pattern: '[\r\n](?!\s*<)?(\x1b\S+)*[a-zA-Z_0-9]{1}[a-zA-Z0-9-_.]*[>|#](?:\s*)(\x1b\S+)*$'
      - pattern" '[\r\n]?[a-zA-Z0-9]{1}[a-zA-Z0-9-_.]*\(.+\)#(?:\s*)$'
    env:
      - name: ANSIBLE_TERMINAL_STDOUT_RE
    vars:
      - name: ansible_terminal_stdout_re
  terminal_stderr_re:
    type: list
    elements: dict
    description:
      - This option provides the regex pattern and optional flags to match the
        error string from the received response chunk.
    default:
      - pattern: '% ?Error'
      - pattern: '^error:(.*)'
        flags: 're.I'
      - pattern: '^% \w+'
        flags: 're.M'
      - pattern: '% ?Bad secret'
      - pattern: 'invalid input'
        flags: 're.I'
      - pattern: '(?:incomplete|ambiguous) command'
        flags: 're.I'
      - pattern: 'connection timed out'
        flags: 're.I'
      - pattern: '[^\r\n]+ not found'
        flags: 're.I'
      - pattern: >
                ''[^']' +returned error code: ?\d+'
      - pattern: 'syntax error'
      - pattern: 'unknown command'
      - pattern: 'user not present'
      - pattern: 'invalid (.+?)at '\^' marker'
        flags: 're.I'
      - pattern: '[B|b]aud rate of console should be.* (\d*) to increase [a-z]* level'
        flags: 're.I'
    env:
      - name: ANSIBLE_TERMINAL_STDERR_RE
    vars:
      - name: ansible_terminal_stderr_re
  terminal_initial_prompt:
    type: list
    description:
      - A single regex pattern or a sequence of patterns to evaluate the expected
        prompt at the time of initial login to the remote host.
    ini:
      - section: nxos_terminal_plugin
        key: terminal_initial_prompt
    env:
      - name: ANSIBLE_TERMINAL_INITIAL_PROMPT
    vars:
      - name: ansible_terminal_initial_prompt
  terminal_initial_answer:
    type: list
    description:
      - The answer to reply with if the C(terminal_initial_prompt) is matched. The value can be a single answer
        or a list of answer for multiple terminal_initial_prompt. In case the login menu has
        multiple prompts the sequence of the prompt and excepted answer should be in same order and the value
        of I(terminal_prompt_checkall) should be set to I(True) if all the values in C(terminal_initial_prompt) are
        expected to be matched and set to I(False) if any one login prompt is to be matched.
    ini:
      - section: nxos_terminal_plugin
        key: terminal_initial_answer
    env:
      - name: ANSIBLE_TERMINAL_INITIAL_ANSWER
    vars:
      - name: ansible_terminal_initial_answer
  terminal_initial_prompt_checkall:
    type: boolean
    description:
      - By default the value is set to I(False) and any one of the prompts mentioned in C(terminal_initial_prompt)
        option is matched it won't check for other prompts. When set to I(True) it will check for all the prompts
        mentioned in C(terminal_initial_prompt) option in the given order and all the prompts
        should be received from remote host if not it will result in timeout.
    default: False
    ini:
      - section: nxos_terminal_plugin
        key: terminal_inital_prompt_checkall
    env:
      - name: ANSIBLE_TERMINAL_INITIAL_PROMPT_CHECKALL
    vars:
      - name: ansible_terminal_initial_prompt_checkall
  terminal_inital_prompt_newline:
    type: boolean
    description:
      - This boolean flag, that when set to I(True) will send newline in the response if any of values
        in I(terminal_initial_prompt) is matched.
    default: True
    ini:
      - section: nxos_terminal_plugin
        key: terminal_inital_prompt_newline
    env:
      - name: ANSIBLE_TERMINAL_INITIAL_PROMPT_NEWLINE
    vars:
      - name: ansible_terminal_initial_prompt_newline
"""

import re
import json

from ansible.plugins.terminal import TerminalBase
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes, to_text


class TerminalModule(TerminalBase):

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

        if self.validate_user_role():
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

    def validate_user_role(self):
        user = self._connection._play_context.remote_user

        out = self._exec_cli_command('show user-account %s' % user)
        out = to_text(out, errors='surrogate_then_replace').strip()

        match = re.search(r'roles:(.+)$', out, re.M)
        if match:
            roles = match.group(1).split()
            if 'network-admin' in roles:
                return True
            return False
