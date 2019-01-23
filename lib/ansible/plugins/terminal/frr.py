#
# (c) 2018 Red Hat Inc.
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

from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.terminal import TerminalBase


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br"[\r\n]?[\w\+\-\.:\/\[\]]+(?:\([^\)]+\)){0,3}(?:[>#]) ?$")
    ]

    terminal_stderr_re = [
        re.compile(br"% Command incomplete", re.I),
        re.compile(br"% Unknown command", re.I),
        re.compile(br"(?:\S+) instance is already running", re.I),
        re.compile(br"% (?:Create|Specify) .* first", re.I),
        re.compile(br"(?:\S+) is not running", re.I),
        re.compile(br"% Can't find .*", re.I),
        re.compile(br"invalid input", re.I),
        re.compile(br"connection timed out", re.I),
        re.compile(br"[^\r\n]+ not found"),
    ]

    def on_open_shell(self):
        try:
            self._exec_cli_command(b'terminal length 0')
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')

    def on_become(self, passwd=None):
        # NOTE: For FRR, enable password only takes effect when telnetting to individual daemons
        #       vtysh will always drop into enable mode since it runs as a privileged process
        pass

    def on_unbecome(self):
        # NOTE: For FRR, enable password only takes effect when telnetting to individual daemons
        #       vtysh will always drop into enable mode since it runs as a privileged process
        pass
