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
"""
import os
import pty
import json
import subprocess

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
        p = subprocess.Popen(["ansible-connection", to_text(os.getppid())], stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

        (stdout, stderr) = p.communicate()
        stdin.close()

        if p.returncode == 0:
            result = json.loads(to_text(stdout, errors='surrogate_then_replace'))
        else:
            result = json.loads(to_text(stderr, errors='surrogate_then_replace'))

        if 'messages' in result:
            for msg in result.get('messages'):
                display.vvvv('%s' % msg, host=self._play_context.remote_addr)

        if 'error' in result:
            if self._play_context.verbosity > 2:
                msg = "The full traceback is:\n" + result['exception']
                display.display(result['exception'], color=C.COLOR_ERROR)
            raise AnsibleError(result['error'])

        return result['socket_path']
