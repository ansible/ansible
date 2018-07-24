# (c) 2016 Red Hat Inc.
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: Ansible Networking Team
connection: network_cli
short_description: Use network_cli to run command on network appliances
description:
  - This connection plugin provides a connection to remote devices over the
    SSH and implements a CLI shell.  This connection plugin is typically used by
    network devices for sending and receiving CLi commands to network devices.
version_added: "2.3"
options:
  host:
    description:
      - Specifies the remote device FQDN or IP address to establish the SSH
        connection to.
    default: inventory_hostname
    vars:
      - name: ansible_host
  port:
    type: int
    description:
      - Specifies the port on the remote device to listening for connections
        when establishing the SSH connection.
    default: 22
    ini:
      - section: defaults
        key: remote_port
    env:
      - name: ANSIBLE_REMOTE_PORT
    vars:
      - name: ansible_port
  network_os:
    description:
      - Configures the device platform network operating system.  This value is
        used to load the correct terminal and cliconf plugins to communicate
        with the remote device
    vars:
      - name: ansible_network_os
  remote_user:
    description:
      - The username used to authenticate to the remote device when the SSH
        connection is first established.  If the remote_user is not specified,
        the connection will use the username of the logged in user.
      - Can be configured form the CLI via the C(--user) or C(-u) options
    ini:
      - section: defaults
        key: remote_user
    env:
      - name: ANSIBLE_REMOTE_USER
    vars:
      - name: ansible_user
  password:
    description:
      - Configures the user password used to authenticate to the remote device
        when first establishing the SSH connection.
    vars:
      - name: ansible_password
      - name: ansible_ssh_pass
  private_key_file:
    description:
      - The private SSH key or certificate file used to to authenticate to the
        remote device when first establishing the SSH connection.
    ini:
     section: defaults
     key: private_key_file
    env:
      - name: ANSIBLE_PRIVATE_KEY_FILE
    vars:
      - name: ansible_private_key_file
  timeout:
    type: int
    description:
      - Sets the connection time, in seconds, for the communicating with the
        remote device.  This timeout is used as the default timeout value for
        commands when issuing a command to the network CLI.  If the command
        does not return in timeout seconds, the an error is generated.
    default: 120
  become:
    type: boolean
    description:
      - The become option will instruct the CLI session to attempt privilege
        escalation on platforms that support it.  Normally this means
        transitioning from user mode to C(enable) mode in the CLI session.
        If become is set to True and the remote device does not support
        privilege escalation or the privilege has already been elevated, then
        this option is silently ignored
      - Can be configured form the CLI via the C(--become) or C(-b) options
    default: False
    ini:
      section: privilege_escalation
      key: become
    env:
      - name: ANSIBLE_BECOME
    vars:
      - name: ansible_become
  become_method:
    description:
      - This option allows the become method to be specified in for handling
        privilege escalation.  Typically the become_method value is set to
        C(enable) but could be defined as other values.
    default: sudo
    ini:
      section: privilege_escalation
      key: become_method
    env:
      - name: ANSIBLE_BECOME_METHOD
    vars:
      - name: ansible_become_method
  host_key_auto_add:
    type: boolean
    description:
      - By default, Ansible will prompt the user before adding SSH keys to the
        known hosts file.  Since persistent connections such as network_cli run
        in background processes, the user will never be prompted.  By enabling
        this option, unknown host keys will automatically be added to the
        known hosts file.
      - Be sure to fully understand the security implications of enabling this
        option on production systems as it could create a security vulnerability.
    default: False
    ini:
      section: paramiko_connection
      key: host_key_auto_add
    env:
      - name: ANSIBLE_HOST_KEY_AUTO_ADD
  persistent_connect_timeout:
    type: int
    description:
      - Configures, in seconds, the amount of time to wait when trying to
        initially establish a persistent connection.  If this value expires
        before the connection to the remote device is completed, the connection
        will fail
    default: 30
    ini:
      - section: persistent_connection
        key: connect_timeout
    env:
      - name: ANSIBLE_PERSISTENT_CONNECT_TIMEOUT
  persistent_command_timeout:
    type: int
    description:
      - Configures, in seconds, the amount of time to wait for a command to
        return from the remote device.  If this timer is exceeded before the
        command returns, the connection plugin will raise an exception and
        close
    default: 10
    ini:
      - section: persistent_connection
        key: command_timeout
    env:
      - name: ANSIBLE_PERSISTENT_COMMAND_TIMEOUT
    vars:
      - name: ansible_command_timeout
"""

import getpass
import json
import logging
import re
import os
import socket
import traceback

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six import BytesIO, PY3
from ansible.module_utils.six.moves import cPickle
from ansible.module_utils._text import to_bytes, to_text
from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection import NetworkConnectionBase
from ansible.plugins.loader import cliconf_loader, terminal_loader, connection_loader

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(NetworkConnectionBase):
    ''' CLI (shell) SSH connections on Paramiko '''

    transport = 'network_cli'
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._ssh_shell = None

        self._matched_prompt = None
        self._matched_cmd_prompt = None
        self._matched_pattern = None
        self._last_response = None
        self._history = list()

        self._terminal = None
        self.cliconf = None
        self.paramiko_conn = None

        if self._play_context.verbosity > 3:
            logging.getLogger('paramiko').setLevel(logging.DEBUG)

    def _get_log_channel(self):
        name = "p=%s u=%s | " % (os.getpid(), getpass.getuser())
        name += "paramiko [%s]" % self._play_context.remote_addr
        return name

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
                for key in ('prompt', 'answer', 'sendonly', 'newline', 'prompt_retry_check'):
                    if cmd.get(key) is True or cmd.get(key) is False:
                        kwargs[key] = cmd[key]
                    elif cmd.get(key) is not None:
                        kwargs[key] = to_bytes(cmd[key], errors='surrogate_or_strict')
                return self.send(**kwargs)
            except ValueError:
                cmd = to_bytes(cmd, errors='surrogate_or_strict')
                return self.send(command=cmd)

        else:
            return super(Connection, self).exec_command(cmd, in_data, sudoable)

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
        if self._play_context.become ^ play_context.become:
            if play_context.become is True:
                auth_pass = play_context.become_pass
                self._terminal.on_become(passwd=auth_pass)
                messages.append('authorizing connection')
            else:
                self._terminal.on_unbecome()
                messages.append('deauthorizing connection')

        self._play_context = play_context

        self.reset_history()
        self.disable_response_logging()
        return messages

    def _connect(self):
        '''
        Connects to the remote device and starts the terminal
        '''
        if not self.connected:
            if not self._network_os:
                raise AnsibleConnectionFailure(
                    'Unable to automatically determine host network os. Please '
                    'manually configure ansible_network_os value for this host'
                )
            display.display('network_os is set to %s' % self._network_os, log_only=True)

            self.paramiko_conn = connection_loader.get('paramiko', self._play_context, '/dev/null')
            self.paramiko_conn._set_log_channel(self._get_log_channel())
            self.paramiko_conn.set_options(direct={'look_for_keys': not bool(self._play_context.password and not self._play_context.private_key_file)})
            self.paramiko_conn.force_persistence = self.force_persistence
            ssh = self.paramiko_conn._connect()

            host = self.get_option('host')
            display.vvvv('ssh connection done, setting terminal', host=host)

            self._ssh_shell = ssh.ssh.invoke_shell()
            self._ssh_shell.settimeout(self.get_option('persistent_command_timeout'))

            self._terminal = terminal_loader.get(self._network_os, self)
            if not self._terminal:
                raise AnsibleConnectionFailure('network os %s is not supported' % self._network_os)

            display.vvvv('loaded terminal plugin for network_os %s' % self._network_os, host=host)

            self.cliconf = cliconf_loader.get(self._network_os, self)
            if self.cliconf:
                display.vvvv('loaded cliconf plugin for network_os %s' % self._network_os, host=host)
                self._implementation_plugins.append(self.cliconf)
                self.cliconf.set_options()
            else:
                display.vvvv('unable to load cliconf for network_os %s' % self._network_os)

            self.receive(prompts=self._terminal.terminal_initial_prompt, answer=self._terminal.terminal_initial_answer,
                         newline=self._terminal.terminal_inital_prompt_newline)

            display.vvvv('firing event: on_open_shell()', host=host)
            self._terminal.on_open_shell()

            if self._play_context.become and self._play_context.become_method == 'enable':
                display.vvvv('firing event: on_become', host=host)
                auth_pass = self._play_context.become_pass
                self._terminal.on_become(passwd=auth_pass)

            display.vvvv('ssh connection has completed successfully', host=host)
            self._connected = True

        return self

    def close(self):
        '''
        Close the active connection to the device
        '''
        # only close the connection if its connected.
        if self._connected:
            display.debug("closing ssh connection to device", host=self._play_context.remote_addr)
            if self._ssh_shell:
                display.debug("firing event: on_close_shell()")
                self._terminal.on_close_shell()
                self._ssh_shell.close()
                self._ssh_shell = None
                display.debug("cli session is now closed")

                self.paramiko_conn.close()
                self.paramiko_conn = None
                display.debug("ssh connection has been closed successfully")
        super(Connection, self).close()

    def receive(self, command=None, prompts=None, answer=None, newline=True, prompt_retry_check=False):
        '''
        Handles receiving of output from command
        '''
        recv = BytesIO()
        handled = False

        self._matched_prompt = None
        self._matched_cmd_prompt = None
        matched_prompt_window = window_count = 0

        while True:
            data = self._ssh_shell.recv(256)

            # when a channel stream is closed, received data will be empty
            if not data:
                break

            recv.write(data)
            offset = recv.tell() - 256 if recv.tell() > 256 else 0
            recv.seek(offset)

            window = self._strip(recv.read())
            window_count += 1

            if prompts and not handled:
                handled = self._handle_prompt(window, prompts, answer, newline)
                matched_prompt_window = window_count
            elif prompts and handled and prompt_retry_check and matched_prompt_window + 1 == window_count:
                # check again even when handled, if same prompt repeats in next window
                # (like in the case of a wrong enable password, etc) indicates
                # value of answer is wrong, report this as error.
                if self._handle_prompt(window, prompts, answer, newline, prompt_retry_check):
                    raise AnsibleConnectionFailure("For matched prompt '%s', answer is not valid" % self._matched_cmd_prompt)

            if self._find_prompt(window):
                self._last_response = recv.getvalue()
                resp = self._strip(self._last_response)
                return self._sanitize(resp, command)

    def send(self, command, prompt=None, answer=None, newline=True, sendonly=False, prompt_retry_check=False):
        '''
        Sends the command to the device in the opened shell
        '''
        try:
            self._history.append(command)
            self._ssh_shell.sendall(b'%s\r' % command)
            if sendonly:
                return
            response = self.receive(command, prompt, answer, newline, prompt_retry_check)
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

    def _handle_prompt(self, resp, prompts, answer, newline, prompt_retry_check=False):
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
                # if prompt_retry_check is enabled to check if same prompt is
                # repeated don't send answer again.
                if not prompt_retry_check:
                    self._ssh_shell.sendall(b'%s' % answer)
                    if newline:
                        self._ssh_shell.sendall(b'\r')
                self._matched_cmd_prompt = match.group()
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
                        self._matched_pattern = regex.pattern
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
