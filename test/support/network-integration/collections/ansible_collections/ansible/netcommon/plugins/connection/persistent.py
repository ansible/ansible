# 2017 Red Hat Inc.
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """author: Ansible Core Team
connection: persistent
short_description: Use a persistent unix socket for connection
description:
- This is a helper plugin to allow making other connections persistent.
options:
  persistent_command_timeout:
    type: int
    description:
    - Configures, in seconds, the amount of time to wait for a command to return from
      the remote device.  If this timer is exceeded before the command returns, the
      connection plugin will raise an exception and close
    default: 10
    ini:
    - section: persistent_connection
      key: command_timeout
    env:
    - name: ANSIBLE_PERSISTENT_COMMAND_TIMEOUT
    vars:
    - name: ansible_command_timeout
"""
from ansible.executor.task_executor import start_connection
from ansible.plugins.connection import ConnectionBase
from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection as SocketConnection
from ansible.utils.display import Display

display = Display()


class Connection(ConnectionBase):
    """ Local based connections """

    transport = "ansible.netcommon.persistent"
    has_pipelining = False

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(
            play_context, new_stdin, *args, **kwargs
        )
        self._task_uuid = to_text(kwargs.get("task_uuid", ""))

    def _connect(self):
        self._connected = True
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        display.vvvv(
            "exec_command(), socket_path=%s" % self.socket_path,
            host=self._play_context.remote_addr,
        )
        connection = SocketConnection(self.socket_path)
        out = connection.exec_command(cmd, in_data=in_data, sudoable=sudoable)
        return 0, out, ""

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
        display.vvvv(
            "starting connection from persistent connection plugin",
            host=self._play_context.remote_addr,
        )
        variables = {
            "ansible_command_timeout": self.get_option(
                "persistent_command_timeout"
            )
        }
        socket_path = start_connection(
            self._play_context, variables, self._task_uuid
        )
        display.vvvv(
            "local domain socket path is %s" % socket_path,
            host=self._play_context.remote_addr,
        )
        setattr(self, "_socket_path", socket_path)
        return socket_path
