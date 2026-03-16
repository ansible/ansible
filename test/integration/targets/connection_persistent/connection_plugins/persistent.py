from __future__ import annotations

DOCUMENTATION = """
options:
  persistent_connect_timeout:
    type: int
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
    default: 30
    ini:
      - section: persistent_connection
        key: command_timeout
    env:
      - name: ANSIBLE_PERSISTENT_COMMAND_TIMEOUT
    vars:
      - name: ansible_command_timeout
  persistent_log_messages:
    type: boolean
    ini:
      - section: persistent_connection
        key: log_messages
    env:
      - name: ANSIBLE_PERSISTENT_LOG_MESSAGES
    vars:
      - name: ansible_persistent_log_messages
"""

import json
import os
import pickle

from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection import NetworkConnectionBase


class Connection(NetworkConnectionBase):
    transport = 'persistent'
    supports_persistence = True

    def _connect(self):
        self._connected = True

    def update_play_context(self, pc_data):
        """
        This is to ensure that the PlayContext.deserialize method remains functional,
        preventing it from breaking the network connection plugins that rely on it.

        See:
        https://github.com/ansible-collections/ansible.netcommon/blob/50fafb6875bb2f57e932a7a50123513b48bd4fd5/plugins/connection/httpapi.py#L258
        """
        pc = self._play_context = PlayContext()

        pc.deserialize(
            pickle.loads(
                pc_data.encode(errors='surrogateescape')
            )
        )

    def get_capabilities(self, *args, **kwargs):
        return json.dumps({
            'pid': os.getpid(),
            'ppid': os.getppid(),
            **self._play_context.dump_attrs()
        })
