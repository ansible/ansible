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


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$|%"),
    ]

    terminal_stderr_re = [
        re.compile(br"unknown command"),
        re.compile(br"syntax error,")
    ]

    def on_open_shell(self):
        try:
            prompt = self._get_prompt()
            if prompt.strip().endswith(b'%'):
                display.vvv('starting cli', self._connection._play_context.remote_addr)
                self._exec_cli_command('cli')
            for c in (b'set cli timestamp disable', b'set cli screen-length 0', b'set cli screen-width 1024'):
                self._exec_cli_command(c)
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')
