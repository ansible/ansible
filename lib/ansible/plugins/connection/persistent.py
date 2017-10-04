# (c) 2017 Red Hat Inc.
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

from ansible.plugins.loader import connection_loader
from ansible.plugins.connection import ConnectionBase
from ansible.executor.process.connection import ConnectionProcess
from ansible.module_utils.connection import Connection as SocketConnection

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
        connection = connection_loader.get(self._play_context.connection, self._play_context, '/dev/null')
        process = ConnectionProcess(connection)
        process.start()
        setattr(self, '_socket_path', connection.socket_path)
        return connection.socket_path
