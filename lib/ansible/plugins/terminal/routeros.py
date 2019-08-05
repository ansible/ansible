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
terminal: routeros
short_description: Use terminal plugin to configure routeros terminal options
description:
  - This routeros terminal plugin provides low level abstraction api's and options for
    setting the remote host terminal after initial login.
version_added: "2.9"
options:
  terminal_stdout_re:
    type: list
    description:
      - A single regex pattern or a sequence of patterns along with optional flags
        to match the command prompt from the received response chunk.
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
      - section: routeros_terminal_plugin
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
      - section: routeros_terminal_plugin
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
      - section: routeros_terminal_plugin
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
      - section: routeros_terminal_plugin
        key: terminal_inital_prompt_newline
    env:
      - name: ANSIBLE_TERMINAL_INITIAL_PROMPT_NEWLINE
    vars:
      - name: ansible_terminal_initial_prompt_newline
"""

import re

from ansible.errors import AnsibleConnectionFailure
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
        re.compile(br"\[\w+\@[\w\s\-\.]+\] ?> ?$"),
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
