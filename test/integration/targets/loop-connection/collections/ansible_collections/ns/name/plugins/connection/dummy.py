# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
name: dummy
short_description: Used for loop-connection tests
description:
- See above
author: ansible (@core)
options:
  remote_addr:
    description: The address used to identify the connection in the connection log.
    vars:
    - name: ansible_host
  connection_log:
    description: Path to a file to log when the connection is opened and closed.
    vars:
    - name: dummy_connection_log
"""

from ansible.errors import AnsibleError
from ansible.plugins.connection import ConnectionBase


class Connection(ConnectionBase):

    transport = 'ns.name.dummy'

    def __init__(self, *args, **kwargs):
        self._cmds_run = 0
        super().__init__(*args, **kwargs)

    def _log(self, action):
        if connection_log := self.get_option('connection_log'):
            with open(connection_log, mode='a') as fd:
                fd.write(f"{action} {self.get_option('remote_addr')}\n")

    def _connect(self):
        self._log('connect')
        self._connected = True

    def exec_command(self, cmd, in_data=None, sudoable=True):
        super().exec_command(cmd, in_data=in_data, sudoable=sudoable)

        if 'become_test' in cmd:
            stderr = f"become - {self.become.name if self.become else None}"

        elif 'connected_test' in cmd:
            self._cmds_run += 1
            stderr = f"ran - {self._cmds_run}"

        elif 'connection_log_test' in cmd:
            stderr = ""

        else:
            raise AnsibleError(f"Unknown test cmd {cmd}")

        return 0, cmd.encode(), stderr.encode()

    def put_file(self, in_path, out_path):
        return

    def fetch_file(self, in_path, out_path):
        return

    def close(self):
        if self._connected:
            self._log('close')
            self._connected = False
