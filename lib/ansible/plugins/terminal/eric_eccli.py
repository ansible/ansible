#
# Copyright (c) 2019 Ericsson AB.
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

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text, to_bytes
from ansible.plugins.terminal import TerminalBase
from ansible.utils.display import Display
from ansible.module_utils.six import PY3

display = Display()


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br"[\r\n]?\[.*\][a-zA-Z0-9_.-]*[>\#] ?$"),
        re.compile(br"[\r\n]?[a-zA-Z0-9_.-]*(?:\([^\)]+\))(?:[>#]) ?$"),
        re.compile(br"bash\-\d\.\d(?:[$#]) ?"),
        re.compile(br"[a-zA-Z0-9_.-]*\@[a-zA-Z0-9_.-]*\[\]\:\/flash\>")
    ]

    terminal_stderr_re = [
        re.compile(br"[\r\n]+syntax error: .*"),
        re.compile(br"Aborted: .*"),
        re.compile(br"[\r\n]+Error: .*"),
        re.compile(br"[\r\n]+% Error:.*"),
        re.compile(br"[\r\n]+% Invalid input.*"),
        re.compile(br"[\r\n]+% Incomplete command:.*")
    ]

    def on_open_shell(self):

        try:
            for cmd in (b'screen-length 0', b'screen-width 512'):
                self._exec_cli_command(cmd)
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')
