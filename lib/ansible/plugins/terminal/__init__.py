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

from abc import ABCMeta, abstractmethod

from ansible.compat.six import with_metaclass
from ansible.errors import AnsibleConnectionFailure


class TerminalBase(with_metaclass(ABCMeta, object)):
    '''
    A base class for implementing cli connections
    '''

    terminal_stdout_re = []

    terminal_stderr_re = []

    ansi_re = [
        re.compile(r'(\x1b\[\?1h\x1b=)'),
        re.compile(r'\x08.')
    ]

    def __init__(self, connection):
        self._connection = connection

    def _exec_cli_command(self, cmd, check_rc=True):
        rc, out, err = self._connection.exec_command(cmd)
        if check_rc and rc != 0:
            raise AnsibleConnectionFailure(err)
        return rc, out, err

    def _get_prompt(self):
        for cmd in ['\n', 'prompt()']:
            rc, out, err = self._exec_cli_command(cmd)
        return out

    def on_open_shell(self):
        pass

    def on_close_shell(self):
        pass

    def on_authorize(self, passwd=None):
        pass

    def on_deauthorize(self):
        pass
