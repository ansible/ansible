# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
name: dummy
short_description: Used for loop-connection tests
description:
- See above
author: ansible (@core)
"""

from ansible.errors import AnsibleError
from ansible.plugins.connection import ConnectionBase


class Connection(ConnectionBase):

    transport = 'ns.name.dummy'

    def __init__(self, *args, **kwargs):
        self._cmds_run = 0
        super().__init__(*args, **kwargs)

    @property
    def connected(self):
        return True

    def _connect(self):
        return

    def exec_command(self, cmd, in_data=None, sudoable=True):
        if 'become_test' in cmd:
            stderr = f"become - {self.become.name if self.become else None}"

        elif 'connected_test' in cmd:
            self._cmds_run += 1
            stderr = f"ran - {self._cmds_run}"

        else:
            raise AnsibleError(f"Unknown test cmd {cmd}")

        return 0, cmd.encode(), stderr.encode()

    def put_file(self, in_path, out_path):
        return

    def fetch_file(self, in_path, out_path):
        return

    def close(self):
        return
