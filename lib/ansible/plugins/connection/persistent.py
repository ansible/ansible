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

from ansible import constants as C
from ansible.plugins.connection import ConnectionBase
from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves import cPickle
from ansible.module_utils.connection import Connection as SocketConnection
from ansible.errors import AnsibleError

try:
    from __main__ import display
except ImportError:
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
        master, slave = pty.openpty()

        python = sys.executable

        def find_file_in_path(filename):
            # Check $PATH first, followed by same directory as sys.argv[0]
            paths = os.environ['PATH'].split(os.pathsep) + [os.path.dirname(sys.argv[0])]
            for dirname in paths:
                fullpath = os.path.join(dirname, filename)
                if os.path.isfile(fullpath):
                    return fullpath

            raise AnsibleError("Unable to find location of '%s'" % filename)

        p = subprocess.Popen(
            [python, find_file_in_path('ansible-connection'), to_text(os.getppid())],
            stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdin = os.fdopen(master, 'wb', 0)
        os.close(slave)

        # Need to force a protocol that is compatible with both py2 and py3.
        # That would be protocol=2 or less.
        # Also need to force a protocol that excludes certain control chars as
        # stdin in this case is a pty and control chars will cause problems.
        # that means only protocol=0 will work.
        src = cPickle.dumps(self._play_context.serialize(), protocol=0)
        stdin.write(src)
        stdin.write(b'\n#END_INIT#\n')

        src = cPickle.dumps({'ansible_command_timeout': self.get_option('persistent_command_timeout')}, protocol=0)
        stdin.write(src)
        stdin.write(b'\n#END_VARS#\n')

        stdin.flush()

        (stdout, stderr) = p.communicate()
        stdin.close()

        if p.returncode == 0:
            result = json.loads(to_text(stdout, errors='surrogate_then_replace'))
        else:
            try:
                result = json.loads(to_text(stderr, errors='surrogate_then_replace'))
            except getattr(json.decoder, 'JSONDecodeError', ValueError):
                # JSONDecodeError only available on Python 3.5+
                result = {'error': to_text(stderr, errors='surrogate_then_replace')}

        if 'messages' in result:
            for msg in result.get('messages'):
                display.vvvv('%s' % msg, host=self._play_context.remote_addr)

        if 'error' in result:
            if self._play_context.verbosity > 2:
                if result.get('exception'):
                    msg = "The full traceback is:\n" + result['exception']
                    display.display(msg, color=C.COLOR_ERROR)
            raise AnsibleError(result['error'])

        return result['socket_path']
