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

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six.moves import StringIO
from ansible.plugins import terminal_loader
from ansible.plugins.connection.paramiko_ssh import Connection as _Connection


class Connection(_Connection):
    ''' CLI SSH based connections on Paramiko '''

    transport = 'network_cli'
    has_pipelining = False

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        assert self._play_context.network_os, 'ansible_network_os must be set'

        self._terminal = terminal_loader.get(self._play_context.network_os, self)
        if not self._terminal:
            raise AnsibleConnectionFailure('network os %s is not supported' % self._play_context.network_os)

        self._shell = None

        self._matched_prompt = None
        self._matched_pattern = None
        self._last_response = None
        self._history = list()

    def update_play_context(self, play_context):
        if self._play_context.become is False and play_context.become is True:
            auth_pass = play_context.become_pass
            self._terminal.on_authorize(passwd=auth_pass)

        elif self._play_context.become is True and not play_context.become:
            self._terminal.on_deauthorize()

        self._play_context = play_context

    def _connect(self):
        super(Connection, self)._connect()
        return (0, 'connected', '')

    def open_shell(self, timeout=10):
        self._shell = self.ssh.invoke_shell()
        self._shell.settimeout(self._play_context.timeout)

        self.receive()

        if self._shell:
            self._terminal.on_open_shell()

        if hasattr(self._play_context, 'become'):
            if self._play_context.become:
                auth_pass = self._play_context.become_pass
                self._terminal.on_authorize(passwd=auth_pass)

    def close(self):
        self.close_shell()
        super(Connection, self).close()

    def close_shell(self):
        if self._shell:
            self._terminal.on_close_shell()

        if self._terminal.supports_multiplexing and self._shell:
            self._shell.close()
            self._shell = None

        return (0, 'shell closed', '')

    def receive(self, obj=None):
        recv = StringIO()
        handled = False

        self._matched_prompt = None

        while True:
            data = self._shell.recv(256)

            recv.write(data)
            recv.seek(recv.tell() - 256)

            window = self._strip(recv.read())

            if obj and (obj.get('prompt') and not handled):
                handled = self._handle_prompt(window, obj)

            if self._find_prompt(window):
                self._last_response = recv.getvalue()
                resp = self._strip(self._last_response)
                return self._sanitize(resp, obj)

    def send(self, obj):
        try:
            command = obj['command']
            self._history.append(command)
            self._shell.sendall('%s\r' % command)
            return self.receive(obj)
        except (socket.timeout, AttributeError):
            raise AnsibleConnectionFailure("timeout trying to send command: %s" % command.strip())

    def _strip(self, data):
        for regex in self._terminal.ansi_re:
            data = regex.sub('', data)
        return data

    def _handle_prompt(self, resp, obj):
        prompt = re.compile(obj['prompt'], re.I)
        answer = obj['answer']
        match = prompt.search(resp)
        if match:
            self._shell.sendall('%s\r' % answer)
            return True

    def _sanitize(self, resp, obj=None):
        cleaned = []
        command = obj.get('command') if obj else None
        for line in resp.splitlines():
            if (command and line.startswith(command.strip())) or self._find_prompt(line):
                continue
            cleaned.append(line)
        return str("\n".join(cleaned)).strip()

    def _find_prompt(self, response):
        for regex in self._terminal.terminal_errors_re:
            if regex.search(response):
                raise AnsibleConnectionFailure(response)

        for regex in self._terminal.terminal_prompts_re:
            match = regex.search(response)
            if match:
                self._matched_pattern = regex.pattern
                self._matched_prompt = match.group()
                return True

    def alarm_handler(self, signum, frame):
        self.close_shell()

    def exec_command(self, cmd):
        ''' {'command': <str>, 'prompt': <str>, 'answer': <str>} '''

        try:
            obj = json.loads(cmd)
        except ValueError:
            obj = {'command': str(cmd).strip()}

        if obj['command'] == 'close_shell()':
            return self.close_shell()
        elif obj['command'] == 'prompt()':
            return (0, self._matched_prompt, '')
        elif obj['command'] == 'history()':
            return (0, self._history, '')

        try:
            if self._shell is None:
                self.open_shell()
        except AnsibleConnectionFailure as exc:
            return (1, '', str(exc))

        try:
            out = self.send(obj)
            return (0, out, '')
        except (AnsibleConnectionFailure, ValueError) as exc:
            return (1, '', str(exc))
