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

import json
import logging
import re
import signal
import socket
import traceback

from collections import Sequence

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six import BytesIO, binary_type
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins import cliconf_loader
from ansible.plugins import terminal_loader
from ansible.plugins.connection.paramiko_ssh import Connection as _Connection
from ansible.utils.jsonrpc import Rpc

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(Rpc, _Connection):
    ''' CLI (shell) SSH connections on Paramiko '''

    transport = 'network_cli'
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._terminal = None
        self._cliconf = None
        self._shell = None
        self._matched_prompt = None
        self._matched_pattern = None
        self._last_response = None
        self._history = list()
        self._play_context = play_context

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

        self._shell = self.ssh.invoke_shell()
        self._shell.settimeout(self._play_context.timeout)

        network_os = self._play_context.network_os
        if not network_os:
            raise AnsibleConnectionFailure(
                'Unable to automatically determine host network os. Please '
                'manually configure ansible_network_os value for this host'
            )

        self._terminal = terminal_loader.get(network_os, self)
        if not self._terminal:
            raise AnsibleConnectionFailure('network os %s is not supported' % network_os)

        display.display('loaded terminal plugin for network_os %s' % network_os, log_only=True)

        self._cliconf = cliconf_loader.get(network_os, self)
        if self._cliconf:
            self._rpc.add(self._cliconf)
            display.display('loaded cliconf plugin for network_os %s' % network_os, log_only=True)
        else:
            display.display('unable to load cliconf for network_os %s' % network_os)

        self.receive()

        display.display('firing event: on_open_shell()', log_only=True)
        self._terminal.on_open_shell()

        if getattr(self._play_context, 'become', None):
            display.display('firing event: on_authorize', log_only=True)
            auth_pass = self._play_context.become_pass
            self._terminal.on_authorize(passwd=auth_pass)

        self._connected = True
        display.display('ssh connection has completed successfully', log_only=True)

    def close(self):
        """Close the active connection to the device
        """
        display.display("closing ssh connection to device", log_only=True)
        if self._shell:
            display.display("firing event: on_close_shell()", log_only=True)
            self._terminal.on_close_shell()
            self._shell.close()
            self._shell = None
            display.display("cli session is now closed", log_only=True)

        super(Connection, self).close()

        self._connected = False
        display.display("ssh connection has been closed successfully", log_only=True)

    def receive(self, command=None, prompts=None, answer=None):
        """Handles receiving of output from command"""
        recv = BytesIO()
        handled = False

        self._matched_prompt = None

        while True:
            data = self._shell.recv(256)

            recv.write(data)
            offset = recv.tell() - 256 if recv.tell() > 256 else 0
            recv.seek(offset)

            window = self._strip(recv.read())

            if prompts and not handled:
                handled = self._handle_prompt(window, prompts, answer)

            if self._find_prompt(window):
                self._last_response = recv.getvalue()
                resp = self._strip(self._last_response)
                return self._sanitize(resp, command)

    def send(self, command, prompts=None, answer=None, send_only=False):
        """Sends the command to the device in the opened shell"""
        try:
            self._history.append(command)
            self._shell.sendall(b'%s\r' % command)
            if send_only:
                return
            return self.receive(command, prompts, answer)
        except (socket.timeout, AttributeError):
            display.display(traceback.format_exc(), log_only=True)
            raise AnsibleConnectionFailure("timeout trying to send command: %s" % command.strip())

    def _strip(self, data):
        """Removes ANSI codes from device response"""
        for regex in self._terminal.ansi_re:
            data = regex.sub(b'', data)
        return data

    def _handle_prompt(self, resp, prompts, answer):
        """
        Matches the command prompt and responds

        :arg resp: Byte string containing the raw response from the remote
        :arg prompts: Sequence of byte strings that we consider prompts for input
        :arg answer: Byte string to send back to the remote if we find a prompt.
                A carriage return is automatically appended to this string.
        :returns: True if a prompt was found in ``resp``.  False otherwise
        """
        prompts = [re.compile(r, re.I) for r in prompts]
        for regex in prompts:
            match = regex.search(resp)
            if match:
                self._shell.sendall(b'%s\r' % answer)
                return True
        return False

    def _sanitize(self, resp, command=None):
        """Removes elements from the response before returning to the caller"""
        cleaned = []
        for line in resp.splitlines():
            if (command and line.startswith(command.strip())) or self._matched_prompt.strip() in line:
                continue
            cleaned.append(line)
        return b'\n'.join(cleaned).strip()

    def _find_prompt(self, response):
        """Searches the buffered response for a matching command prompt"""
        errored_response = None
        is_error_message = False
        for regex in self._terminal.terminal_stderr_re:
            if regex.search(response):
                is_error_message = True

                # Check if error response ends with command prompt if not
                # receive it buffered prompt
                for regex in self._terminal.terminal_stdout_re:
                    match = regex.search(response)
                    if match:
                        errored_response = response
                        break

        if not is_error_message:
            for regex in self._terminal.terminal_stdout_re:
                match = regex.search(response)
                if match:
                    self._matched_pattern = regex.pattern
                    self._matched_prompt = match.group()
                    if not errored_response:
                        return True

        if errored_response:
            raise AnsibleConnectionFailure(errored_response)

        return False

    def alarm_handler(self, signum, frame):
        """Alarm handler raised in case of command timeout """
        display.display('closing shell due to sigalarm', log_only=True)
        self.close()

    def exec_command(self, cmd):
        """Executes the cmd on in the shell and returns the output

        The method accepts three forms of cmd.  The first form is as a byte
        string that represents the command to be executed in the shell.  The
        second form is as a utf8 JSON byte string with additional keywords.
        The third form is a json-rpc (2.0)
        Keywords supported for cmd:
            :command: the command string to execute
            :prompt: the expected prompt generated by executing command.
                This can be a string or a list of strings
            :answer: the string to respond to the prompt with
            :sendonly: bool to disable waiting for response
        :arg cmd: the byte string that represents the command to be executed
            which can be a single command or a json encoded string.
        :returns: a tuple of (return code, stdout, stderr).  The return
            code is an integer and stdout and stderr are byte strings
        """
        try:
            obj = json.loads(to_text(cmd, errors='surrogate_or_strict'))
        except (ValueError, TypeError):
            obj = {'command': to_bytes(cmd.strip(), errors='surrogate_or_strict')}

        obj = dict((k, to_bytes(v, errors='surrogate_or_strict', nonstring='passthru')) for k, v in obj.items())
        if 'prompt' in obj:
            if isinstance(obj['prompt'], binary_type):
                # Prompt was a string
                obj['prompt'] = [obj['prompt']]
            elif not isinstance(obj['prompt'], Sequence):
                # Convert nonstrings into byte strings (to_bytes(5) => b'5')
                if obj['prompt'] is not None:
                    obj['prompt'] = [to_bytes(obj['prompt'], errors='surrogate_or_strict')]
            else:
                # Prompt was a Sequence of strings.  Make sure they're byte strings
                obj['prompt'] = [to_bytes(p, errors='surrogate_or_strict') for p in obj['prompt'] if p is not None]

        if 'jsonrpc' in obj:
            if self._cliconf:
                out = self._exec_rpc(obj)
            else:
                out = self.internal_error("cliconf is not supported for network_os %s" % self._play_context.network_os)
            return 0, to_bytes(out, errors='surrogate_or_strict'), b''

        if obj['command'] == b'prompt()':
            return 0, self._matched_prompt, b''

        try:
            if not signal.getsignal(signal.SIGALRM):
                signal.signal(signal.SIGALRM, self.alarm_handler)
            signal.alarm(self._play_context.timeout)
            out = self.send(obj['command'], obj.get('prompt'), obj.get('answer'), obj.get('sendonly'))
            signal.alarm(0)
            return 0, out, b''
        except (AnsibleConnectionFailure, ValueError) as exc:
            return 1, b'', to_bytes(exc)
