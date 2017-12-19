# (c) 2016 Red Hat Inc.
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: Ansible Networking Team
    connection: network_cli
    short_description: Use network_cli to run command on network appliances
    description:
        - This plugin actually forces use of 'local' execution but using paramiko to establish a remote ssh shell on the appliance.
        - Also this plugin ignores the become_method but still uses the becoe_user and become_pass to
          do privilege escalation, method depending on network_os used.
    version_added: "2.3"
    options:
      network_os:
        description:
            - Appliance specific OS
        default: 'default'
        vars:
            - name: ansible_netconf_network_os
      password:
        description:
            - Secret used to authenticate
        vars:
            - name: ansible_pass
            - name: ansible_netconf_pass
      private_key_file:
        description:
            - Key or certificate file used for authentication
        ini:
            - section: defaults
              key: private_key_file
        env:
            - name: ANSIBLE_PRIVATE_KEY_FILE
        vars:
            - name: ansible_private_key_file
      timeout:
        type: int
        description:
          - Connection timeout in seconds
        default: 120
"""

import json
import logging
import re
import os
import socket
import traceback

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six import BytesIO, PY3
from ansible.module_utils.six.moves import cPickle
from ansible.module_utils._text import to_bytes, to_text
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import cliconf_loader, terminal_loader, connection_loader
from ansible.plugins.connection import ConnectionBase
from ansible.utils.path import unfrackpath

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    ''' CLI (shell) SSH connections on Paramiko '''

    transport = 'network_cli'
    has_pipelining = True
    force_persistence = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._ssh_shell = None

        self._matched_prompt = None
        self._matched_pattern = None
        self._last_response = None
        self._history = list()
        self._play_context = play_context

        self._local = connection_loader.get('local', play_context, '/dev/null')
        self._local.set_options()

        self._terminal = None
        self._cliconf = None

        self._ansible_playbook_pid = kwargs.get('ansible_playbook_pid')

        if self._play_context.verbosity > 3:
            logging.getLogger('paramiko').setLevel(logging.DEBUG)

        # reconstruct the socket_path and set instance values accordingly
        self._update_connection_state()

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if name.startswith('_'):
                raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))
            return getattr(self._cliconf, name)

    def get_prompt(self):
        """Returns the current prompt from the device"""
        return self._matched_prompt

    def exec_command(self, cmd, in_data=None, sudoable=True):
        # this try..except block is just to handle the transition to supporting
        # network_cli as a toplevel connection.  Once connection=local is gone,
        # this block can be removed as well and all calls passed directly to
        # the local connection
        if self._ssh_shell:
            try:
                cmd = json.loads(to_text(cmd, errors='surrogate_or_strict'))
                kwargs = {'command': to_bytes(cmd['command'], errors='surrogate_or_strict')}
                for key in ('prompt', 'answer', 'sendonly'):
                    if cmd.get(key) is not None:
                        kwargs[key] = to_bytes(cmd[key], errors='surrogate_or_strict')
                return self.send(**kwargs)
            except ValueError:
                cmd = to_bytes(cmd, errors='surrogate_or_strict')
                return self.send(command=cmd)

        else:
            return self._local.exec_command(cmd, in_data, sudoable)

    def put_file(self, in_path, out_path):
        return self._local.put_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        return self._local.fetch_file(in_path, out_path)

    def update_play_context(self, pc_data):
        """Updates the play context information for the connection"""
        pc_data = to_bytes(pc_data)
        if PY3:
            pc_data = cPickle.loads(pc_data, encoding='bytes')
        else:
            pc_data = cPickle.loads(pc_data)
        play_context = PlayContext()
        play_context.deserialize(pc_data)

        messages = ['updating play_context for connection']
        if self._play_context.become is False and play_context.become is True:
            auth_pass = play_context.become_pass
            self._terminal.on_become(passwd=auth_pass)
            messages.append('authorizing connection')

        elif self._play_context.become is True and not play_context.become:
            self._terminal.on_unbecome()
            messages.append('deauthorizing connection')

        self._play_context = play_context
        return messages

    def _connect(self):
        '''
        Connects to the remote device and starts the terminal
        '''
        if self.connected:
            return

        p = connection_loader.get('paramiko', self._play_context, '/dev/null')
        p.set_options(direct={'look_for_keys': not bool(self._play_context.password and not self._play_context.private_key_file)})
        p.force_persistence = self.force_persistence
        ssh = p._connect()

        display.vvvv('ssh connection done, setting terminal', host=self._play_context.remote_addr)

        self._ssh_shell = ssh.ssh.invoke_shell()
        self._ssh_shell.settimeout(self._play_context.timeout)

        network_os = self._play_context.network_os
        if not network_os:
            raise AnsibleConnectionFailure(
                'Unable to automatically determine host network os. Please '
                'manually configure ansible_network_os value for this host'
            )

        self._terminal = terminal_loader.get(network_os, self)
        if not self._terminal:
            raise AnsibleConnectionFailure('network os %s is not supported' % network_os)

        display.vvvv('loaded terminal plugin for network_os %s' % network_os, host=self._play_context.remote_addr)

        self._cliconf = cliconf_loader.get(network_os, self)
        if self._cliconf:
            display.vvvv('loaded cliconf plugin for network_os %s' % network_os, host=self._play_context.remote_addr)
        else:
            display.vvvv('unable to load cliconf for network_os %s' % network_os)

        self.receive()

        display.vvvv('firing event: on_open_shell()', host=self._play_context.remote_addr)
        self._terminal.on_open_shell()

        if self._play_context.become and self._play_context.become_method == 'enable':
            display.vvvv('firing event: on_become', host=self._play_context.remote_addr)
            auth_pass = self._play_context.become_pass
            self._terminal.on_become(passwd=auth_pass)

        display.vvvv('ssh connection has completed successfully', host=self._play_context.remote_addr)
        self._connected = True

        return self

    def _update_connection_state(self):
        '''
        Reconstruct the connection socket_path and check if it exists

        If the socket path exists then the connection is active and set
        both the _socket_path value to the path and the _connected value
        to True.  If the socket path doesn't exist, leave the socket path
        value to None and the _connected value to False
        '''
        ssh = connection_loader.get('ssh', class_only=True)
        cp = ssh._create_control_path(self._play_context.remote_addr, self._play_context.port, self._play_context.remote_user, self._play_context.connection,
                                      self._ansible_playbook_pid)

        tmp_path = unfrackpath(C.PERSISTENT_CONTROL_PATH_DIR)
        socket_path = unfrackpath(cp % dict(directory=tmp_path))

        if os.path.exists(socket_path):
            self._connected = True
            self._socket_path = socket_path

    def reset(self):
        '''
        Reset the connection
        '''
        if self._socket_path:
            display.vvvv('resetting persistent connection for socket_path %s' % self._socket_path, host=self._play_context.remote_addr)
            self.close()
        display.vvvv('reset call on connection instance', host=self._play_context.remote_addr)

    def close(self):
        '''
        Close the active connection to the device
        '''
        # only close the connection if its connected.
        if self._connected:
            display.debug("closing ssh connection to device")
            if self._ssh_shell:
                display.debug("firing event: on_close_shell()")
                self._terminal.on_close_shell()
                self._ssh_shell.close()
                self._ssh_shell = None
                display.debug("cli session is now closed")
            self._connected = False
            display.debug("ssh connection has been closed successfully")

    def receive(self, command=None, prompts=None, answer=None):
        '''
        Handles receiving of output from command
        '''
        recv = BytesIO()
        handled = False

        self._matched_prompt = None

        while True:
            data = self._ssh_shell.recv(256)

            # when a channel stream is closed, received data will be empty
            if not data:
                break

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

    def send(self, command, prompt=None, answer=None, sendonly=False):
        '''
        Sends the command to the device in the opened shell
        '''
        try:
            self._history.append(command)
            self._ssh_shell.sendall(b'%s\r' % command)
            if sendonly:
                return
            response = self.receive(command, prompt, answer)
            return to_text(response, errors='surrogate_or_strict')
        except (socket.timeout, AttributeError):
            display.vvvv(traceback.format_exc(), host=self._play_context.remote_addr)
            raise AnsibleConnectionFailure("timeout trying to send command: %s" % command.strip())

    def _strip(self, data):
        '''
        Removes ANSI codes from device response
        '''
        for regex in self._terminal.ansi_re:
            data = regex.sub(b'', data)
        return data

    def _handle_prompt(self, resp, prompts, answer):
        '''
        Matches the command prompt and responds

        :arg resp: Byte string containing the raw response from the remote
        :arg prompts: Sequence of byte strings that we consider prompts for input
        :arg answer: Byte string to send back to the remote if we find a prompt.
                A carriage return is automatically appended to this string.
        :returns: True if a prompt was found in ``resp``.  False otherwise
        '''
        if not isinstance(prompts, list):
            prompts = [prompts]
        prompts = [re.compile(r, re.I) for r in prompts]
        for regex in prompts:
            match = regex.search(resp)
            if match:
                self._ssh_shell.sendall(b'%s\r' % answer)
                return True
        return False

    def _sanitize(self, resp, command=None):
        '''
        Removes elements from the response before returning to the caller
        '''
        cleaned = []
        for line in resp.splitlines():
            if (command and line.strip() == command.strip()) or self._matched_prompt.strip() in line:
                continue
            cleaned.append(line)
        return b'\n'.join(cleaned).strip()

    def _find_prompt(self, response):
        '''Searches the buffered response for a matching command prompt
        '''
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
                        self._matched_prompt = match.group()
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
