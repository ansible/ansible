#
# (c) 2017 Red Hat Inc.
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

import signal

from abc import ABCMeta, abstractmethod
from functools import wraps

from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.six import with_metaclass

try:
    from scp import SCPClient
    HAS_SCP = True
except ImportError:
    HAS_SCP = False

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def enable_mode(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        prompt = self._connection.get_prompt()
        if not to_text(prompt, errors='surrogate_or_strict').strip().endswith('#'):
            raise AnsibleError('operation requires privilege escalation')
        return func(self, *args, **kwargs)
    return wrapped


class CliconfBase(with_metaclass(ABCMeta, object)):
    """
    A base class for implementing cli connections

    .. note:: String inputs to :meth:`send_command` will be cast to byte strings
         within this method and as such are not required to be made byte strings
         beforehand.  Please avoid using literal byte strings (``b'string'``) in
         :class:`CliConfBase` plugins as this can lead to unexpected errors when
         running on Python 3

    List of supported rpc's:
        :get_config: Retrieves the specified configuration from the device
        :edit_config: Loads the specified commands into the remote device
        :get: Execute specified command on remote device
        :get_capabilities: Retrieves device information and supported rpc methods
        :commit: Load configuration from candidate to running
        :discard_changes: Discard changes to candidate datastore

    Note: List of supported rpc's for remote device can be extracted from
          output of get_capabilities()

    :returns: Returns output received from remote device as byte string

            Usage:
            from ansible.module_utils.connection import Connection

            conn = Connection()
            conn.get('show lldp neighbors detail'')
            conn.get_config('running')
            conn.edit_config(['hostname test', 'netconf ssh'])
    """

    def __init__(self, connection):
        self._connection = connection

    def _alarm_handler(self, signum, frame):
        """Alarm handler raised in case of command timeout """
        display.display('closing shell due to command timeout (%s seconds).' % self._connection._play_context.timeout, log_only=True)
        self.close()

    def send_command(self, command, prompt=None, answer=None, sendonly=False, newline=True, prompt_retry_check=False):
        """Executes a cli command and returns the results
        This method will execute the CLI command on the connection and return
        the results to the caller.  The command output will be returned as a
        string
        """
        kwargs = {'command': to_bytes(command), 'sendonly': sendonly,
                  'newline': newline, 'prompt_retry_check': prompt_retry_check}
        if prompt is not None:
            kwargs['prompt'] = to_bytes(prompt)
        if answer is not None:
            kwargs['answer'] = to_bytes(answer)

        resp = self._connection.send(**kwargs)
        return resp

    def get_base_rpc(self):
        """Returns list of base rpc method supported by remote device"""
        return ['get_config', 'edit_config', 'get_capabilities', 'get']

    @abstractmethod
    def get_config(self, source='running', format='text'):
        """Retrieves the specified configuration from the device
        This method will retrieve the configuration specified by source and
        return it to the caller as a string.  Subsequent calls to this method
        will retrieve a new configuration from the device
        :args:
            arg[0] source: Datastore from which configuration should be retrieved eg: running/candidate/startup. (optional)
                           default is running.
            arg[1] format: Output format in which configuration is retrieved
                           Note: Specified datastore should be supported by remote device.
        :kwargs:
          Keywords supported
            :command: the command string to execute
            :source: Datastore from which configuration should be retrieved
            :format: Output format in which configuration is retrieved
        :returns: Returns output received from remote device as byte string
        """
        pass

    @abstractmethod
    def edit_config(self, commands=None):
        """Loads the specified commands into the remote device
        This method will load the commands into the remote device.  This
        method will make sure the device is in the proper context before
        send the commands (eg config mode)
        :args:
            arg[0] command: List of configuration commands
        :kwargs:
          Keywords supported
            :command: the command string to execute
        :returns: Returns output received from remote device as byte string
        """
        pass

    @abstractmethod
    def get(self, command=None, prompt=None, answer=None, sendonly=False, newline=True):
        """Execute specified command on remote device
        This method will retrieve the specified data and
        return it to the caller as a string.
        :args:
             command: command in string format to be executed on remote device
             prompt: the expected prompt generated by executing command.
                            This can be a string or a list of strings (optional)
             answer: the string to respond to the prompt with (optional)
             sendonly: bool to disable waiting for response, default is false (optional)
        :returns: Returns output received from remote device as byte string
        """
        pass

    @abstractmethod
    def get_capabilities(self):
        """Retrieves device information and supported
        rpc methods by device platform and return result
        as a string
        :returns: Returns output received from remote device as byte string
        """
        pass

    def commit(self, comment=None):
        """Commit configuration changes"""
        return self._connection.method_not_found("commit is not supported by network_os %s" % self._play_context.network_os)

    def discard_changes(self):
        "Discard changes in candidate datastore"
        return self._connection.method_not_found("discard_changes is not supported by network_os %s" % self._play_context.network_os)

    def copy_file(self, source=None, destination=None, proto='scp', timeout=30):
        """Copies file over scp/sftp to remote device"""
        ssh = self._connection.paramiko_conn._connect_uncached()
        if proto == 'scp':
            if not HAS_SCP:
                raise AnsibleError("Required library scp is not installed.  Please install it using `pip install scp`")
            with SCPClient(ssh.get_transport(), socket_timeout=timeout) as scp:
                out = scp.put(source, destination)
        elif proto == 'sftp':
            with ssh.open_sftp() as sftp:
                sftp.put(source, destination)

    def get_file(self, source=None, destination=None, proto='scp', timeout=30):
        """Fetch file over scp/sftp from remote device"""
        ssh = self._connection.paramiko_conn._connect_uncached()
        if proto == 'scp':
            if not HAS_SCP:
                raise AnsibleError("Required library scp is not installed.  Please install it using `pip install scp`")
            with SCPClient(ssh.get_transport(), socket_timeout=timeout) as scp:
                scp.get(source, destination)
        elif proto == 'sftp':
            with ssh.open_sftp() as sftp:
                sftp.get(source, destination)
