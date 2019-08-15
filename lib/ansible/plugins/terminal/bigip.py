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

from ansible.plugins.terminal import TerminalBase
from ansible.errors import AnsibleConnectionFailure


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br"[\r\n]?(?:\([^\)]+\)){,5}(?:>|#) ?$"),
        re.compile(br"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(br"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$"),
        re.compile(br"(?:new|confirm) password:")
    ]

    terminal_stderr_re = [
        re.compile(br"% ?Error"),
        re.compile(br"Syntax Error", re.I),
        re.compile(br"% User not present"),
        re.compile(br"% ?Bad secret"),
        re.compile(br"invalid input", re.I),
        re.compile(br"(?:incomplete|ambiguous) command", re.I),
        re.compile(br"connection timed out", re.I),
        re.compile(br"the new password was not confirmed", re.I),
        re.compile(br"[^\r\n]+ not found", re.I),
        re.compile(br"'[^']' +returned error code: ?\d+"),
        re.compile(br"[^\r\n]\/bin\/(?:ba)?sh")
    ]

    def on_open_shell(self):
        try:
            self._exec_cli_command(b'modify cli preference display-threshold 0 pager disabled')
            self._exec_cli_command(b'run /util bash -c "stty cols 1000000" 2> /dev/null')
        except AnsibleConnectionFailure as ex:
            output = str(ex)
            if 'modify: command not found' in output:
                try:
                    self._exec_cli_command(b'tmsh modify cli preference display-threshold 0 pager disabled')
                    self._exec_cli_command(b'stty cols 1000000 2> /dev/null')
                except AnsibleConnectionFailure as ex:
                    raise AnsibleConnectionFailure('unable to set terminal parameters')
