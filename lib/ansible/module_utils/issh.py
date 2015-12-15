#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
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
"""
Ansible shared module for building modules that require an interactive
SSH Shell such as those for command line driven devices.  This module
provides a native SSH transport using paramiko and builds a base Shell
class for creating shell driven modules.

In order to use this module, include it as part of a custom
module as shown below and create and subclass Shell.

** Note: The order of the import statements does matter. **

from ansible.module_utils.basic import *
from ansible.module_utils.ssh import *

This module provides the following common argument spec for creating
shell connections:

    * host (str) - [Required]  The IPv4 address or FQDN of the device

    * port (int) - Overrides the default SSH port.

    * username (str) - [Required] The username to use to authenticate
        the SSH session.

    * password (str) - [Required] The password to use to authenticate
        the SSH session

    * connect_timeout (int) - Specifies the connection timeout in seconds

"""
import re
import socket

from StringIO import StringIO

import paramiko

def shell_argument_spec(spec=None):
    """ Generates an argument spec for the Shell class
    """
    arg_spec = dict(
        host=dict(required=True),
        port=dict(default=22, type='int'),
        username=dict(required=True),
        password=dict(required=True),
        connect_timeout=dict(default=10, type='int'),
    )
    if spec:
        arg_spec.update(spec)
    return arg_spec


class ShellError(Exception):

    def __init__(self, msg, command=None):
        super(ShellError, self).__init__(msg)
        self.message = msg
        self.command = command


class Command(object):

    def __init__(self, command, prompt=None, response=None):
        self.command = command
        self.prompt = prompt
        self.response = response

    def __str__(self):
        return self.command

class Ssh(object):

    def __init__(self):
        self.client = None

    def open(self, host, port=22, username=None, password=None,
            timeout=10, key_filename=None):

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        use_keys = password is None

        ssh.connect(host, port=port, username=username, password=password,
                    timeout=timeout, allow_agent=use_keys, look_for_keys=use_keys,
                    key_filename=key_filename)

        self.client = ssh
        return self.on_open()

    def on_open(self):
        pass

    def close(self):
        self.client.close()
        return self.on_close()

    def on_close(self):
        pass


class Shell(Ssh):

    def __init__(self):
        super(Shell, self).__init__()
        self.shell = None

        self.prompts = list()
        self.errors = list()

    def on_open(self):
        self.shell = self.client.invoke_shell()
        self.shell.settimeout(10)
        self.receive()

    def receive(self, cmd=None):
        recv = StringIO()

        while True:
            recv.write(self.shell.recv(200))
            recv.seek(recv.tell() - 200)

            window = recv.read()

            if isinstance(cmd, Command):
                self.handle_input(window, prompt=cmd.prompt,
                                  response=cmd.response)

            try:
                if self.read(window):
                    resp = recv.getvalue()
                    return self.sanitize(cmd, resp)
            except ShellError, exc:
                exc.command = cmd
                raise

    def send(self, command):
        try:
            cmd = '%s\r' % str(command)
            self.shell.sendall(cmd)
            return self.receive(command)
        except socket.timeout, exc:
            raise ShellError("timeout trying to send command", cmd)

    def handle_input(self, resp, prompt, response):
        if not prompt or not response:
            return

        prompt = to_list(prompt)
        response = to_list(response)

        for pr, ans in zip(prompt, response):
            match = pr.search(resp)
            if match:
                cmd = '%s\r' % ans
                self.shell.sendall(cmd)

    def sanitize(self, cmd, resp):
        cleaned = []
        for line in resp.splitlines():
            if line.startswith(str(cmd)) or self.read(line):
                continue
            cleaned.append(line)
        return "\n".join(cleaned)

    def read(self, response):
        for regex in self.errors:
            if regex.search(response):
                raise ShellError('{}'.format(response))

        for regex in self.prompts:
            if regex.search(response):
                return True



