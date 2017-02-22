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
import os
import re
import socket
import time
import signal
import json

try:
    import paramiko
    from paramiko.ssh_exception import AuthenticationException
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

from ansible.module_utils.basic import get_exception
from ansible.module_utils.network import NetworkError
from ansible.module_utils.six import BytesIO
from ansible.module_utils._text import to_native
from ansible.module_utils.network_common import to_list, ComplexDict
from ansible.module_utils.netcli import Command

ANSI_RE = [
    re.compile(r'(\x1b\[\?1h\x1b=)'),
    re.compile(r'\x08'),
    re.compile(r'\x1b[^m]*m')
]


class ShellError(Exception):

    def __init__(self, msg, command=None):
        super(ShellError, self).__init__(msg)
        self.command = command


class Shell(object):

    def __init__(self, prompts_re=None, errors_re=None, kickstart=True, timeout=10):
        self.ssh = None
        self.shell = None

        self.kickstart = kickstart
        self._matched_prompt = None

        self.prompts = prompts_re or list()
        self.errors = errors_re or list()

        self._timeout = timeout
        self._history = list()

        signal.signal(signal.SIGALRM, self.alarm_handler)

    def open(self, host, port=22, username=None, password=None,
             key_filename=None, pkey=None, look_for_keys=None,
             allow_agent=False, key_policy="loose"):

        self.ssh = paramiko.SSHClient()

        if key_policy != "ignore":
            self.ssh.load_system_host_keys()
            try:
                self.ssh.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
            except IOError:
                pass

        if key_policy == "strict":
            self.ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # unless explicitly set, disable look for keys if a password is
        # present. this changes the default search order paramiko implements
        if not look_for_keys:
            look_for_keys = password is None

        try:
            self.ssh.connect(
                host, port=port, username=username, password=password,
                timeout=self._timeout, look_for_keys=look_for_keys, pkey=pkey,
                key_filename=key_filename, allow_agent=allow_agent,
            )
            self.shell = self.ssh.invoke_shell()
            self.shell.settimeout(self._timeout)
        except socket.gaierror:
            raise ShellError("unable to resolve host name")
        except AuthenticationException:
            raise ShellError('Unable to authenticate to remote device')
        except socket.timeout:
            raise ShellError("timeout trying to connect to remote device")
        except socket.error:
            exc = get_exception()
            if exc.errno == 60:
                raise ShellError('timeout trying to connect to host')
            raise

        if self.kickstart:
            self.shell.sendall("\n")

        self.receive()

    def strip(self, data):
        for regex in ANSI_RE:
            data = regex.sub('', data)
        return data

    def alarm_handler(self, signum, frame):
        self.shell.close()
        raise ShellError('timeout trying to send command: %s' % self._history[-1])

    def receive(self, cmd=None):
        recv = BytesIO()
        handled = False

        while True:
            data = self.shell.recv(200)

            recv.write(data)
            recv.seek(recv.tell() - len(data))

            window = self.strip(recv.read().decode('utf8'))

            if cmd:
                if cmd.get('prompt') and not handled:
                    handled = self.handle_prompt(window, cmd)

            try:
                if self.find_prompt(window):
                    resp = self.strip(recv.getvalue().decode('utf8'))
                    if cmd:
                        resp = self.sanitize(cmd, resp)
                    return resp
            except ShellError:
                exc = get_exception()
                exc.command = cmd['command']
                raise

    def send(self, obj):
        try:
            self._history.append(str(obj['command']))
            cmd = '%s\r' % str(obj['command'])

            self.shell.sendall(cmd)

            if obj.get('sendonly'):
                return

            signal.alarm(self._timeout)
            out = self.receive(obj)
            signal.alarm(0)

            return (0, out, '')
        except ShellError:
            exc = get_exception()
            return (1, '', to_native(exc))

    def close(self):
        self.shell.close()

    def handle_prompt(self, resp, cmd):
        for prompt in to_list(cmd['prompt']):
            match = re.search(prompt, resp)
            if match:
                answer = '%s\r' % cmd['response']
                self.shell.sendall(answer)
                return True

    def sanitize(self, cmd, resp):
        cleaned = []
        for line in resp.splitlines():
            if line.lstrip().startswith(cmd['command']) or self.find_prompt(line):
                continue
            cleaned.append(line)
        return "\n".join(cleaned)

    def find_prompt(self, response):
        for regex in self.errors:
            if regex.search(response):
                raise ShellError('matched error in response: %s' % response)

        for regex in self.prompts:
            match = regex.search(response)
            if match:
                self._matched_prompt = match.group()
                return True


class CliBase(object):
    """Basic paramiko-based ssh transport any NetworkModule can use."""

    def __init__(self):
        if not HAS_PARAMIKO:
            raise NetworkError(
                msg='paramiko is required but does not appear to be installed.  '
                'It can be installed using  `pip install paramiko`'
            )

        self.shell = None
        self._connected = False

    def connect(self, params, kickstart=True):
        host = params['host']
        port = params.get('port') or 22

        username = params['username']
        password = params.get('password')
        key_file = params.get('ssh_keyfile')

        timeout = params.get('timeout') or 10

        try:
            self.shell = Shell(
                kickstart=kickstart,
                prompts_re=self.CLI_PROMPTS_RE,
                errors_re=self.CLI_ERRORS_RE,
                timeout=timeout
            )

            self.shell.open(host, port=port, username=username,
                            password=password, key_filename=key_file)

        except ShellError:
            exc = get_exception()
            raise NetworkError(msg='failed to connect to %s:%s' % (host, port),
                               exc=to_native(exc))

        self._connected = True

    def disconnect(self):
        self.shell.close()
        self._connected = False

    def to_command(self, obj):
        if isinstance(obj, Command):
            cmdobj = dict()
            cmdobj['command'] = obj.command
            cmdobj['response'] = obj.response
            cmdobj['prompt'] = [p.pattern for p in to_list(obj.prompt)]
            return cmdobj

        elif not isinstance(obj, dict):
            transform = ComplexDict(dict(
                command=dict(key=True),
                prompt=dict(),
                answer=dict(),
                sendonly=dict(default=False)
            ))
            return transform(obj)

        else:
            return obj

    def execute(self, commands):
        try:
            responses = list()
            for item in to_list(commands):
                item = self.to_command(item)
                rc, out, err = self.shell.send(item)
                if rc != 0:
                    raise ShellError(err)
                responses.append(out)
            return responses
        except ShellError:
            exc = get_exception()
            raise NetworkError(to_native(exc))

    run_commands = lambda self, x: self.execute(to_list(x))
    exec_command = lambda self, x: self.shell.send(self.to_command(x))
