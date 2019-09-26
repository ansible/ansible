# Copyright (c) 2019 - NOKIA Inc. All Rights Reserved.
# Please read the associated COPYRIGHTS file for more details.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from ansible.plugins.terminal import TerminalBase
from ansible.errors import AnsibleConnectionFailure


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br"\r?\n\r?\n\!?\*?(\((ex|gl|pr|ro)\))?\[.*\]\r?\n[AB]\:\S+\@\S+\#\s"),
        re.compile(br"\r?\n\*?[AB]:[\w\-\.\>]+\#\s")
    ]

    terminal_stderr_re = [
        re.compile(br"[\r\n]Error: .*[\r\n]+"),
        re.compile(br"[\r\n](WARNING|MINOR|MAJOR|CRITICAL): .*[\r\n]+")
    ]

    def on_open_shell(self):
        try:
            if '\n' in self._connection.get_prompt().strip():
                # node is running md-cli
                self._exec_cli_command(b'environment more false')
                self._exec_cli_command(b'//environment no more')
            else:
                # node is running classic-cli
                self._exec_cli_command(b'environment no more')

        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')
