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
from ansible.module_utils.six import with_metaclass

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def enable_mode(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        prompt = self.get_prompt()
        if not str(prompt).strip().endswith('#'):
            raise AnsibleError('operation requires privilege escalation')
        return func(self, *args, **kwargs)
    return wrapped


class CliconfBase(with_metaclass(ABCMeta, object)):
    """
    A base class for implementing cli connections

    .. note:: Unlike most of Ansible, nearly all strings in
        :class:`CliconfBase` plugins are byte strings.  This is because of
        how close to the underlying platform these plugins operate.  Remember
        to mark literal strings as byte string (``b"string"``) and to use
        :func:`~ansible.module_utils._text.to_bytes` and
        :func:`~ansible.module_utils._text.to_text` to avoid unexpected
        problems.
    """

    def __init__(self, connection):
        self._connection = connection

    def _alarm_handler(self, signum, frame):
        raise AnsibleConnectionFailure('timeout waiting for command to complete')

    def send_command(self, command, prompt=None, answer=None, sendonly=False):
        """Executes a cli command and returns the results
        This method will execute the CLI command on the connection and return
        the results to the caller.  The command output will be returned as a
        string
        """
        timeout = self._connection._play_context.timeout or 30
        signal.signal(signal.SIGALRM, self._alarm_handler)
        signal.alarm(timeout)
        display.display("command: %s" % command, log_only=True)
        resp = self._connection.send(command, prompt, answer, sendonly)
        signal.alarm(0)
        return resp

    def get_prompt(self):
        """Returns the current prompt from the device"""
        return self._connection._matched_prompt

    def get_base_rpc(self):
        """Returns list of base rpc method supported by remote device"""
        return ['get_config', 'edit_config', 'get_capabilities', 'get']

    @abstractmethod
    def get_config(self, source='running'):
        """Retrieves the specified configuration from the device
        This method will retrieve the configuration specified by source and
        return it to the caller as a string.  Subsequent calls to this method
        will retrieve a new configuration from the device
        """
        pass

    @abstractmethod
    def edit_config(self, commands):
        """Loads the specified commands into the remote device
        This method will load the commands into the remote device.  This
        method will make sure the device is in the proper context before
        send the commands (eg config mode)
        """
        pass

    @abstractmethod
    def get(self, commands):
        """Execute specified command on remote device
        This method will retrieve the specified data and
        return it to the caller as a string.
        """
        pass

    @abstractmethod
    def get_capabilities(self, commands):
        """Retrieves device information and supported
        rpc methods by device platform and return result
        as a string
        """
        pass

    def commit(self, comment=None):
        """Commit configuration changes"""
        return self._connection.method_not_found("commit is not supported by network_os %s" % self._play_context.network_os)

    def discard_changes(self):
        "Discard changes in candidate datastore"
        return self._connection.method_not_found("discard_changes is not supported by network_os %s" % self._play_context.network_os)

    def put_file(self, source, destination):
        """Copies file over scp to remote device"""
        pass

    def fetch_file(self, source, destination):
        """Fetch file over scp from remote device"""
        pass
