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
      - Specifies the port on the remote device that listens for connections
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
        with the remote device.
    vars:
      - name: ansible_network_os
  remote_user:
    description:
      - The username used to authenticate to the remote device when the SSH
        connection is first established.  If the remote_user is not specified,
        the connection will use the username of the logged in user.
      - Can be configured from the CLI via the C(--user) or C(-u) options.
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
      - name: ansible_ssh_password
  private_key_file:
    description:
      - The private SSH key or certificate file used to authenticate to the
        remote device when first establishing the SSH connection.
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
      - Sets the connection time, in seconds, for communicating with the
        remote device.  This timeout is used as the default timeout value for
        commands when issuing a command to the network CLI.  If the command
        does not return in timeout seconds, an error is generated.
    default: 120
  become:
    type: boolean
    description:
      - The become option will instruct the CLI session to attempt privilege
        escalation on platforms that support it.  Normally this means
        transitioning from user mode to C(enable) mode in the CLI session.
        If become is set to True and the remote device does not support
        privilege escalation or the privilege has already been elevated, then
        this option is silently ignored.
      - Can be configured from the CLI via the C(--become) or C(-b) options.
    default: False
    ini:
      - section: privilege_escalation
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
      - section: privilege_escalation
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
      - section: paramiko_connection
        key: host_key_auto_add
    env:
      - name: ANSIBLE_HOST_KEY_AUTO_ADD
  persistent_connect_timeout:
    type: int
    description:
      - Configures, in seconds, the amount of time to wait when trying to
        initially establish a persistent connection.  If this value expires
        before the connection to the remote device is completed, the connection
        will fail.
    default: 30
    ini:
      - section: persistent_connection
        key: connect_timeout
    env:
      - name: ANSIBLE_PERSISTENT_CONNECT_TIMEOUT
    vars:
      - name: ansible_connect_timeout
  persistent_command_timeout:
    type: int
    description:
      - Configures, in seconds, the amount of time to wait for a command to
        return from the remote device.  If this timer is exceeded before the
        command returns, the connection plugin will raise an exception and
        close.
    default: 30
    ini:
      - section: persistent_connection
        key: command_timeout
    env:
      - name: ANSIBLE_PERSISTENT_COMMAND_TIMEOUT
    vars:
      - name: ansible_command_timeout
  persistent_buffer_read_timeout:
    type: float
    description:
      - Configures, in seconds, the amount of time to wait for the data to be read
        from Paramiko channel after the command prompt is matched. This timeout
        value ensures that command prompt matched is correct and there is no more data
        left to be received from remote host.
    default: 0.1
    ini:
      - section: persistent_connection
        key: buffer_read_timeout
    env:
      - name: ANSIBLE_PERSISTENT_BUFFER_READ_TIMEOUT
    vars:
      - name: ansible_buffer_read_timeout
  persistent_log_messages:
    type: boolean
    description:
      - This flag will enable logging the command executed and response received from
        target device in the ansible log file. For this option to work 'log_path' ansible
        configuration option is required to be set to a file path with write access.
      - Be sure to fully understand the security implications of enabling this
        option as it could create a security vulnerability by logging sensitive information in log file.
    default: False
    ini:
      - section: persistent_connection
        key: log_messages
    env:
      - name: ANSIBLE_PERSISTENT_LOG_MESSAGES
    vars:
      - name: ansible_persistent_log_messages
  terminal_stdout_re:
    type: list
    elements: dict
    version_added: '2.9'
    description:
      - A single regex pattern or a sequence of patterns along with optional flags
        to match the command prompt from the received response chunk. This option
        accepts C(pattern) and C(flags) keys. The value of C(pattern) is a python
        regex pattern to match the response and the value of C(flags) is the value
        accepted by I(flags) argument of I(re.compile) python method to control
        the way regex is matched with the response, for example I('re.I').
    vars:
      - name: ansible_terminal_stdout_re
  terminal_stderr_re:
    type: list
    elements: dict
    version_added: '2.9'
    description:
      - This option provides the regex pattern and optional flags to match the
        error string from the received response chunk. This option
        accepts C(pattern) and C(flags) keys. The value of C(pattern) is a python
        regex pattern to match the response and the value of C(flags) is the value
        accepted by I(flags) argument of I(re.compile) python method to control
        the way regex is matched with the response, for example I('re.I').
    vars:
      - name: ansible_terminal_stderr_re
  terminal_initial_prompt:
    type: list
    version_added: '2.9'
    description:
      - A single regex pattern or a sequence of patterns to evaluate the expected
        prompt at the time of initial login to the remote host.
    vars:
      - name: ansible_terminal_initial_prompt
  terminal_initial_answer:
    type: list
    version_added: '2.9'
    description:
      - The answer to reply with if the C(terminal_initial_prompt) is matched. The value can be a single answer
        or a list of answers for multiple terminal_initial_prompt. In case the login menu has
        multiple prompts the sequence of the prompt and excepted answer should be in same order and the value
        of I(terminal_prompt_checkall) should be set to I(True) if all the values in C(terminal_initial_prompt) are
        expected to be matched and set to I(False) if any one login prompt is to be matched.
    vars:
      - name: ansible_terminal_initial_answer
  terminal_initial_prompt_checkall:
    type: boolean
    version_added: '2.9'
    description:
      - By default the value is set to I(False) and any one of the prompts mentioned in C(terminal_initial_prompt)
        option is matched it won't check for other prompts. When set to I(True) it will check for all the prompts
        mentioned in C(terminal_initial_prompt) option in the given order and all the prompts
        should be received from remote host if not it will result in timeout.
    default: False
    vars:
      - name: ansible_terminal_initial_prompt_checkall
  terminal_inital_prompt_newline:
    type: boolean
    version_added: '2.9'
    description:
      - This boolean flag, that when set to I(True) will send newline in the response if any of values
        in I(terminal_initial_prompt) is matched.
    default: True
    vars:
      - name: ansible_terminal_initial_prompt_newline
  network_cli_retries:
    description:
      - Number of attempts to connect to remote host. The delay time between the retires increases after
        every attempt by power of 2 in seconds till either the maximum attempts are exhausted or any of the
        C(persistent_command_timeout) or C(persistent_connect_timeout) timers are triggered.
    default: 3
    version_added: '2.9'
    type: integer
    env:
        - name: ANSIBLE_NETWORK_CLI_RETRIES
    ini:
        - section: persistent_connection
          key: network_cli_retries
    vars:
        - name: ansible_network_cli_retries
"""

from functools import wraps
import getpass
import json
import logging
import re
import os
import signal
import socket
import time
import traceback
from io import BytesIO

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves import cPickle
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils._text import to_bytes, to_text
from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection import NetworkConnectionBase
from ansible.plugins.loader import cliconf_loader, terminal_loader, connection_loader


def ensure_connect(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        if not self._connected:
            self._connect()
        self.update_cli_prompt_context()
        return func(self, *args, **kwargs)
    return wrapped


class AnsibleCmdRespRecv(Exception):
    pass


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
        self._command_response = None
        self._last_recv_window = None

        self._terminal = None
        self.cliconf = None
        self._paramiko_conn = None

        # Managing prompt context
        self._check_prompt = False
        self._task_uuid = to_text(kwargs.get('task_uuid', ''))

        if self._play_context.verbosity > 3:
            logging.getLogger('paramiko').setLevel(logging.DEBUG)

        if self._network_os:
            self._terminal = terminal_loader.get(self._network_os, self)
            if not self._terminal:
                raise AnsibleConnectionFailure('network os %s is not supported' % self._network_os)

            self.cliconf = cliconf_loader.get(self._network_os, self)
            if self.cliconf:
                self._sub_plugin = {'type': 'cliconf', 'name': self.cliconf._load_name, 'obj': self.cliconf}
                self.queue_message('vvvv', 'loaded cliconf plugin %s from path %s for network_os %s' %
                                   (self.cliconf._load_name, self.cliconf._original_path, self._network_os))
            else:
                self.queue_message('vvvv', 'unable to load cliconf for network_os %s' % self._network_os)
        else:
            raise AnsibleConnectionFailure(
                'Unable to automatically determine host network os. Please '
                'manually configure ansible_network_os value for this host'
            )
        self.queue_message('log', 'network_os is set to %s' % self._network_os)

    @property
    def paramiko_conn(self):
        if self._paramiko_conn is None:
            self._paramiko_conn = connection_loader.get('paramiko', self._play_context, '/dev/null')
            self._paramiko_conn.set_options(direct={'look_for_keys': not bool(self._play_context.password and not self._play_context.private_key_file)})
        return self._paramiko_conn

    def _get_log_channel(self):
        name = "p=%s u=%s | " % (os.getpid(), getpass.getuser())
        name += "paramiko [%s]" % self._play_context.remote_addr
        return name

    @ensure_connect
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

        self.queue_message('vvvv', 'updating play_context for connection')
        if self._play_context.become ^ play_context.become:
            if play_context.become is True:
                auth_pass = play_context.become_pass
                self._terminal.on_become(passwd=auth_pass)
                self.queue_message('vvvv', 'authorizing connection')
            else:
                self._terminal.on_unbecome()
                self.queue_message('vvvv', 'deauthorizing connection')

        self._play_context = play_context
        if self._paramiko_conn is not None:
            self._paramiko_conn._play_context = play_context

        if hasattr(self, 'reset_history'):
            self.reset_history()
        if hasattr(self, 'disable_response_logging'):
            self.disable_response_logging()

    def set_check_prompt(self, task_uuid):
        self._check_prompt = task_uuid

    def update_cli_prompt_context(self):
        # set cli prompt context at the start of new task run only
        if self._check_prompt and self._task_uuid != self._check_prompt:
            self._task_uuid, self._check_prompt = self._check_prompt, False
            self.set_cli_prompt_context()

    def _connect(self):
        '''
        Connects to the remote device and starts the terminal
        '''
        if not self.connected:
            self.paramiko_conn._set_log_channel(self._get_log_channel())
            self.paramiko_conn.force_persistence = self.force_persistence

            command_timeout = self.get_option('persistent_command_timeout')
            max_pause = min([self.get_option('persistent_connect_timeout'), command_timeout])
            retries = self.get_option('network_cli_retries')
            total_pause = 0

            for attempt in range(retries + 1):
                try:
                    ssh = self.paramiko_conn._connect()
                    break
                except Exception as e:
                    pause = 2 ** (attempt + 1)
                    if attempt == retries or total_pause >= max_pause:
                        raise AnsibleConnectionFailure(to_text(e, errors='surrogate_or_strict'))
                    else:
                        msg = (u"network_cli_retry: attempt: %d, caught exception(%s), "
                               u"pausing for %d seconds" % (attempt + 1, to_text(e, errors='surrogate_or_strict'), pause))

                        self.queue_message('vv', msg)
                        time.sleep(pause)
                        total_pause += pause
                        continue

            self.queue_message('vvvv', 'ssh connection done, setting terminal')
            self._connected = True

            self._ssh_shell = ssh.ssh.invoke_shell()
            self._ssh_shell.settimeout(command_timeout)

            self.queue_message('vvvv', 'loaded terminal plugin for network_os %s' % self._network_os)

            terminal_initial_prompt = self.get_option('terminal_initial_prompt') or self._terminal.terminal_initial_prompt
            terminal_initial_answer = self.get_option('terminal_initial_answer') or self._terminal.terminal_initial_answer
            newline = self.get_option('terminal_inital_prompt_newline') or self._terminal.terminal_inital_prompt_newline
            check_all = self.get_option('terminal_initial_prompt_checkall') or False

            self.receive(prompts=terminal_initial_prompt, answer=terminal_initial_answer, newline=newline, check_all=check_all)

            if self._play_context.become:
                self.queue_message('vvvv', 'firing event: on_become')
                auth_pass = self._play_context.become_pass
                self._terminal.on_become(passwd=auth_pass)

            self.queue_message('vvvv', 'firing event: on_open_shell()')
            self._terminal.on_open_shell()

            self.queue_message('vvvv', 'ssh connection has completed successfully')

        return self

    def close(self):
        '''
        Close the active connection to the device
        '''
        # only close the connection if its connected.
        if self._connected:
            self.queue_message('debug', "closing ssh connection to device")
            if self._ssh_shell:
                self.queue_message('debug', "firing event: on_close_shell()")
                self._terminal.on_close_shell()
                self._ssh_shell.close()
                self._ssh_shell = None
                self.queue_message('debug', "cli session is now closed")

                self.paramiko_conn.close()
                self._paramiko_conn = None
                self.queue_message('debug', "ssh connection has been closed successfully")
        super(Connection, self).close()

    def receive(self, command=None, prompts=None, answer=None, newline=True, prompt_retry_check=False, check_all=False):
        '''
        Handles receiving of output from command
        '''
        self._matched_prompt = None
        self._matched_cmd_prompt = None
        recv = BytesIO()
        handled = False
        command_prompt_matched = False
        matched_prompt_window = window_count = 0

        # set terminal regex values for command prompt and errors in response
        self._terminal_stderr_re = self._get_terminal_std_re('terminal_stderr_re')
        self._terminal_stdout_re = self._get_terminal_std_re('terminal_stdout_re')

        cache_socket_timeout = self._ssh_shell.gettimeout()
        command_timeout = self.get_option('persistent_command_timeout')
        self._validate_timeout_value(command_timeout, "persistent_command_timeout")
        if cache_socket_timeout != command_timeout:
            self._ssh_shell.settimeout(command_timeout)

        buffer_read_timeout = self.get_option('persistent_buffer_read_timeout')
        self._validate_timeout_value(buffer_read_timeout, "persistent_buffer_read_timeout")

        self._log_messages("command: %s" % command)
        while True:
            if command_prompt_matched:
                try:
                    signal.signal(signal.SIGALRM, self._handle_buffer_read_timeout)
                    signal.setitimer(signal.ITIMER_REAL, buffer_read_timeout)
                    data = self._ssh_shell.recv(256)
                    signal.alarm(0)
                    self._log_messages("response-%s: %s" % (window_count + 1, data))
                    # if data is still received on channel it indicates the prompt string
                    # is wrongly matched in between response chunks, continue to read
                    # remaining response.
                    command_prompt_matched = False

                    # restart command_timeout timer
                    signal.signal(signal.SIGALRM, self._handle_command_timeout)
                    signal.alarm(command_timeout)

                except AnsibleCmdRespRecv:
                    # reset socket timeout to global timeout
                    self._ssh_shell.settimeout(cache_socket_timeout)
                    return self._command_response
            else:
                data = self._ssh_shell.recv(256)
                self._log_messages("response-%s: %s" % (window_count + 1, data))
            # when a channel stream is closed, received data will be empty
            if not data:
                break

            recv.write(data)
            offset = recv.tell() - 256 if recv.tell() > 256 else 0
            recv.seek(offset)

            window = self._strip(recv.read())
            self._last_recv_window = window
            window_count += 1

            if prompts and not handled:
                handled = self._handle_prompt(window, prompts, answer, newline, False, check_all)
                matched_prompt_window = window_count
            elif prompts and handled and prompt_retry_check and matched_prompt_window + 1 == window_count:
                # check again even when handled, if same prompt repeats in next window
                # (like in the case of a wrong enable password, etc) indicates
                # value of answer is wrong, report this as error.
                if self._handle_prompt(window, prompts, answer, newline, prompt_retry_check, check_all):
                    raise AnsibleConnectionFailure("For matched prompt '%s', answer is not valid" % self._matched_cmd_prompt)

            if self._find_prompt(window):
                self._last_response = recv.getvalue()
                resp = self._strip(self._last_response)
                self._command_response = self._sanitize(resp, command)
                if buffer_read_timeout == 0.0:
                    # reset socket timeout to global timeout
                    self._ssh_shell.settimeout(cache_socket_timeout)
                    return self._command_response
                else:
                    command_prompt_matched = True

    @ensure_connect
    def send(self, command, prompt=None, answer=None, newline=True, sendonly=False, prompt_retry_check=False, check_all=False):
        '''
        Sends the command to the device in the opened shell
        '''
        if check_all:
            prompt_len = len(to_list(prompt))
            answer_len = len(to_list(answer))
            if prompt_len != answer_len:
                raise AnsibleConnectionFailure("Number of prompts (%s) is not same as that of answers (%s)" % (prompt_len, answer_len))
        try:
            cmd = b'%s\r' % command
            self._history.append(cmd)
            self._ssh_shell.sendall(cmd)
            self._log_messages('send command: %s' % cmd)
            if sendonly:
                return
            response = self.receive(command, prompt, answer, newline, prompt_retry_check, check_all)
            return to_text(response, errors='surrogate_or_strict')
        except (socket.timeout, AttributeError):
            self.queue_message('error', traceback.format_exc())
            raise AnsibleConnectionFailure("timeout value %s seconds reached while trying to send command: %s"
                                           % (self._ssh_shell.gettimeout(), command.strip()))

    def _handle_buffer_read_timeout(self, signum, frame):
        self.queue_message('vvvv', "Response received, triggered 'persistent_buffer_read_timeout' timer of %s seconds" %
                           self.get_option('persistent_buffer_read_timeout'))
        raise AnsibleCmdRespRecv()

    def _handle_command_timeout(self, signum, frame):
        msg = 'command timeout triggered, timeout value is %s secs.\nSee the timeout setting options in the Network Debug and Troubleshooting Guide.'\
              % self.get_option('persistent_command_timeout')
        self.queue_message('log', msg)
        raise AnsibleConnectionFailure(msg)

    def _strip(self, data):
        '''
        Removes ANSI codes from device response
        '''
        for regex in self._terminal.ansi_re:
            data = regex.sub(b'', data)
        return data

    def _handle_prompt(self, resp, prompts, answer, newline, prompt_retry_check=False, check_all=False):
        '''
        Matches the command prompt and responds

        :arg resp: Byte string containing the raw response from the remote
        :arg prompts: Sequence of byte strings that we consider prompts for input
        :arg answer: Sequence of Byte string to send back to the remote if we find a prompt.
                A carriage return is automatically appended to this string.
        :param prompt_retry_check: Bool value for trying to detect more prompts
        :param check_all: Bool value to indicate if all the values in prompt sequence should be matched or any one of
                          given prompt.
        :returns: True if a prompt was found in ``resp``. If check_all is True
                  will True only after all the prompt in the prompts list are matched. False otherwise.
        '''
        single_prompt = False
        if not isinstance(prompts, list):
            prompts = [prompts]
            single_prompt = True
        if not isinstance(answer, list):
            answer = [answer]
        prompts_regex = [re.compile(to_bytes(r), re.I) for r in prompts]
        for index, regex in enumerate(prompts_regex):
            match = regex.search(resp)
            if match:
                self._matched_cmd_prompt = match.group()
                self._log_messages("matched command prompt: %s" % self._matched_cmd_prompt)

                # if prompt_retry_check is enabled to check if same prompt is
                # repeated don't send answer again.
                if not prompt_retry_check:
                    prompt_answer = answer[index] if len(answer) > index else answer[0]
                    self._ssh_shell.sendall(b'%s' % prompt_answer)
                    if newline:
                        self._ssh_shell.sendall(b'\r')
                        prompt_answer += b'\r'
                    self._log_messages("matched command prompt answer: %s" % prompt_answer)
                if check_all and prompts and not single_prompt:
                    prompts.pop(0)
                    answer.pop(0)
                    return False
                return True
        return False

    def _sanitize(self, resp, command=None):
        '''
        Removes elements from the response before returning to the caller
        '''
        cleaned = []
        for line in resp.splitlines():
            if command and line.strip() == command.strip():
                continue

            for prompt in self._matched_prompt.strip().splitlines():
                if prompt.strip() in line:
                    break
            else:
                cleaned.append(line)
        return b'\n'.join(cleaned).strip()

    def _find_prompt(self, response):
        '''Searches the buffered response for a matching command prompt
        '''
        errored_response = None
        is_error_message = False

        for regex in self._terminal_stderr_re:
            if regex.search(response):
                is_error_message = True

                # Check if error response ends with command prompt if not
                # receive it buffered prompt
                for regex in self._terminal_stdout_re:
                    match = regex.search(response)
                    if match:
                        errored_response = response
                        self._matched_pattern = regex.pattern
                        self._matched_prompt = match.group()
                        self._log_messages("matched error regex '%s' from response '%s'" % (self._matched_pattern, errored_response))
                        break

        if not is_error_message:
            for regex in self._terminal_stdout_re:
                match = regex.search(response)
                if match:
                    self._matched_pattern = regex.pattern
                    self._matched_prompt = match.group()
                    self._log_messages("matched cli prompt '%s' with regex '%s' from response '%s'" % (self._matched_prompt, self._matched_pattern, response))
                    if not errored_response:
                        return True

        if errored_response:
            raise AnsibleConnectionFailure(errored_response)

        return False

    def _validate_timeout_value(self, timeout, timer_name):
        if timeout < 0:
            raise AnsibleConnectionFailure("'%s' timer value '%s' is invalid, value should be greater than or equal to zero." % (timer_name, timeout))

    def transport_test(self, connect_timeout):
        """This method enables wait_for_connection to work.

        As it is used by wait_for_connection, it is called by that module's action plugin,
        which is on the controller process, which means that nothing done on this instance
        should impact the actual persistent connection... this check is for informational
        purposes only and should be properly cleaned up.
        """

        # Force a fresh connect if for some reason we have connected before.
        self.close()
        self._connect()
        self.close()

    def _get_terminal_std_re(self, option):
        terminal_std_option = self.get_option(option)
        terminal_std_re = []

        if terminal_std_option:
            for item in terminal_std_option:
                if "pattern" not in item:
                    raise AnsibleConnectionFailure("'pattern' is a required key for option '%s',"
                                                   " received option value is %s" % (option, item))
                pattern = br"%s" % to_bytes(item['pattern'])
                flag = item.get('flags', 0)
                if flag:
                    flag = getattr(re, flag.split('.')[1])
                terminal_std_re.append(re.compile(pattern, flag))
        else:
            # To maintain backward compatibility
            terminal_std_re = getattr(self._terminal, option)

        return terminal_std_re
