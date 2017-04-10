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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import socket
import json
import signal
import datetime
import traceback
import logging

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six.moves import StringIO
from ansible.plugins import terminal_loader
from ansible.plugins.connection import ensure_connect
from ansible.plugins.connection.paramiko_ssh import Connection as _Connection

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(_Connection):
    ''' CLI (shell) SSH connections on Paramiko '''

    transport = 'network_cli'
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._terminal = None
        self._shell = None
        self._matched_prompt = None
        self._matched_pattern = None
        self._last_response = None
        self._history = list()

        if play_context.verbosity > 3:
            logging.getLogger('paramiko').setLevel(logging.DEBUG)

    def update_play_context(self, play_context):
        """Updates the play context information for the connection"""

        display.display('updating play_context for connection', log_only=True)

        if self._play_context.become is False and play_context.become is True:
            auth_pass = play_context.become_pass
            self._terminal.on_authorize(passwd=auth_pass)

        elif self._play_context.become is True and not play_context.become:
            self._terminal.on_deauthorize()

        self._play_context = play_context

    def _connect(self):
        """Connections to the device and sets the terminal type"""

        if self._play_context.password and not self._play_context.private_key_file:
            C.PARAMIKO_LOOK_FOR_KEYS = False

        super(Connection, self)._connect()

        display.display('ssh connection done, setting terminal', log_only=True)

        network_os = self._play_context.network_os
        if not network_os:
            raise AnsibleConnectionFailure(
                'Unable to automatically determine host network os. Please '
                'manually configure ansible_network_os value for this host'
            )

        self._terminal = terminal_loader.get(network_os, self)
        if not self._terminal:
            raise AnsibleConnectionFailure('network os %s is not supported' % network_os)

        self._connected = True
        display.display('ssh connection has completed successfully', log_only=True)

    @ensure_connect
    def open_shell(self):
        display.display('attempting to open shell to device', log_only=True)
        self._shell = self.ssh.invoke_shell()
        self._shell.settimeout(self._play_context.timeout)

        self.receive()

        if self._shell:
            self._terminal.on_open_shell()

        if getattr(self._play_context, 'become', None):
            auth_pass = self._play_context.become_pass
            self._terminal.on_authorize(passwd=auth_pass)

        display.display('shell successfully opened', log_only=True)
        return (0, 'ok', '')

    def close(self):
        display.display('closing connection', log_only=True)
        self.close_shell()
        super(Connection, self).close()
        self._connected = False

    def close_shell(self):
        """Closes the vty shell if the device supports multiplexing"""
        display.display('closing shell on device', log_only=True)
        if self._shell:
            self._terminal.on_close_shell()

        if self._shell:
            self._shell.close()
            self._shell = None

        return (0, 'ok', '')

    def receive(self, obj=None):
        """Handles receiving of output from command"""
        recv = StringIO()
        handled = False

        self._matched_prompt = None

        while True:
            data = self._shell.recv(256)

            recv.write(data)
            offset = recv.tell() - 256 if recv.tell() > 256 else 0
            recv.seek(offset)

            window = self._strip(recv.read())

            if obj and (obj.get('prompt') and not handled):
                handled = self._handle_prompt(window, obj)

            if self._find_prompt(window):
                self._last_response = recv.getvalue()
                resp = self._strip(self._last_response)
                return self._sanitize(resp, obj)

    def send(self, obj):
        """Sends the command to the device in the opened shell"""
        try:
            command = obj['command']
            self._history.append(command)
            self._shell.sendall('%s\r' % command)
            if obj.get('sendonly'):
                return
            return self.receive(obj)
        except (socket.timeout, AttributeError) as exc:
            display.display(traceback.format_exc(), log_only=True)
            raise AnsibleConnectionFailure("timeout trying to send command: %s" % command.strip())

    def _strip(self, data):
        """Removes ANSI codes from device response"""
        for regex in self._terminal.ansi_re:
            data = regex.sub('', data)
        return data

    def _handle_prompt(self, resp, obj):
        """Matches the command prompt and responds"""
        if not isinstance(obj['prompt'], list):
            obj['prompt'] = [obj['prompt']]
        prompts = [re.compile(r, re.I) for r in obj['prompt']]
        answer = obj['answer']
        for regex in prompts:
            match = regex.search(resp)
            if match:
                self._shell.sendall('%s\r' % answer)
                return True

    def _sanitize(self, resp, obj=None):
        """Removes elements from the response before returning to the caller"""
        cleaned = []
        command = obj.get('command') if obj else None
        for line in resp.splitlines():
            if (command and line.startswith(command.strip())) or self._matched_prompt.strip() in line:
                continue
            cleaned.append(line)
        return str("\n".join(cleaned)).strip()

    def _find_prompt(self, response):
        """Searches the buffered response for a matching command prompt"""
        errored_response = None
        for regex in self._terminal.terminal_stderr_re:
            if regex.search(response):
                errored_response = response
                break

        for regex in self._terminal.terminal_stdout_re:
            match = regex.search(response)
            if match:
                self._matched_pattern = regex.pattern
                self._matched_prompt = match.group()
                if not errored_response:
                    return True

        if errored_response:
            raise AnsibleConnectionFailure(errored_response)

    def alarm_handler(self, signum, frame):
        """Alarm handler raised in case of command timeout """
        display.display('closing shell due to sigalarm', log_only=True)
        self.close_shell()

    def exec_command(self, cmd):
        """Executes the cmd on in the shell and returns the output

        The method accepts two forms of cmd.  The first form is as a
        string that represents the command to be executed in the shell.  The
        second form is as a JSON string with additional keyword.

        Keywords supported for cmd:
            * command - the command string to execute
            * prompt - the expected prompt generated by executing command
            * answer - the string to respond to the prompt with
            * sendonly - bool to disable waiting for response

        :arg cmd: the string that represents the command to be executed
            which can be a single command or a json encoded string
        :returns: a tuple of (return code, stdout, stderr).  The return
            code is an integer and stdout and stderr are strings
        """
        try:
            obj = json.loads(cmd)
        except (ValueError, TypeError):
            obj = {'command': str(cmd).strip()}

        if obj['command'] == 'close_shell()':
            return self.close_shell()
        elif obj['command'] == 'open_shell()':
            return self.open_shell()
        elif obj['command'] == 'prompt()':
            return (0, self._matched_prompt, '')

        try:
            if self._shell is None:
                self.open_shell()
        except AnsibleConnectionFailure as exc:
            return (1, '', str(exc))

        try:
            if not signal.getsignal(signal.SIGALRM):
                signal.signal(signal.SIGALRM, self.alarm_handler)
            signal.alarm(self._play_context.timeout)
            out = self.send(obj)
            signal.alarm(0)
            return (0, out, '')
        except (AnsibleConnectionFailure, ValueError) as exc:
            return (1, '', str(exc))
