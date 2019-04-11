# 2017 Red Hat Inc.
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
author: Ansible Core Team
connection: persistent
short_description: Use a persistent unix socket for connection
description:
  - This is a helper plugin to allow making other connections persistent.
version_added: "2.3"
options:
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
import os
import pty
import json
import subprocess
import sys
import termios

from ansible import constants as C
from ansible.plugins.loader import become_loader, cliconf_loader, connection_loader, httpapi_loader, netconf_loader, terminal_loader
from ansible.plugins.connection import ConnectionBase
from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection as SocketConnection, write_to_file_descriptor
from ansible.errors import AnsibleError
from ansible.utils.display import Display

display = Display()


class Connection(ConnectionBase):
    ''' Local based connections '''

    transport = 'persistent'
    has_pipelining = False

    def _connect(self):
        self._connected = True
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        display.vvvv('exec_command(), socket_path=%s' % self.socket_path, host=self._play_context.remote_addr)
        connection = SocketConnection(self.socket_path)
        out = connection.exec_command(cmd, in_data=in_data, sudoable=sudoable)
        return 0, out, ''

    def put_file(self, in_path, out_path):
        pass

    def fetch_file(self, in_path, out_path):
        pass

    def close(self):
        self._connected = False

    def run(self):
        """Returns the path of the persistent connection socket.

        Attempts to ensure (within playcontext.timeout seconds) that the
        socket path exists. If the path exists (or the timeout has expired),
        returns the socket path.
        """
        display.vvvv('starting connection from persistent connection plugin', host=self._play_context.remote_addr)
        socket_path = self._start_connection()
        display.vvvv('local domain socket path is %s' % socket_path, host=self._play_context.remote_addr)
        setattr(self, '_socket_path', socket_path)
        return socket_path

    def _start_connection(self):
        '''
        Starts the persistent connection
        '''
        candidate_paths = [C.ANSIBLE_CONNECTION_PATH or os.path.dirname(sys.argv[0])]
        candidate_paths.extend(os.environ['PATH'].split(os.pathsep))
        for dirname in candidate_paths:
            ansible_connection = os.path.join(dirname, 'ansible-connection')
            if os.path.isfile(ansible_connection):
                break
        else:
            raise AnsibleError("Unable to find location of 'ansible-connection'. "
                               "Please set or check the value of ANSIBLE_CONNECTION_PATH")

        env = os.environ.copy()
        env.update({
                   'ANSIBLE_BECOME_PLUGINS': become_loader.print_paths(),
                   'ANSIBLE_CLICONF_PLUGINS': cliconf_loader.print_paths(),
                   'ANSIBLE_CONNECTION_PLUGINS': connection_loader.print_paths(),
                   'ANSIBLE_HTTPAPI_PLUGINS': httpapi_loader.print_paths(),
                   'ANSIBLE_NETCONF_PLUGINS': netconf_loader.print_paths(),
                   'ANSIBLE_TERMINAL_PLUGINS': terminal_loader.print_paths(),
                   })
        python = sys.executable
        master, slave = pty.openpty()
        p = subprocess.Popen(
            [python, ansible_connection, to_text(os.getppid())],
            stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        os.close(slave)

        # We need to set the pty into noncanonical mode. This ensures that we
        # can receive lines longer than 4095 characters (plus newline) without
        # truncating.
        old = termios.tcgetattr(master)
        new = termios.tcgetattr(master)
        new[3] = new[3] & ~termios.ICANON

        try:
            termios.tcsetattr(master, termios.TCSANOW, new)
            write_to_file_descriptor(master, {'ansible_command_timeout': self.get_option('persistent_command_timeout')})
            write_to_file_descriptor(master, self._play_context.serialize())

            (stdout, stderr) = p.communicate()
        finally:
            termios.tcsetattr(master, termios.TCSANOW, old)
        os.close(master)

        if p.returncode == 0:
            result = json.loads(to_text(stdout, errors='surrogate_then_replace'))
        else:
            try:
                result = json.loads(to_text(stderr, errors='surrogate_then_replace'))
            except getattr(json.decoder, 'JSONDecodeError', ValueError):
                # JSONDecodeError only available on Python 3.5+
                result = {'error': to_text(stderr, errors='surrogate_then_replace')}

        if 'messages' in result:
            for level, message in result['messages']:
                if level == 'log':
                    display.display(message, log_only=True)
                elif level in ('debug', 'v', 'vv', 'vvv', 'vvvv', 'vvvvv', 'vvvvvv'):
                    getattr(display, level)(message, host=self._play_context.remote_addr)
                else:
                    if hasattr(display, level):
                        getattr(display, level)(message)
                    else:
                        display.vvvv(message, host=self._play_context.remote_addr)

        if 'error' in result:
            if self._play_context.verbosity > 2:
                if result.get('exception'):
                    msg = "The full traceback is:\n" + result['exception']
                    display.display(msg, color=C.COLOR_ERROR)
            raise AnsibleError(result['error'])

        return result['socket_path']
