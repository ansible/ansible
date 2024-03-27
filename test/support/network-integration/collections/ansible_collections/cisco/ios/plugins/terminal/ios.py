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
from __future__ import annotations


import json
import re

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.common.text.converters import to_text, to_bytes
from ansible.plugins.terminal import TerminalBase
from ansible.utils.display import Display

display = Display()


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(rb"[\r\n]?[\w\+\-\.:\/\[\]]+(?:\([^\)]+\)){0,3}(?:[>#]) ?$")
    ]

    terminal_stderr_re = [
        re.compile(rb"% ?Error"),
        # re.compile(br"^% \w+", re.M),
        re.compile(rb"% ?Bad secret"),
        re.compile(rb"[\r\n%] Bad passwords"),
        re.compile(rb"invalid input", re.I),
        re.compile(rb"(?:incomplete|ambiguous) command", re.I),
        re.compile(rb"connection timed out", re.I),
        re.compile(rb"[^\r\n]+ not found"),
        re.compile(rb"'[^']' +returned error code: ?\d+"),
        re.compile(rb"Bad mask", re.I),
        re.compile(rb"% ?(\S+) ?overlaps with ?(\S+)", re.I),
        re.compile(rb"[%\S] ?Error: ?[\s]+", re.I),
        re.compile(rb"[%\S] ?Informational: ?[\s]+", re.I),
        re.compile(rb"Command authorization failed"),
    ]

    def on_open_shell(self):
        try:
            self._exec_cli_command(b"terminal length 0")
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure("unable to set terminal parameters")

        try:
            self._exec_cli_command(b"terminal width 512")
            try:
                self._exec_cli_command(b"terminal width 0")
            except AnsibleConnectionFailure:
                pass
        except AnsibleConnectionFailure:
            display.display(
                "WARNING: Unable to set terminal width, command responses may be truncated"
            )

    def on_become(self, passwd=None):
        if self._get_prompt().endswith(b"#"):
            return

        cmd = {"command": "enable"}
        if passwd:
            # Note: python-3.5 cannot combine u"" and r"" together.  Thus make
            # an r string and use to_text to ensure it's text on both py2 and py3.
            cmd["prompt"] = to_text(
                r"[\r\n]?(?:.*)?[Pp]assword: ?$", errors="surrogate_or_strict"
            )
            cmd["answer"] = passwd
            cmd["prompt_retry_check"] = True
        try:
            self._exec_cli_command(
                to_bytes(json.dumps(cmd), errors="surrogate_or_strict")
            )
            prompt = self._get_prompt()
            if prompt is None or not prompt.endswith(b"#"):
                raise AnsibleConnectionFailure(
                    "failed to elevate privilege to enable mode still at prompt [%s]"
                    % prompt
                )
        except AnsibleConnectionFailure as e:
            prompt = self._get_prompt()
            raise AnsibleConnectionFailure(
                "unable to elevate privilege to enable mode, at prompt [%s] with error: %s"
                % (prompt, e.message)
            )

    def on_unbecome(self):
        prompt = self._get_prompt()
        if prompt is None:
            # if prompt is None most likely the terminal is hung up at a prompt
            return

        if b"(config" in prompt:
            self._exec_cli_command(b"end")
            self._exec_cli_command(b"disable")

        elif prompt.endswith(b"#"):
            self._exec_cli_command(b"disable")
