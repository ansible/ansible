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

    # compiled regular expression as stdout
    terminal_stdout_re = []

    # compiled regular expression as stderr
    terminal_stderr_re = []

    # copiled regular expression to remove ANSI codes
    ansi_re = [
        re.compile(r'(\x1b\[\?1h\x1b=)'),
        re.compile(r'\x08.')
    ]

    def __init__(self, connection):
        self._connection = connection

    def _exec_cli_command(self, cmd, check_rc=True):
        """Executes a CLI command on the device"""
        rc, out, err = self._connection.exec_command(cmd)
        if check_rc and rc != 0:
            raise AnsibleConnectionFailure(err)
        return rc, out, err

    def _get_prompt(self):
        """ Returns the current prompt from the device"""
        for cmd in ['\n', 'prompt()']:
            rc, out, err = self._exec_cli_command(cmd)
        return out

    def on_open_shell(self):
        """Called after the SSH session is established

        This method is called right after the invoke_shell() is called from
        the Paramiko SSHClient instance.  It provides an opportunity to setup
        terminal parameters such as disbling paging for instance.
        """
        pass

    def on_close_shell(self):
        """Called before the connection is closed

        This method gets called once the connection close has been requested
        but before the connection is actually closed.  It provides an
        opportunity to clean up any terminal resources before the shell is
        actually closed
        """
        pass

    def on_authorize(self, passwd=None):
        """Called when privilege escalation is requested

        This method is called when the privilege is requested to be elevated
        in the play context by setting become to True.  It is the responsibility
        of the terminal plugin to actually do the privilege escalation such
        as entering `enable` mode for instance
        """
        pass

    def on_deauthorize(self):
        """Called when privilege deescalation is requested

        This method is called when the privilege changed from escalated
        (become=True) to non escalated (become=False).  It is the responsibility
        of the this method to actually perform the deauthorization procedure
        """
        pass
